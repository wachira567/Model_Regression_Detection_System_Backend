import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from app.agents.critics import factual_critic_node, logical_critic_node

# Define the State for our LangGraph
class EvalState(TypedDict):
    input: dict
    expected_output: dict
    actual_output: dict
    
    # Critic outputs
    factual_score: int
    factual_reasoning: str
    logical_score: int
    logical_reasoning: str
    
    # Aggregated issues (using operator.add to append lists during parallel execution)
    issues: Annotated[list[str], operator.add]
    
    # Final verdict
    final_score: float
    status: str

async def synthesize_verdict_node(state: EvalState) -> dict:
    """
    Supervisor node that synthesizes the critic scores into a final verdict.
    """
    f_score = state.get("factual_score", 0)
    l_score = state.get("logical_score", 0)
    
    # Calculate average
    avg_score = (f_score + l_score) / 2.0
    
    # Simple threshold logic: if average >= 4.0, it passes
    status = "pass" if avg_score >= 4.0 else "fail"
    
    return {"final_score": avg_score, "status": status}

def build_eval_graph() -> StateGraph:
    """
    Builds and compiles the LangGraph state machine for the Deep Agentic Evaluation.
    """
    workflow = StateGraph(EvalState)
    
    # Add nodes
    workflow.add_node("factual_critic", factual_critic_node)
    workflow.add_node("logical_critic", logical_critic_node)
    workflow.add_node("supervisor", synthesize_verdict_node)
    
    # The workflow starts by running the critics in parallel
    workflow.set_entry_point("factual_critic")
    workflow.add_edge("factual_critic", "supervisor")
    
    # To run in parallel in LangGraph, we attach multiple nodes to the entry
    # But since set_entry_point only takes one, we can use a dummy start node, 
    # or just route from start to both.
    # In newer langgraph, we can add conditional edges from START, or just add an init node.
    # For simplicity, let's create an init node that just passes state.
    
    workflow.add_node("init", lambda state: state)
    workflow.set_entry_point("init")
    workflow.add_edge("init", "factual_critic")
    workflow.add_edge("init", "logical_critic")
    
    workflow.add_edge("logical_critic", "supervisor")
    workflow.add_edge("supervisor", END)
    
    # Compile the graph
    app = workflow.compile()
    return app
