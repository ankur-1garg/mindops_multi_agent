# agents/intent.py
import json
import google.generativeai as genai
from .base_agent import BaseAgent, StepResult
from state.workflow_state import WorkflowState
import config

class IntentAgent(BaseAgent):
    """Specializes in understanding user intent using Gemini."""

    def __init__(self):
        genai.configure(api_key=config.GOOGLE_API_KEY)
        self.llm = genai.GenerativeModel(
            config.INTENT_LLM_MODEL,
            generation_config={"response_mime_type": "application/json"} # Request JSON output directly
        )

    async def execute(self, state: WorkflowState) -> StepResult:
        print("🧠 Intent Agent (Gemini): Parsing user request...")
        
        prompt = f"""
        Parse this UI modification request into a structured JSON object.
        User Request: "{state.user_request}"

        Extract the following:
        - "action": The primary action (e.g., 'add', 'modify', 'remove').
        - "target_element": The UI element being targeted (e.g., 'button', 'form').
        - "element_identifier": A specific label or ID for the element (e.g., "Sign Up button").
        - "location_hints": Any phrases describing where the element is (e.g., 'header', 'login page').
        - "search_query": An optimized query for a vector database to find this screen.
        
        Return ONLY the raw JSON object.
        """
        
        try:
            # Use generate_content_async for async calls
            response = await self.llm.generate_content_async(prompt)
            
            # Gemini models configured for JSON output will have it in response.text
            parsed_intent = json.loads(response.text)
            state.intent = parsed_intent
            
            return StepResult(success=True, data={'intent': parsed_intent}, message="Intent parsed successfully with Gemini.")
        except Exception as e:
            return StepResult(success=False, message=f"Failed to parse intent with Gemini: {e}")