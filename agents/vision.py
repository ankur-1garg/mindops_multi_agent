# agents/vision.py
import os
import mimetypes
from PIL import Image
import google.generativeai as genai
from .base_agent import BaseAgent, StepResult
from state.workflow_state import WorkflowState
import config

class VisionAgent(BaseAgent):
    """
    Specializes in generating and analyzing UI images using Gemini,
    guided by an expert system prompt.
    """

    def __init__(self):
        genai.configure(api_key=config.GOOGLE_API_KEY)

        # The system prompt contains the expert knowledge from the documentation.
        system_prompt = """
You are an expert AI UI/UX designer and image generation specialist. Your purpose is to create high-fidelity visual mockups of web interfaces based on user requests.

Your core strength is deep language understanding. You must follow these principles derived from professional prompting guides:

**1. Core Principle: Describe the Scene, Don't List Keywords.**
   - You must interpret the user's request as a narrative change to an existing scene. Your output should reflect a coherent, visually consistent world.

**2. Hyper-Specificity and Context:**
   - Pay close attention to the context of the original UI (its name and description). The new design must feel like a natural evolution of the old one.
   - When a user asks to modify an element (e.g., "make the button green"), you must also consider the existing design system. The shade of green, the button's border-radius, and font should match the established style.

**3. Photographic and Cinematic Language:**
   - Treat the UI as a scene. Think in terms of lighting (e.g., "soft, ambient lighting"), materials ("matte finish"), and camera angles ("straight-on, eye-level view"). This will create a more realistic and professional mockup.

**4. Accurate Text Rendering:**
   - If the request involves adding or changing text, you must render it legibly and accurately. Consider the font style (e.g., "a clean, sans-serif font like Inter") and placement.

**5. Task Instructions:**
   - Your task is to generate a *new image* that represents the UI *after* the user's requested change has been applied.
   - You will be given the original UI's context (its name and description) and the user's specific request.
   - Your output must be ONLY the generated image. Do not include any explanatory text, markdown, or other content.
"""
        self.llm = genai.GenerativeModel(
            config.VISION_IMAGE_MODEL,
            system_instruction=system_prompt
        )

    async def execute(self, state: WorkflowState) -> StepResult:
        print("🎨 Vision Agent (Gemini): Generating UI mockup with expert system prompt...")

        screen_data = state.screen
        
        # This is the prompt for this specific task, which complements the system prompt.
        user_task_prompt = f"""
        **Original UI Context:**
        - Screen Name: "{screen_data.get('screen_name', 'a web page')}"
        - Description: "{screen_data.get('description', 'a standard web page interface')}"

        **User's Modification Request:**
        - "{state.user_request}"

        Please generate the new UI image now.
        """

        try:
            # For text-to-image, we send the detailed text prompt.
            # For a true image-to-image model, you would also include the original screenshot here.
            response = await self.llm.generate_content_async(user_task_prompt)
            
            image_part = next((part for part in response.parts if hasattr(part, 'mime_type') and part.mime_type.startswith('image/')), None)

            if not image_part:
                print(f"❌ Gemini did not return an image. Response text: {response.text}")
                return StepResult(success=False, message="Gemini did not return a modified image.", data={"response_text": response.text})

            # Save the new mockup to the output folder
            mime_type = image_part.mime_type
            file_extension = mimetypes.guess_extension(mime_type) or ".png"
            output_filename = f"output/mockup_{state.screen['screen_id']}{file_extension}"
            
            with open(output_filename, "wb") as f:
                f.write(image_part.data)

            state.mockup_path = output_filename
            message = f"UI mockup generated and saved to {output_filename}."
            print(f"   -> {message}")

            return StepResult(success=True, data={'mockup_path': output_filename}, message=message)

        except Exception as e:
            print(f"An error occurred during mockup generation: {e}")
            return StepResult(success=False, message=f"Failed to generate mockup with Gemini: {e}")