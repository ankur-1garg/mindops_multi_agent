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
        # Agents are now initialized per-request
        self.intent_agent = IntentAgent()
        self.vision_agent = VisionAgent()  # Vision agent doesn't need repo path

    async def process_request(self, workflow_id: str, user_request: str, repo_url: str):
        state = WorkflowState(workflow_id=workflow_id,
                              user_request=user_request,
                              repo_url=repo_url)
        temp_repo_path = None

        try:
            # Step 1: Set up the workspace
            temp_repo_path = setup_temporary_workspace(repo_url)

            # Initialize agents that need filesystem access
            search_agent = SearchAgent(repo_path=temp_repo_path)
            code_agent = CodeAgent(repo_path=temp_repo_path)
            test_agent = TestAgent(repo_path=temp_repo_path)

            # Create the execution plan
            agents = {
                'intent': self.intent_agent,
                'search': search_agent,
                'vision': self.vision_agent,
                'code': code_agent,
                'test': test_agent,
            }

            # Define the execution plan (skipping vision for quota limits)
            plan = ['intent', 'search', 'code', 'test']

            logger.info(
                f"[{workflow_id}] Starting new workflow for: '{user_request}'")
            await self._send_update(workflow_id, "started", "Orchestrator")

            for agent_name in plan:
                state.current_step = agent_name
                logger.info(f"[{workflow_id}] -> Executing step: {agent_name}")
                await self._send_update(workflow_id, "in_progress", agent_name)

                agent = agents.get(agent_name)

                for attempt in range(MAX_RETRIES):
                    result = await agent.execute(state)
                    if result.success:
                        state.steps_completed.append(agent_name)
                        logger.info(
                            f"[{workflow_id}] Step '{agent_name}' successful.")
                        await self._send_update(workflow_id, "completed", agent_name, result.data)
                        break
                    else:
                        logger.warning(
                            f"[{workflow_id}]  Step '{agent_name}' failed on attempt {attempt + 1}/{MAX_RETRIES}. Reason: {result.message}")
                        if attempt < MAX_RETRIES - 1:
                            await asyncio.sleep(2)  # Wait before retrying
                        else:
                            state.status = "failed"
                            state.error = f"Step '{agent_name}' failed after {MAX_RETRIES} attempts. Final error: {result.message}"
                            logger.error(
                                f"[{workflow_id}]  Workflow failed. {state.error}")
                            await self._send_update(workflow_id, "failed", agent_name, {"error": state.error})
                            return state

            state.status = "completed"
            logger.info(f"[{workflow_id}] Workflow finished successfully!")
            await self._send_update(workflow_id, "completed", "Orchestrator", state.to_dict())
            return state

        finally:
            # Step Final: Clean up the workspace regardless of success or failure
            if temp_repo_path:
                cleanup_workspace(temp_repo_path)

    async def _send_update(self, workflow_id, status, step, data=None):
        if self.websocket_manager:
            payload = {"workflow_id": workflow_id,
                       "status": status, "step": step, "data": data or {}}
            await self.websocket_manager.broadcast(workflow_id, payload)
