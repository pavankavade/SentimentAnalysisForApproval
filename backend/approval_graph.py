from typing import TypedDict, Annotated, Union
import operator
from langgraph.graph import StateGraph, END

# Import the classification function from our azure_gpt module
# We use a relative import assuming main.py will run from the backend directory's parent
# or that the backend directory is added to PYTHONPATH.
# If running main.py directly within backend/, use: from azure_gpt import ...
from .azure_gpt import get_reply_classification

# Define the state structure for our graph
class ApprovalState(TypedDict):
    """Represents the state of the approval workflow."""
    service_line: str
    threshold: int
    justification_email: str # The email sent *to* the user (if threshold > 30)
    user_reply: str        # The reply received *from* the user
    classification: str    # Result of the LLM classification ('positive', 'negative', 'error')
    final_status: str      # The final outcome ('Approved', 'Rejected', 'Error')

# Define the nodes for our graph

async def classify_reply_node(state: ApprovalState) -> dict:
    """Classifies the user's reply using the LLM."""
    print("--- Classifying Reply Node ---")
    user_reply = state['user_reply']
    
    # Handle the case where threshold was <= 30 and no reply is expected/needed
    # Or if the request failed before getting a reply
    if not user_reply:
        print("No user reply provided, skipping classification.")
        # If there's no reply because it was auto-approved, this node might not 
        # even be hit depending on entry logic, but handling defensively.
        # We might set a specific classification or let the graph handle it.
        # For now, assume if this node is hit, classification is needed or implies rejection.
        return {"classification": "negative"} 
        
    classification_result = await get_reply_classification(user_reply)
    print(f"Classification Result: {classification_result}")
    return {"classification": classification_result}

def determine_final_status_node(state: ApprovalState) -> dict:
    """Determines the final status based on classification."""
    print("--- Determining Final Status Node ---")
    classification = state['classification']
    final_status = "Rejected" # Default to Rejected
    if classification == 'positive':
        final_status = "Approved"
    elif classification == 'error':
        final_status = "Error"
        print("Error during classification process.")
    
    print(f"Final Status: {final_status}")
    return {"final_status": final_status}

# Define the conditional logic for branching
def decide_next_step(state: ApprovalState) -> str:
    """Decides the next step based on the classification."""
    print("--- Decision Node ---")
    # In this simple graph, classification directly leads to final status determination
    # This node might be more complex in graphs with more steps.
    # For now, it always goes to the final status node after classification.
    return "determine_final_status"


# Create the StateGraph
workflow = StateGraph(ApprovalState)

# Add nodes to the graph
workflow.add_node("classify_reply", classify_reply_node)
workflow.add_node("determine_final_status", determine_final_status_node)

# Define the entry point
workflow.set_entry_point("classify_reply")

# Add edges
# After classifying, always go to determine the final status
workflow.add_edge("classify_reply", "determine_final_status")
# The determine_final_status node is the end of this simple workflow
workflow.add_edge("determine_final_status", END)

# Compile the graph into a runnable application
approval_graph_app = workflow.compile()

# Function to run the graph (can be called from FastAPI)
async def run_approval_graph(service_line: str, threshold: int, justification_email: str, user_reply: str) -> dict:
    """Runs the approval graph with the given inputs."""
    initial_state = {
        "service_line": service_line,
        "threshold": threshold,
        "justification_email": justification_email,
        "user_reply": user_reply,
        "classification": "", # Initial empty values
        "final_status": ""     # Initial empty values
    }
    # Use ainvoke for asynchronous execution
    final_state = await approval_graph_app.ainvoke(initial_state)
    return final_state

# Example Usage (Optional - for testing)
# import asyncio
# async def main_test():
#     print("Testing Approved Scenario:")
#     result_pos = await run_approval_graph("Data Migration", 50, "Subject: Approval...", "Sounds good, please proceed.")
#     print("\nFinal State (Approved):", result_pos)
# 
#     print("\nTesting Rejected Scenario:")
#     result_neg = await run_approval_graph("Cloud Setup", 45, "Subject: Approval...", "No, hold off for now.")
#     print("\nFinal State (Rejected):", result_neg)
# 
#     print("\nTesting Auto-Approved Scenario (Simulated - Graph input):")
#     # In reality, the graph might not run or run differently if threshold <= 30
#     # This simulates providing no reply, leading to rejection by the graph's current logic
#     result_auto = await run_approval_graph("Minor Update", 20, "", "") 
#     print("\nFinal State (Auto/No Reply):", result_auto)
#
# if __name__ == "__main__":
#     asyncio.run(main_test()) 