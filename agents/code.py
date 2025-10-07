# agents/code.py
import os
import re
import google.generativeai as genai
from .base_agent import BaseAgent, StepResult
from state.workflow_state import WorkflowState
from utils.logger import setup_logger
import config

logger = setup_logger(__name__)


class CodeAgent(BaseAgent):
    """Specializes in generating code modifications using Gemini."""

    def __init__(self, repo_path: str):
        # self.repo_path = repo_path  # <<< ADD this line
        genai.configure(api_key=config.GOOGLE_API_KEY)
        self.llm = genai.GenerativeModel(config.CODE_LLM_MODEL)
        self.repo_path = repo_path

    async def execute(self, state: WorkflowState) -> StepResult:
        logger.info(
            f"[{state.workflow_id}] [Code] Agent: Starting code modification...")

        source_file = state.screen.get('source_file')
        if not source_file:
            return StepResult(success=False, message="No source file found in the current state.")

        # Read the file from the temporary local repository
        file_path = os.path.join(self.repo_path, source_file)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
        except FileNotFoundError:
            logger.error(
                f"[{state.workflow_id}] Code file not found at: {file_path}")
            return StepResult(success=False, message=f"Code file not found at: {file_path}")

        prompt = f"""
        You are an expert Next.js 14 developer. Your task is to modify a React component file.
        User Request: "{state.user_request}"
        File to Modify: `{source_file}`
        
        Original Code:
        ```tsx
        {original_code}
        ```
        
        Instructions:
        1. Implement the user's requested change.
        2. Maintain the existing coding style and libraries.
        3. Make minimal, surgical changes.
        4. Return the ENTIRE, COMPLETE file content with changes applied in a single code block.

        Modified Code:
        """

        try:
            response = await self.llm.generate_content_async(prompt)
            modified_code = response.text
            
            match = re.search(r'```(?:tsx|jsx|js)?\n(.*)```', modified_code, re.DOTALL)
            if match:
                modified_code = match.group(1).strip()
            else:
                modified_code = modified_code.strip()

            changes = {"original_code": original_code, "modified_code": modified_code}
            state.code_changes = changes

            logger.info(f"[{state.workflow_id}] Code generated successfully.")
            return StepResult(success=True, data=changes, message="Code generated successfully.")
            
        except Exception as e:
            logger.error(f"[{state.workflow_id}] Failed to generate code with Gemini: {e}", exc_info=True)
            # Ensure the except block also returns a StepResult
            return StepResult(success=False, message=f"Failed to generate code with Gemini: {e}")
