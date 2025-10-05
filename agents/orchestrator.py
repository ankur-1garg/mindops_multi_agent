# agents/orchestrator.py
from state.workflow_state import WorkflowState
from .intent import IntentAgent
from .search import SearchAgent
from .vision import VisionAgent # Import the new VisionAgent
from .code import CodeAgent

class OrchestratorAgent:
    def __init__(self):
        self.agents = {
            'intent': IntentAgent(),
            'search': SearchAgent(),
            'vision': VisionAgent(), # Add the VisionAgent here
            'code': CodeAgent(),
        }

    async def process_request(self, user_request: str):
        state = WorkflowState(user_request=user_request)
        
        # Updated plan to include vision
        plan = ['intent', 'search', 'code']#, 'vision'] # Vision runs after search, before code
        
        print(f"🚀 Starting Multi-Agent Workflow for: '{user_request}'\n")
        
        for agent_name in plan:
            agent = self.agents.get(agent_name)
            result = await agent.execute(state)
            
            if not result.success:
                print(f"❌ Workflow failed at step '{agent_name}'. Reason: {result.message}")
                return None
            
            print(f"✅ Step '{agent_name}' successful. {result.message}\n")

        print("🎉 Workflow finished successfully!")
        return state