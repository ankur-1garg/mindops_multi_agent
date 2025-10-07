# agents/orchestrator.py
import asyncio
from state.workflow_state import WorkflowState
from agents.intent import IntentAgent
from agents.search import SearchAgent
from agents.vision import VisionAgent
from agents.code import CodeAgent
from agents.test import TestAgent
from utils.logger import setup_logger
from utils.workspace import setup_temporary_workspace, cleanup_workspace

logger = setup_logger(__name__)
MAX_RETRIES = 2


class OrchestratorAgent:
    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager
        # Agents that don't need a repo path can be initialized here
        self.intent_agent = IntentAgent()
        self.vision_agent = VisionAgent()

    async def process_request(self, workflow_id: str, user_request: str, repo_url: str):
        state = WorkflowState(workflow_id=workflow_id,
                              user_request=user_request)
        temp_repo_path = None

        try:
            # Step 1: Set up the workspace
            temp_repo_path = setup_temporary_workspace(repo_url)

            # Step 2: Initialize agents that need filesystem access
            search_agent = SearchAgent(repo_path=temp_repo_path)
            code_agent = CodeAgent(repo_path=temp_repo_path)
            test_agent = TestAgent(repo_path=temp_repo_path)

            agents = {
                'intent': self.intent_agent,
                'search': search_agent,
                'vision': self.vision_agent,
                'code': code_agent,
                'test': test_agent,
            }

            # Note: Re-enable 'vision' once quota issues are resolved
            plan = ['intent', 'search', 'code', 'test']

            logger.info(
                f"[{workflow_id}] Starting new workflow for: '{user_request}'")

            # --- THE WORKFLOW LOOP ---
            for agent_name in plan:
                state.current_step = agent_name
                logger.info(f"[{workflow_id}] -> Executing step: {agent_name}")
                await self._send_update(workflow_id, "in_progress", agent_name)

                retry_count = 0
                while retry_count <= MAX_RETRIES:
                    try:
                        result = await agents[agent_name].execute(state)

                        if result.success:
                            logger.info(
                                f"[{workflow_id}] {agent_name.capitalize()} agent completed successfully")
                            await self._send_update(workflow_id, "completed", agent_name, result.data)
                            break
                        else:
                            logger.warning(
                                f"[{workflow_id}] {agent_name.capitalize()} agent failed: {result.message}")
                            if retry_count == MAX_RETRIES:
                                state.status = "failed"
                                state.error = f"Max retries exceeded for {agent_name} agent: {result.message}"
                                await self._send_update(workflow_id, "failed", agent_name, {"error": result.message})
                                return state
                            retry_count += 1
                            await self._send_update(workflow_id, "retrying", agent_name)

                    except Exception as e:
                        logger.error(
                            f"[{workflow_id}] Error in {agent_name} agent: {str(e)}", exc_info=True)
                        if retry_count == MAX_RETRIES:
                            state.status = "failed"
                            state.error = f"Error in {agent_name} agent: {str(e)}"
                            await self._send_update(workflow_id, "failed", agent_name, {"error": str(e)})
                            return state
                        retry_count += 1
                        await self._send_update(workflow_id, "retrying", agent_name)

            # Workflow completed successfully
            state.status = "completed"
            await self._send_update(workflow_id, "completed", "workflow", {
                "status": "completed",
                "test_results": state.test_results,
                "code_changes": state.code_changes
            })

        finally:
            # Final Step: Clean up the workspace
            if temp_repo_path:
                cleanup_workspace(temp_repo_path)

        return state

    async def _send_update(self, workflow_id: str, status: str, step: str, data: dict = None):
        """Helper function to send updates over the WebSocket."""
        if self.websocket_manager:
            payload = {
                "workflow_id": workflow_id,
                "status": status,
                "step": step,
                "data": data or {}
            }
            await self.websocket_manager.broadcast(workflow_id, payload)
