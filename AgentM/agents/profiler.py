from langsmith import traceable
from AgentM.states import DataCleanState
from AgentM.config import llm
from AgentM.utils.utils import file_handler

import pandas as pd
import numpy as np


@traceable(name="Profiler Agent", run_type="chain")
def profiler(state: DataCleanState):
    """
    The profiler analyzes uploaded csv file in detail.

    Responsibilities:
        1. read schemas and columns
        2. detect null values
        3. find messy and inconsistent data
        4. create a cleaning strategy

    Output:
        1. Dataset Summary
        2. Cleaning recommendations    
        3. Cleaning Steps
        4. Risk area for transformation
    """

    dataset_path = state.get("dataset_path", "")
    user_instructions = state.get("user_instruction", "") or state.get("user_instructions", "")

    _, data_profile = file_handler("read_csv", dataset_path)

    instruction_text = f"\n USER INSTRUCTIONS:\n'{user_instructions}'" if user_instructions else ""

    prompt = f"""
You are a Senior Data Cleaning Agent.

DATASET PROFILE:
{data_profile}
{instruction_text}

TASK:
1. Analyze the dataset based on the user's instructions.
2. Write a 3-step cleaning strategy.
3. STEP 1 MUST focus on the user's request.
4. Do not write code yet. Just the bullet-point plan.
"""

    response = llm.invoke(prompt)

    return {"clean_plan": response.content}
