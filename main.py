# main.py
import asyncio
import difflib
from agents.orchestrator import OrchestratorAgent
import os
import json # Make sure json is imported
import uuid

async def main():
    orchestrator = OrchestratorAgent()
    workflow_id = str(uuid.uuid4())
    user_request = "Change the main heading on the landing page to 'Build Websites Instantly'"
    
    final_state = await orchestrator.process_request(workflow_id, user_request)

    if final_state and final_state.status == "completed":
        print("\n--- FINAL WORKFLOW SUMMARY ---")
        
        # Print the code diff
        if final_state.code_changes:
            print("\n--- GENERATED CODE DIFF ---")
            original = final_state.code_changes['original_code'].splitlines(keepends=True)
            modified = final_state.code_changes['modified_code'].splitlines(keepends=True)
            diff = difflib.unified_diff(original, modified, fromfile='original', tofile='modified')
            for line in diff:
                if line.startswith('+'):
                    print(f'\033[92m{line.strip()}\033[0m')
                elif line.startswith('-'):
                    print(f'\033[91m{line.strip()}\033[0m')
                else:
                    print(line.strip())
        
        # Print the path to the generated test script
        if final_state.test_results and final_state.test_results.get('test_script_path'):
            print("\n--- GENERATED TEST SCRIPT ---")
            test_path = final_state.test_results['test_script_path']
            print(f"✅ Test script has been generated and saved to:")
            print(f"   -> {os.path.abspath(test_path)}")
            print("\nTo run the test, copy this file into your project's source directory and run your test command (e.g., 'npm test').")

        print("\n--------------------------")

if __name__ == "__main__":
    if not os.path.exists('output/catalog.json'):
        print("❌ Catalog not found! Please run `python catalog_builder.py` first.")
    else:
        asyncio.run(main())