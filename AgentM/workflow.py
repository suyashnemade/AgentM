from langgraph.graph import END, START, StateGraph
from AgentM.agents.profiler import profiler
from AgentM.agents.planer import planer
from AgentM.agents.coder import coder
from AgentM.agents.reviewer import reviewer
from AgentM.agents.code_executer import code_execute
from AgentM.states import DataCleanState
from langgraph.checkpoint.memory import MemorySaver



def route_after_review(state):
    """Reviewer rejected → back to Coder, approved → Human Review."""
    if not state.get("review_safe", True):
        return "coder"
    return "human_review"


def human_review(state):
    """Passthrough node — interrupt_before pauses here for human approval."""
    return {}


def route_after_human_review(state):
    """Human approved → Executor, rejected → back to Coder."""
    if state.get("human_approved", False):
        return "code_execute"
    return "coder"


def route_after_execution(state):
    """Executor success → END, retry < 3 → Coder, retry >= 3 → Circuit Breaker."""
    if state.get("is_cleaned"):
        return END

    # If we fail 3 times, stop
    if state.get("retry_count", 0) >= 3:
        return END

    return "coder"



graph = StateGraph(DataCleanState)

# Add all worker nodes + human review gate
graph.add_node("profile", profiler)
graph.add_node("planer", planer)
graph.add_node("coder", coder)
graph.add_node("ai_review", reviewer)
graph.add_node("human_review", human_review)
graph.add_node("code_execute", code_execute)

# Define the flow
graph.add_edge(START,"profile")
graph.add_edge("profile", "coder")
graph.add_edge("coder", "ai_review")

# Reviewer: SAFE → Human Review, DANGER → back to Coder
graph.add_conditional_edges("ai_review", route_after_review, {
    "coder": "coder",
    "human_review": "human_review",
})

# Human Review: Approved → Executor, Rejected → back to Coder
graph.add_conditional_edges("human_review", route_after_human_review, {
    "code_execute": "code_execute",
    "coder": "coder",
})

# Executor: Success → END, Error + retries < 3 → Coder, Error + retries >= 3 → END
graph.add_conditional_edges("code_execute", route_after_execution, {
    END: END,
    "coder": "coder",
})

memory = MemorySaver()

# Pause BEFORE human_review so the caller can set human_approved in state
workflow = graph.compile(checkpointer=memory, interrupt_before=["human_review"])