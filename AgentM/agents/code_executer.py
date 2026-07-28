import os
from langsmith import traceable
from AgentM.utils.utils import code_runner, file_handler, metrics
from AgentM.states import DataCleanState


@traceable(name="Executor Agent", run_type="tool")
def code_execute(state: DataCleanState):
    """
    The Executor runs the approved code in a controlled workflow.

    Responsibilities

        1.Executes transformation logic
        2.Captures runtime errors
        3.Validates output generation
        4.Routes failures back to the Coder
        5.Produces the final cleaned dataset

    Output

        1.Cleaned CSV
        2.Execution status
        3.Error trace if transformation fails

    """

    code = state.get("python_code", "")
    dataset_path = state.get("dataset_path", "")
    orig_filename = os.path.basename(dataset_path) if dataset_path else "data.csv"
    script_path = "workspace_cleaner.py"

    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    target_file = os.path.join(output_dir, f"cleaned_{orig_filename}").replace("\\", "/")

    current_retries = state.get("retry_count", 0)

    try:
        # 1. Remove old target file if it exists
        file_handler("cleanup", path=target_file)

        # 2. Save generated python code to temporary script
        file_handler("save_code", path=script_path, content=code)

        # 3. Run the script
        run_result = code_runner(script_path=script_path)

        # 4. Verification
        if run_result['success'] and os.path.exists(target_file):
            print(f" code executed successfully (Retries: {current_retries})")
            return {
                "is_cleaned": True,
                "clean_path": target_file,
                "errors": []
            }

        # Fallback check if LLM saved directly to root or alternative path
        fallback_target = f"cleaned_{orig_filename}"
        if os.path.exists(fallback_target):
            os.rename(fallback_target, target_file)
            print(f" code executed successfully (Retries: {current_retries})")
            return {
                "is_cleaned": True,
                "clean_path": target_file,
                "errors": []
            }

        error_msg = run_result["error"] or f"Execution finished but '{target_file}' was not created."
        print(f" Execution Failed. Incrementing retry count.")

        return {
            "is_cleaned": False,
            "retry_count": current_retries + 1,
            "errors": [error_msg]
        }

    finally:
        # 5. Clean up temporary script file after execution
        file_handler("cleanup", path=script_path)
