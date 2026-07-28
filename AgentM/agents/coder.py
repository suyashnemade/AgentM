import os
from langsmith import traceable
from AgentM.states import DataCleanState
from AgentM.config import llm
from dotenv import load_dotenv

load_dotenv()


@traceable(name="Coder", run_type="chain")
def coder(state: DataCleanState):
    """
    The Coder generates Python/Pandas code based on the Profiler findings.

        Responsibilities
            1. Writes cleaning logic
            2. Handles missing values
            3. Fixes data type issues
            4. Normalizes inconsistent values
            5. Learns from previous errors
            
        Output
            1. Executable Pandas transformation code
            2. Updated logic after failure feedback
    """

    plan = state.get("clean_plan", "")
    dataset_path = state.get("dataset_path", "")
    user_instructions = state.get("user_instruction", "")
    errors = state.get("errors", [])
    retry_count = state.get("retry_count", 0)

    orig_filename = os.path.basename(dataset_path) if dataset_path else "data.csv"
    target_output_path = os.path.join("outputs", f"cleaned_{orig_filename}").replace("\\", "/")

    error_context = ""
    if errors:
        print(f"-> ⚠️ Repairing code (Attempt {retry_count}/3). Error: {errors[-1].splitlines()[-1]}")
        error_context = f"""
        CRITICAL: Your previous attempt failed. 
        ERROR MESSAGE: {errors[-1]}
        You must fix this error. If the error was a 'FileNotFoundError', check your save path.
        If it was a 'TypeError', check your data types.
        """

    prompt = f"""You are a Senior Data Coder.
    FILE TO CLEAN: '{dataset_path}'
    USER'S MANDATORY REQUEST: "{user_instructions}"
    CLEANING PLAN:
    {plan}
    {error_context}

    MANDATORY CODING RULES:
    1. Use 'import pandas as pd' and 'import numpy as np' and 'import os'.
    2. YOU MUST implement the user's request: "{user_instructions}".
    3. Load data directly from '{dataset_path}'. Handle encoding issues gracefully (e.g. use encoding='latin1' or encoding_errors='replace' if UTF-8 fails).
    4. YOU MUST CREATE THE 'outputs' DIRECTORY (`os.makedirs('outputs', exist_ok=True)`) AND SAVE THE FINAL RESULT EXACTLY TO '{target_output_path}'.
    5. ONLY OUTPUT THE RAW PYTHON CODE. NO MARKDOWN (no ```python). 
    6. If this is Attempt #{retry_count}, use a different logical approach to avoid repeating the same error.
    """

    response = llm.invoke(prompt)
    raw_code = response.content.replace("```python", "").replace("```", "").strip()
    return {"python_code": raw_code}
