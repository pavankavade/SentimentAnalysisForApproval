from typing import TypedDict, Annotated, Union
import operator
from langgraph.graph import StateGraph, END

# Import the classification function from our azure_gpt module
# We use a relative import assuming main.py will run from the backend directory's parent
# or that the backend directory is added to PYTHONPATH.
# If running main.py directly within backend/, use: from azure_gpt import ...
from .azure_gpt import get_reply_classification, extract_hiring_manager_fields

# Define the state structure for our graph
class ApprovalState(TypedDict):
    """Represents the state of the approval workflow."""
    service_line: str
    threshold: int
    approval_email: str    # The email sent *to* the user (if threshold > 30)
    user_reply: str        # The reply received *from* the user
    classification: str    # Result of the LLM classification ('Approved', 'Not Approved', 'Clarification', 'Error')
    final_status: str      # The final outcome ('Approved', 'Rejected', 'Error')
    clarification_needed: bool  # True if clarification is required
    hiring_manager_reply: str   # The reply from the hiring manager
    extracted_data: dict        # Extracted info from hiring manager

# Define the nodes for our graph

async def classify_reply_node(state: ApprovalState) -> dict:
    """Classifies the user's reply using the LLM."""
    print("--- Classifying Reply Node ---")
    user_reply = state['user_reply']
    approval_email = state['approval_email']
    
    # Handle the case where threshold was <= 30 and no reply is expected/needed
    # Or if the request failed before getting a reply
    if not user_reply:
        print("No user reply provided, assuming Not Approved.")
        # If threshold > 30, lack of reply means rejection.
        return {"classification": "Not Approved", "clarification_needed": False} 
        
    # Pass both the original email and the reply
    classification_result = await get_reply_classification(approval_email, user_reply)
    print(f"Classification Result: {classification_result}")
    clarification_needed = classification_result == "Clarification"
    return {"classification": classification_result, "clarification_needed": clarification_needed}

async def clarification_node(state: ApprovalState) -> dict:
    """Handles clarification by waiting for hiring manager reply and extracting required fields."""
    print("--- Clarification Node ---")
    hiring_manager_reply = state.get('hiring_manager_reply', '')
    approval_email = state.get('approval_email', '')
    if not hiring_manager_reply:
        print("No hiring manager reply provided.")
        return {"final_status": "Error"}
    # Use LLM extraction instead of regex
    result = await extract_hiring_manager_fields(approval_email, hiring_manager_reply)
    status = result.get("status", "Error")
    extracted = result.get("extracted_data", {})
    missing = result.get("missing_fields", [])
    if status == "Approved" and all(extracted.values()):
        print(f"Extracted Data: {extracted}")
        return {"final_status": "Approved", "extracted_data": extracted}
    else:
        print(f"Missing required fields in hiring manager reply or not approved. Missing: {missing}")
        return {"final_status": "Error", "missing_fields": missing}

async def set_status_node(state: ApprovalState) -> dict:
    """Sets the status based on classification."""
    print("--- Setting Status Node ---")
    classification = state['classification']
    final_status = "Rejected" # Default to Rejected
    if classification == 'Approved':
        final_status = "Approved"
    elif classification == 'Clarification':
        final_status = "Clarification"
    elif classification == 'Error':
        final_status = "Error"
        print("Error during classification process.")
    print(f"Final Status: {final_status}")
    return {"final_status": final_status}

# Define the conditional logic for branching
def decide_next_step(state: ApprovalState) -> dict:
    """Decides the next step based on the classification and presence of hiring manager reply."""
    if state.get("final_status") == "Clarification":
        # Only proceed to clarification node if hiring_manager_reply is present
        if state.get("hiring_manager_reply"):
            return {"next": "clarification"}
        else:
            # End the graph here, wait for separate trigger (from /process-clarification)
            return {"next": END}
    return {"next": END}

# Create the StateGraph
workflow = StateGraph(ApprovalState)

# Add nodes to the graph
workflow.add_node("classify_reply", classify_reply_node)
workflow.add_node("set_status", set_status_node)
workflow.add_node("decision", decide_next_step)
workflow.add_node("clarification", clarification_node)

# Define the entry point
workflow.set_entry_point("classify_reply")

# Add edges
workflow.add_edge("classify_reply", "set_status")
workflow.add_edge("set_status", "decision")
workflow.add_conditional_edges(
    "decision",
    lambda state: state["next"],
    {
        "clarification": "clarification",
        END: END,
    }
)

# Compile the graph into a runnable application
approval_graph_app = workflow.compile()

# Function to run the graph (can be called from FastAPI)
async def run_approval_graph(service_line: str, threshold: int, approval_email: str, user_reply: str, hiring_manager_reply: str = "") -> dict:
    """Runs the approval graph with the given inputs."""
    initial_state = {
        "service_line": service_line,
        "threshold": threshold,
        "approval_email": approval_email,
        "user_reply": user_reply,
        "classification": "", # Initial empty values
        "final_status": "",     # Initial empty values
        "clarification_needed": False,
        "hiring_manager_reply": hiring_manager_reply,
        "extracted_data": {},
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