# agents/test.py
import os
import re
from .base_agent import BaseAgent, StepResult
from state.workflow_state import WorkflowState
from utils.logger import setup_logger
import google.generativeai as genai
import config

logger = setup_logger(__name__)


class TestAgent(BaseAgent):
    """Generates a test script for the code changes and provides it to the user."""

    def __init__(self, repo_path: str): # Add repo_path here
        self.repo_path = repo_path # <<< ADD this line
        genai.configure(api_key=config.GOOGLE_API_KEY)
        self.llm = genai.GenerativeModel(config.TEST_LLM_MODEL)

    async def execute(self, state: WorkflowState) -> StepResult:
        logger.info(
            f"[{state.workflow_id}]  Test Agent: Starting test script generation...")

        try:
            # Step 1: Generate test code from Gemini
            test_code = await self._generate_test_code(state)
            if not test_code:
                return StepResult(success=False, message="Failed to generate test code.")

            # Step 2: Determine the correct path and save the file
            source_file = state.screen['source_file']
            # Create a dedicated directory for generated tests to keep the source repo clean
            test_output_dir = os.path.join("output", "generated_tests")
            os.makedirs(test_output_dir, exist_ok=True)

            # Create a descriptive filename
            base_name = os.path.basename(
                source_file).replace('.tsx', '.test.tsx')
            test_file_path = os.path.join(test_output_dir, base_name)

            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write(test_code)

            logger.info(
                f"[{state.workflow_id}] Test script saved to {test_file_path}")

            results = {
                "test_script_path": test_file_path,
                "message": "Test script generated. Please run it manually in your project."
            }
            state.test_results = results

            return StepResult(success=True, data=results, message=f"Test script saved to {test_file_path}")

        except Exception as e:
            logger.error(
                f"[{state.workflow_id}] Error in TestAgent: {e}", exc_info=True)
            return StepResult(success=False, message=str(e))

    async def _generate_test_code(self, state: WorkflowState) -> str:
        prompt = f"""
        You are an expert QA engineer specializing in Next.js and React. Your task is to write a unit test for a code modification.

        User Request: "{state.user_request}"
        File Modified: `{state.screen['source_file']}`
        
        Modified Code (the code to test):
        ```tsx
        {state.code_changes['modified_code']}
        ```
        
        Instructions:
        1. Write a new Jest and React Testing Library test file (`.test.tsx`).
        2. Focus on testing the specific change requested by the user.
        3. Ensure the test is self-contained and follows best practices.
        4. Return ONLY the raw test code inside a single code block.
        """
        response = await self.llm.generate_content_async(prompt)
        match = re.search(r'```(?:tsx|jsx|js)?\n(.*)```',
                          response.text, re.DOTALL)
        return match.group(1).strip() if match else response.text
