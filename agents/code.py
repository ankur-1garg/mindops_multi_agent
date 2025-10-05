# agents/code.py
import os
import re
import requests
import base64
import google.generativeai as genai
from .base_agent import BaseAgent, StepResult
from state.workflow_state import WorkflowState
import config


class CodeAgent(BaseAgent):
    """Specializes in generating code modifications using Gemini."""

    def __init__(self):
        genai.configure(api_key=config.GOOGLE_API_KEY)
        # Using the specified LLM model
        self.llm = genai.GenerativeModel(config.CODE_LLM_MODEL)

    async def execute(self, state: WorkflowState) -> StepResult:
        print("💻 Code Agent (Gemini): Generating code modification...")

        source_file = state.screen.get('source_file')
        if not source_file:
            return StepResult(success=False, message="No source file found in the current state.")

        # Get the file content from GitHub's raw content URL
        correct_path = "src/app/site/page.tsx"  # This is the main landing page
        url = f"https://raw.githubusercontent.com/{config.GITHUB_REPO_OWNER}/{config.GITHUB_REPO_NAME}/main/{correct_path}"
        print(f"Fetching file from {url}")
        headers = {
            "Authorization": f"token {config.GITHUB_TOKEN}"} if config.GITHUB_TOKEN else {}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return StepResult(success=False, message=f"Failed to fetch file from GitHub. Status: {response.status_code}")

            original_code = response.text  # Raw content doesn't need base64 decoding
        except Exception as e:
            return StepResult(success=False, message=f"Failed to fetch file from GitHub: {e}")

        prompt = f"""
        You are an expert Next.js 14 developer. Your task is to modify a React component file.
        User Request: "{state.user_request}"
        Target Element Details: {state.intent.get('element_identifier', 'N/A')}
        File to Modify: `{source_file}`
        
        Original Code:
        ```tsx
        {original_code}
        ```

        Instructions:
        1. Implement the user's requested change (Action: {state.intent.get('action')}, Target: {state.intent.get('target_element')}, specifically related to "{state.intent.get('element_identifier', '')}").
        2. Maintain the existing coding style, component structure, and libraries (e.g., Tailwind CSS).
        3. Make minimal, surgical changes. Do not rewrite unrelated parts of the file.
        4. Return the ENTIRE, COMPLETE file content with changes applied.
        5. Your response must be a single code block with the modified code.

        Modified Code:
        """

        try:
            response = await self.llm.generate_content_async(prompt)
            modified_code = response.text

            # Clean up the response to get only the code
            match = re.search(r'```(?:tsx|jsx|js)?\n(.*)```',
                              modified_code, re.DOTALL)
            if match:
                modified_code = match.group(1).strip()
            else:  # If no code block is found, assume the entire response is code
                modified_code = modified_code.strip()

            changes = {"original_code": original_code,
                       "modified_code": modified_code}
            state.code_changes = changes

            return StepResult(success=True, data=changes, message="Code generated successfully with Gemini.")
        except Exception as e:
            return StepResult(success=False, message=f"Failed to generate code with Gemini: {e}")
