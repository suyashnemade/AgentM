from langsmith import traceable
from AgentM.states import DataCleanState
from AgentM.config import llm


@traceable(name="Reviewer", run_type="chain")
def reviewer(state: DataCleanState):
    """
    The Reviewer acts as a safety layer before execution.

    Responsibilities

        1.Reviews AI-generated code
        2.Flags dangerous operations
        3.Blocks unsafe system calls
        4.Prevents risky file or OS-level behavior

    Example risks

        1.File deletion logic
        2.Unauthorized system calls
        3.Unsafe imports
        4.Risky execution patterns
    """

    code = state.get("python_code", "")

    prompt = f"""You are a Cyber Security Expert. 
    Review this AI-generated Python code for dangerous operations:
    
    CODE:
    {code}
    
    CHECK FOR:
    1. System commands (os.system, subprocess.Popen with shell=True).
    2. File deletions (os.remove, shutil.rmtree) UNLESS it is deleting 'workspace_cleaner.py'.
    3. Network requests to unknown URLs.
    
    If the code is safe, reply with 'SAFE'.
    If it is dangerous, reply with 'DANGER: [reason]'.
    """

    response = llm.invoke(prompt)

    if "DANGER" in response.content.upper():
        # If it's dangerous, route back to the coder via conditional edge
        return {"review_safe": False, "errors": [f"SECURITY VETO: {response.content}"]}

    return {"review_safe": True, "errors": []}