# main.py
import asyncio
import difflib
import os
import uuid
import json
from agents.orchestrator import OrchestratorAgent

# We'll run the orchestrator directly for CLI testing
# The API and websockets are not used in this script

async def main():
    orchestrator = OrchestratorAgent() # No websocket_manager needed for CLI
    workflow_id = str(uuid.uuid4())
    
    # --- YOUR REQUEST AND REPO URL GO HERE ---
    user_request = "add a big button in blue color on the landing page that says 'View on GitHub' and redirects to https://github.com"
    repo_url = "https://github.com/AmanM137/SAAS-Website-Builder"
    
    # --- Run the full workflow ---
    final_state = await orchestrator.process_request(
        workflow_id=workflow_id,
        user_request=user_request,
        repo_url=repo_url
    )

    # --- Print the final results ---
    if final_state and final_state.status == "completed":
        print("\n" + "="*50)
        print("🎉 WORKFLOW COMPLETED SUCCESSFULLY 🎉")
        print("="*50)

        # Print the code diff
        if final_state.code_changes:
            print("\n--- 🤖 GENERATED CODE DIFF ---")
            original = final_state.code_changes.get('original_code', '').splitlines(keepends=True)
            modified = final_state.code_changes.get('modified_code', '').splitlines(keepends=True)
            
            diff = difflib.unified_diff(original, modified, fromfile='original', tofile='modified')
            diff_output = "".join(diff)

            if not diff_output:
                 print("No difference between original and modified code.")
            else:
                for line in diff_output.splitlines():
                    if line.startswith('+'):
                        print(f'\033[92m{line}\033[0m') # Green
                    elif line.startswith('-'):
                        print(f'\033[91m{line}\033[0m') # Red
                    else:
                        print(line)
        
        # Print the content of the generated test script
        if final_state.test_results and final_state.test_results.get('test_script_path'):
            print("\n--- 🧪 GENERATED TEST SCRIPT ---")
            test_path = final_state.test_results['test_script_path']
            print(f"✅ Test script saved to: {os.path.abspath(test_path)}\n")
            
            try:
                with open(test_path, 'r', encoding='utf-8') as f:
                    print(f.read())
            except FileNotFoundError:
                print(f"Warning: Could not read test file at {test_path}. It might have been cleaned up with the workspace.")

        print("\n" + "="*50)

    elif final_state:
        print(f"\n❌ WORKFLOW FAILED at step: {final_state.current_step}")
        print(f"   Reason: {final_state.error}")

if __name__ == "__main__":
    # For CLI testing, we don't need a pre-built catalog
    asyncio.run(main())