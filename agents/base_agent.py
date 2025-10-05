  
# agents/base_agent.py
from abc import ABC, abstractmethod
from state.workflow_state import WorkflowState

class StepResult:
    """Standardized result object for an agent's execution step."""
    def __init__(self, success: bool, data: dict = None, message: str = ""):
        self.success = success
        self.data = data or {}
        self.message = message

class BaseAgent(ABC):
    """Abstract base class for all specialized agents."""
    
    @abstractmethod
    async def execute(self, state: WorkflowState) -> StepResult:
        """
        The main entry point for an agent to perform its task.
        It reads from the state, performs its logic, and returns a result.
        """
        pass