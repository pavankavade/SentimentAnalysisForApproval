from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os

# Import the graph runner function from our approval_graph module
# Assuming this script is run from the parent directory of 'backend'
# or backend is in PYTHONPATH
from backend.approval_graph import run_approval_graph

# --- Pydantic Models for Request/Response --- 

class ApprovalRequest(BaseModel):
    service_line: str
    threshold: int
    approval_email: str    # The email content shown to the user if threshold > 30
    user_reply: str        # The user's reply text

class ApprovalResponse(BaseModel):
    status: str # e.g., "Approved", "Rejected", "Error", "Auto-Approved", "Clarification"
    detail: str | None = None # Optional field for more details
    extracted_data: dict | None = None # Optional field for extracted data

class ClarificationRequest(BaseModel):
    service_line: str
    threshold: int
    approval_email: str
    user_reply: str
    hiring_manager_reply: str

# --- FastAPI Application Setup ---

app = FastAPI(title="Approval Processing API")

# Configure CORS (Cross-Origin Resource Sharing)
# Allows requests from the default Vite development server origin
# Adjust the origins if your frontend runs on a different port/domain
origins = [
    "http://localhost",
    "http://localhost:5173", # Default Vite dev server
    "http://127.0.0.1:5173",
    # Add other origins if needed (e.g., your deployed frontend URL)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"]
)

@app.post("/process-approval")
async def process_approval(request: ApprovalRequest) -> ApprovalResponse:
    """
    Endpoint to process an approval request.
    - If threshold <= 30, it's auto-approved.
    - If threshold > 30, it runs the LangGraph workflow to classify the reply.
    """
    print(f"Received request: {request.dict()}")

    if request.threshold <= 30:
        print("Threshold <= 30, auto-approving.")
        # Optionally log this auto-approval somewhere
        return ApprovalResponse(status="Auto-Approved", detail="Threshold was not exceeded.")
    
    # Threshold > 30, requires justification and reply analysis
    if not request.user_reply:
         # Should not happen if frontend logic is correct, but handle defensively
         print("Error: Reply is required when threshold > 30")
         raise HTTPException(status_code=400, detail="User reply is required when threshold > 30.")

    try:
        print("Running approval graph...")
        # Run the LangGraph workflow
        graph_result = await run_approval_graph(
            service_line=request.service_line,
            threshold=request.threshold,
            approval_email=request.approval_email, 
            user_reply=request.user_reply
        )
        
        print(f"Graph Result: {graph_result}")

        final_status = graph_result.get('final_status', 'Error') # Default to Error if key missing
        detail_message = f"Reply classified as: {graph_result.get('classification', 'N/A')}"
        
        if final_status == "Clarification":
            return ApprovalResponse(status="Clarification", detail="Clarification required from hiring manager.")
        
        if final_status == "Error":
             print("Error occurred within the approval graph.")
             # Consider more specific error handling based on graph output
             raise HTTPException(status_code=500, detail="Processing error in the approval workflow.")

        return ApprovalResponse(status=final_status, detail=detail_message)

    except Exception as e:
        print(f"Error processing approval request: {e}")
        # Log the exception details for debugging
        # Consider more specific exception handling (e.g., Azure connection errors)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.post("/process-clarification")
async def process_clarification(request: ClarificationRequest) -> ApprovalResponse:
    """
    Endpoint to process a clarification request.
    - Runs the LangGraph workflow with the hiring manager's reply.
    - Extracts and validates hiring manager details.
    """
    print(f"Received clarification request: {request.dict()}")
    try:
        graph_result = await run_approval_graph(
            service_line=request.service_line,
            threshold=request.threshold,
            approval_email=request.approval_email,
            user_reply=request.user_reply,
            hiring_manager_reply=request.hiring_manager_reply
        )
        print(f"Clarification Graph Result: {graph_result}")

        final_status = graph_result.get('final_status', 'Error') # Default to Error if key missing
        extracted_data = graph_result.get('extracted_data') # Extracted data from the graph result
        missing_fields = graph_result.get('missing_fields', [])

        if final_status == "Approved" and extracted_data:
            return ApprovalResponse(status="Approved", detail="Hiring manager details extracted and approved.", extracted_data=extracted_data)
        elif final_status == "Error" and missing_fields:
            raise HTTPException(status_code=400, detail=f"Missing or invalid hiring manager details. Missing fields: {', '.join(missing_fields)}")
        else:
            raise HTTPException(status_code=400, detail="Missing or invalid hiring manager details.")

    except Exception as e:
        print(f"Error processing clarification: {e}")
        # Log the exception details for debugging
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# --- Run the application ---

if __name__ == "__main__":
    # Ensure environment variables are loaded (if not already by azure_gpt/approval_graph)
    # from dotenv import load_dotenv
    # load_dotenv() 
    
    # Get port from environment variable or default to 8000
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting FastAPI server on port {port}...")
    # Use reload=True for development to automatically reload server on code changes
    # Explicitly specify the app location for uvicorn when running with python -m
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)