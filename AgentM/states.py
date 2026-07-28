from typing import TypedDict, List


class DataCleanState(TypedDict):
    dataset_path: str
    
    user_instruction: str
    clean_plan: str          # Profiler's cleaning strategy
    python_code: str         # Coder's generated code

    review_safe: bool        # Review Verdict
    human_approved: bool     # Human review decision

    errors: List[str]    
    retry_count: int  # No of retries

    is_cleaned: bool
    clean_path: str
