# main.py
import asyncio
import difflib
from agents.orchestrator import OrchestratorAgent

async def main():
    orchestrator = OrchestratorAgent()
    
    # --- YOUR REQUEST GOES HERE ---
    user_request = "Change the main heading on the landing page to 'Build Websites Instantly'"

    final_state = await orchestrator.process_request(user_request=user_request)

    if final_state:
        print("\n--- FINAL WORKFLOW SUMMARY ---")
        print(f"User Request: {final_state.user_request}")
        print(f"Intent: {final_state.intent}")
        print(f"Screen Found: {final_state.screen.get('screen_name', 'N/A')}")
        
        if final_state.mockup_path:
            print(f"Generated Mockup: {final_state.mockup_path}")
            # You can add code here to open the image automatically if desired
            # import webbrowser
            # webbrowser.open(final_state.mockup_path)

        if final_state.code_changes:
            print("--- FINAL CODE DIFF ---")
            original = final_state.code_changes['original_code'].splitlines(keepends=True)
            modified = final_state.code_changes['modified_code'].splitlines(keepends=True)
            
            diff = difflib.unified_diff(original, modified, fromfile='original', tofile='modified')
            for line in diff:
                if line.startswith('+'):
                    print(f'\033[92m{line.strip()}\033[0m') # Green
                elif line.startswith('-'):
                    print(f'\033[91m{line.strip()}\033[0m') # Red
                else:
                    print(line.strip())
        print("--------------------------")

if __name__ == "__main__":
    asyncio.run(main())