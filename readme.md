Okay, here is detailed documentation for the provided full-stack approval application codebase.

---

# Approval Application Documentation

## 1. Overview

This application provides a simple web interface for submitting requests that may require approval based on a numerical threshold. If the threshold exceeds a predefined limit (30 in this case), the application generates a sample approval email, prompts the user for a reply, and then uses an AI model (Azure OpenAI GPT via LangChain/LangGraph) to classify the user's reply as "Approved" or "Not Approved". Requests below or equal to the threshold are automatically approved client-side.

The application consists of:

*   **Frontend:** A simple HTML/CSS/TypeScript interface built potentially using Vite (implied by structure). It handles user input, basic threshold logic, and communication with the backend API.
*   **Backend:** A Python FastAPI server that exposes an API endpoint to process approval requests. It uses LangGraph to orchestrate the approval logic, which involves calling an Azure OpenAI model via LangChain to classify user replies.

## 2. Project Structure

```
.
├── backend/
│   ├── approval_graph.py  # Defines the LangGraph approval workflow
│   ├── azure_gpt.py       # Handles interaction with Azure OpenAI API via LangChain
│   ├── main.py            # FastAPI application, API endpoints
│   └── .env               # (Needs to be created) Environment variables (Azure keys, etc.)
│   └── requirements.txt   # (Should be created) Python dependencies
├── frontend/
│   ├── api.ts             # Frontend API client for backend communication
│   ├── index.html         # Main HTML structure for the frontend
│   ├── main.ts            # Frontend logic (DOM manipulation, event handling)
│   ├── style.css          # (Referenced but not provided) CSS styling
│   └── vite.svg           # Vite icon (implies Vite tooling)
├── package.json           # (Implied) Frontend Node.js dependencies
└── tsconfig.json          # (Implied) TypeScript configuration
```

## 3. Technology Stack

*   **Frontend:**
    *   HTML5
    *   CSS3 (via `style.css`)
    *   TypeScript
    *   Vite (Likely build tool/dev server)
    *   `fetch` API (for backend communication)
*   **Backend:**
    *   Python 3.x
    *   FastAPI (Web framework)
    *   Uvicorn (ASGI server)
    *   Pydantic (Data validation)
    *   LangChain (`langchain-openai`, `langchain-core`)
    *   LangGraph (`langgraph`)
    *   Azure OpenAI SDK (`openai`)
    *   `python-dotenv` (Environment variable management)

## 4. Setup and Running

### 4.1 Prerequisites

*   Node.js and npm (or yarn) installed.
*   Python 3.8+ and pip installed.
*   Access to an Azure OpenAI account with a deployed GPT model (GPT-4o is implied by `AzureChatOpenAI` default but depends on your deployment).
*   Azure OpenAI Endpoint, API Key, Deployment Name, and API Version.

### 4.2 Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```
2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```
3.  **Create a `requirements.txt` file** (if not present) with the following content:
    ```txt
    fastapi
    uvicorn[standard]
    pydantic
    langchain
    langchain-openai
    langchain-core
    langgraph
    openai
    python-dotenv
    ```
4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Create a `.env` file** in the `backend` directory and add your Azure credentials:
    ```env
    AZURE_OPENAI_ENDPOINT="YOUR_AZURE_ENDPOINT"
    AZURE_OPENAI_API_KEY="YOUR_AZURE_API_KEY"
    AZURE_OPENAI_CHAT_DEPLOYMENT_NAME="YOUR_DEPLOYMENT_NAME"
    AZURE_OPENAI_API_VERSION="YOUR_API_VERSION"
    # Optional: Define a different port if needed
    # PORT=8001
    ```
6.  **Run the FastAPI server:**
    From the *parent directory* (the root of the project), run:
    ```bash
    python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
    ```
    *   `--reload`: Enables auto-reloading during development.
    *   `--host 0.0.0.0`: Makes the server accessible from your network (and the frontend dev server).
    *   `--port 8000`: Specifies the port (matches `API_BASE_URL` in `frontend/api.ts`).

### 4.3 Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd ../frontend
    # Or from the root: cd frontend
    ```
2.  **Install dependencies:**
    ```bash
    npm install
    # or if using yarn:
    # yarn install
    ```
3.  **Run the development server:**
    ```bash
    npm run dev
    # or if using yarn:
    # yarn dev
    ```
4.  **Access the application:** Open your web browser and navigate to the URL provided by the Vite dev server (usually `http://localhost:5173`).

## 5. Workflow

1.  **User Interaction:** The user opens the web application (`index.html`).
2.  **Input Submission:** The user enters a "Service Line" (text) and a "Threshold" (number) into the main form (`#approval-form`) and clicks "Submit".
3.  **Frontend Logic (`main.ts`):**
    *   The form submission event is captured.
    *   The `currentServiceLine` and `currentThreshold` variables are updated.
    *   The previous result message (`#result-message`) is cleared.
    *   The approval section (`#approval-section`) is hidden.
    *   **Threshold Check:**
        *   If `currentThreshold <= 30`: The application displays "Task automatically approved..." in the `#result-message` div. No backend call is made for this specific scenario (though logging could be added).
        *   If `currentThreshold > 30`:
            *   A pre-formatted approval email text is generated and displayed in the read-only `#approval-email` textarea.
            *   The `#approval-section` containing the email preview and the reply textarea (`#reply`) is shown.
4.  **User Reply (if threshold > 30):**
    *   The user reads the generated email content.
    *   The user types their reply (e.g., "Approved", "No", "Need more info") into the `#reply` textarea.
    *   The user clicks the "Send" button (`#send-reply`).
5.  **Backend Request (`main.ts` -> `api.ts`):**
    *   The "Send" button's click event handler is triggered.
    *   Input validation checks if the reply is empty.
    *   The `sendReplyButton` is disabled, and a "Processing..." message is shown.
    *   The `sendApprovalRequest` function in `api.ts` is called with `currentServiceLine`, `currentThreshold`, the generated `approvalEmail` text, and the `userReply`.
    *   `sendApprovalRequest` makes a `POST` request to the backend's `/process-approval` endpoint with the data in JSON format.
6.  **Backend Processing (`main.py`):**
    *   The FastAPI server receives the POST request at `/process-approval`.
    *   The JSON payload is parsed and validated against the `ApprovalRequest` Pydantic model.
    *   **Threshold Check (Backend):** Although the frontend already checked, the backend *could* re-verify `request.threshold <= 30` for robustness (currently it does and returns "Auto-Approved" directly if <= 30, potentially duplicating frontend logic but ensuring backend consistency).
    *   **LangGraph Execution (if threshold > 30):**
        *   The `run_approval_graph` function (from `approval_graph.py`) is called asynchronously with the request details.
7.  **Approval Graph Logic (`approval_graph.py`):**
    *   The graph starts at the `classify_reply_node`.
    *   **`classify_reply_node`:** Calls `get_reply_classification` (from `azure_gpt.py`) with the `approval_email` and `user_reply`.
8.  **LLM Classification (`azure_gpt.py`):**
    *   The `get_reply_classification` function:
        *   Checks if the LLM client (`AzureChatOpenAI`) is initialized.
        *   Validates inputs. Handles empty replies (returns "Not Approved").
        *   Formats the input using the `prompt_template`, including the original email context and the user's reply.
        *   Sends the formatted prompt to the configured Azure OpenAI model via the LangChain chain (`prompt_template | llm | output_parser`).
        *   Parses the LLM's response. Based on the strict prompt, it expects "Approved" or something else.
        *   Returns the classification string: "Approved", "Not Approved", or "Error".
9.  **Approval Graph Continuation (`approval_graph.py`):**
    *   The classification result updates the graph's state.
    *   The graph transitions to the `determine_final_status_node`.
    *   **`determine_final_status_node`:** Sets the `final_status` in the state based on the `classification`:
        *   `classification == 'Approved'` -> `final_status = 'Approved'`
        *   `classification == 'Error'` -> `final_status = 'Error'`
        *   `classification == 'Not Approved'` -> `final_status = 'Rejected'`
    *   The graph reaches the `END` state.
10. **Backend Response (`main.py`):**
    *   The `run_approval_graph` function returns the final state dictionary.
    *   The `/process-approval` endpoint extracts the `final_status` and `classification` from the result.
    *   It constructs an `ApprovalResponse` Pydantic model (e.g., `{"status": "Approved", "detail": "Reply classified as: Approved"}`) and returns it as a JSON response with HTTP status 200.
    *   Handles potential exceptions during processing, returning HTTP 500 errors with details.
11. **Frontend Result Display (`main.ts`):**
    *   The `sendApprovalRequest` function receives the response from the backend.
    *   The `try...catch` block in the `sendReplyButton` event listener handles the response or error.
    *   On success:
        *   The backend status is displayed in `#result-message`.
        *   The `#approval-section` is hidden.
        *   The initial form (`#approval-form`) and reply textarea (`#reply`) are cleared/reset.
    *   On error:
        *   The error message is displayed in `#result-message`.
    *   Finally: The `sendReplyButton` is re-enabled.

## 6. Codebase Details

### 6.1 Frontend (`frontend/`)

*   **`index.html`**:
    *   Standard HTML5 structure.
    *   Includes basic form elements (`#approval-form`) for Service Line and Threshold input.
    *   Contains a hidden section (`#approval-section`) for displaying the generated approval email (`#approval-email`) and collecting the user's reply (`#reply`).
    *   Includes a button (`#send-reply`) within the approval section.
    *   Provides a div (`#result-message`) to display feedback and results to the user.
    *   Links to `style.css` for styling and loads the main TypeScript logic via `<script type="module" src="/main.ts"></script>`.
*   **`main.ts`**:
    *   **DOM Element References:** Gets references to all necessary HTML elements using `document.getElementById`.
    *   **State:** Uses module-level variables `currentServiceLine` and `currentThreshold` to store data between form submission and reply sending.
    *   **Event Listener (Form Submit):**
        *   Prevents default form submission.
        *   Reads input values, updates state variables.
        *   Implements the core client-side threshold logic: shows the approval section only if `threshold > 30`, otherwise displays an "Auto-Approved" message.
        *   Generates the sample approval email text.
    *   **Event Listener (Send Reply Button Click):**
        *   Handles the asynchronous process of sending the reply.
        *   Performs basic validation (checks for non-empty reply).
        *   Provides user feedback ("Processing...") and disables the button during the API call.
        *   Calls `sendApprovalRequest` from `api.ts`.
        *   Updates the UI based on the API response (success or error) using the `#result-message` div.
        *   Resets the form and hides the approval section on success.
        *   Re-enables the button in the `finally` block.
*   **`api.ts`**:
    *   **`API_BASE_URL`**: Defines the base URL for the backend API (defaults to `http://localhost:8000`). Needs adjustment if the backend runs elsewhere.
    *   **`sendApprovalRequest` function**:
        *   An `async` function responsible for making the actual network request to the backend.
        *   Takes `serviceLine`, `threshold`, `approvalEmail`, and `userReply` as arguments.
        *   Constructs the JSON `payload` expected by the backend.
        *   Uses the `fetch` API to send a `POST` request to `/process-approval`.
        *   Sets appropriate headers (`Content-Type: application/json`).
        *   Includes error handling:
            *   Checks `response.ok` to see if the HTTP status indicates success (2xx).
            *   If not okay, attempts to parse a JSON error detail from the backend response for a more informative error message.
            *   Throws an error if the request fails or the response is not okay.
        *   Parses the JSON response from the backend on success.
        *   Re-throws errors to be caught by the calling code in `main.ts`.

### 6.2 Backend (`backend/`)

*   **`main.py`**:
    *   **FastAPI App Initialization:** Creates the FastAPI application instance (`app`).
    *   **CORS Middleware:** Configures Cross-Origin Resource Sharing to allow requests from the frontend development server (`http://localhost:5173` and others). Essential for development.
    *   **Pydantic Models:**
        *   `ApprovalRequest`: Defines the expected structure and data types for the incoming request body.
        *   `ApprovalResponse`: Defines the structure and data types for the response sent back to the frontend.
    *   **`/process-approval` Endpoint:**
        *   Defined with `@app.post("/process-approval")`.
        *   Takes an `ApprovalRequest` object as input (FastAPI automatically handles request body parsing and validation).
        *   Returns an `ApprovalResponse`.
        *   Contains the main API logic: checks threshold, calls `run_approval_graph` if needed, constructs the response.
        *   Uses `HTTPException` to return appropriate HTTP error codes (400 for bad requests, 500 for server errors) with details.
        *   Includes basic `print` statements for logging request reception and results (consider using a proper logging library for production).
    *   **Uvicorn Runner (`if __name__ == "__main__":`)**:
        *   Standard Python entry point to run the FastAPI application using Uvicorn.
        *   Loads the `PORT` from environment variables (defaulting to 8000).
        *   Runs Uvicorn with `reload=True` for development convenience.
*   **`azure_gpt.py`**:
    *   **Environment Variable Loading:** Uses `dotenv.load_dotenv(override=True)` to load Azure credentials from the `.env` file.
    *   **Configuration:** Defines constants for Azure settings.
    *   **LLM Initialization:**
        *   Initializes the `AzureChatOpenAI` client from LangChain using the loaded environment variables.
        *   Includes error handling during initialization and sets `llm` to `None` if it fails.
        *   Sets `temperature=0` for more deterministic classification output.
    *   **Output Parser:** Initializes a `StrOutputParser` to get the raw string output from the LLM.
    *   **Prompt Template:**
        *   Uses `ChatPromptTemplate.from_messages` with system and human roles.
        *   The **system prompt** is crucial: it instructs the LLM to analyze the reply *in the context of the original email* and respond *only* with "Approved" or "Not Approved". This constraint simplifies parsing.
        *   The **human prompt** uses placeholders (`{approval_email}`, `{user_reply}`) to inject the specific request details.
    *   **`get_reply_classification` function:**
        *   The core asynchronous function for interacting with the LLM.
        *   Takes the original email content and the user's reply as strings.
        *   Performs checks: LLM initialization, input types, empty reply.
        *   Creates the LangChain Expression Language (LCEL) chain: `prompt_template | llm | output_parser`.
        *   Invokes the chain asynchronously (`await chain.ainvoke(...)`) with the input data.
        *   Parses the `result`: checks if it's the expected "Approved" string (case-insensitive).
        *   Returns "Approved", "Not Approved", or "Error" based on the LLM output or any exceptions during the process.
        *   Includes error logging.
    *   **Example Usage (`if __name__ == "__main__":`)**: Provides a way to test the classification function directly by running `python backend/azure_gpt.py`.
*   **`approval_graph.py`**:
    *   **State Definition (`ApprovalState`)**: Uses `TypedDict` to define the structure of the data that flows through the graph. This includes inputs and intermediate/final results.
    *   **Node Functions (`classify_reply_node`, `determine_final_status_node`):**
        *   Each node is an `async` function that takes the current `state` (an `ApprovalState` dictionary) as input and returns a dictionary containing the updates to the state.
        *   `classify_reply_node`: Calls `get_reply_classification` and updates the `classification` field in the state. Includes basic logging. Handles the case where no reply is present.
        *   `determine_final_status_node`: Takes the `classification` from the state and determines the `final_status` ('Approved', 'Rejected', 'Error'). Includes logging.
    *   **Conditional Logic (`decide_next_step` - *currently unused but good practice*):**
        *   A function that takes the state and returns the name of the *next* node to execute. In this simple graph, the flow is linear (`classify_reply` -> `determine_final_status`), so this isn't strictly needed for branching but demonstrates how conditional edges could be added. *Currently, direct edges are used instead.*
    *   **Graph Definition (`StateGraph`):**
        *   Initializes a `StateGraph` with the `ApprovalState`.
        *   Adds the defined nodes using `workflow.add_node()`.
        *   Sets the entry point using `workflow.set_entry_point()`.
        *   Defines the flow using `workflow.add_edge()`. Here, it's a simple sequence: `classify_reply` always goes to `determine_final_status`, which then goes to `END`.
    *   **Graph Compilation:** Compiles the graph definition into a runnable LangGraph application object (`approval_graph_app`).
    *   **`run_approval_graph` function:**
        *   An `async` wrapper function designed to be called externally (e.g., by the FastAPI endpoint).
        *   Takes the initial input parameters.
        *   Constructs the initial state dictionary.
        *   Invokes the compiled graph asynchronously (`await approval_graph_app.ainvoke(initial_state)`).
        *   Returns the final state dictionary after the graph has finished execution.
    *   **Example Usage (`if __name__ == "__main__":`)**: Provides a way to test the entire graph flow directly by running `python backend/approval_graph.py`.

## 7. API Reference

### Endpoint: `/process-approval`

*   **Method:** `POST`
*   **Description:** Processes an approval request. If the threshold is > 30, it uses an LLM to classify the user's reply provided in the context of the original request email.
*   **Request Body:**
    *   Content-Type: `application/json`
    *   Schema (`ApprovalRequest` Pydantic Model):
        ```json
        {
          "service_line": "string",
          "threshold": "integer",
          "approval_email": "string", // The email content shown to the user
          "user_reply": "string"      // The user's reply text
        }
        ```
*   **Success Response (200 OK):**
    *   Content-Type: `application/json`
    *   Schema (`ApprovalResponse` Pydantic Model):
        ```json
        {
          "status": "string", // e.g., "Approved", "Rejected", "Error", "Auto-Approved"
          "detail": "string | null" // Optional details, e.g., "Reply classified as: Approved"
        }
        ```
*   **Error Responses:**
    *   **400 Bad Request:** Returned if the `user_reply` is missing when `threshold > 30` (validation within the endpoint).
    *   **422 Unprocessable Entity:** Returned by FastAPI if the request body doesn't match the `ApprovalRequest` schema.
    *   **500 Internal Server Error:** Returned for unexpected errors during graph execution or LLM classification. The response body might contain:
        ```json
        {
          "detail": "Error message string"
        }
        ```

## 8. Configuration

The primary configuration is done via the `.env` file in the `backend` directory:

*   `AZURE_OPENAI_ENDPOINT`: The URL of your Azure OpenAI resource.
*   `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key.
*   `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME`: The name of your deployed chat model (e.g., gpt-4o, gpt-35-turbo).
*   `AZURE_OPENAI_API_VERSION`: The API version required by your Azure endpoint (e.g., "2024-02-01").
*   `PORT` (Optional): The port number for the backend FastAPI server (defaults to 8000 if not set).

## 9. Error Handling

*   **Frontend:**
    *   `api.ts` uses `try...catch` around the `fetch` call and checks `response.ok`. It attempts to parse backend error details.
    *   `main.ts` uses `try...catch` around the call to `sendApprovalRequest` and displays error messages in the `#result-message` div. Basic input validation (empty reply) uses `alert`.
*   **Backend:**
    *   FastAPI handles request validation errors automatically (422).
    *   The `/process-approval` endpoint uses `try...except` to catch general exceptions during processing and returns a 500 error with `HTTPException`. It also explicitly raises a 400 `HTTPException` if the reply is missing when required.
    *   `azure_gpt.py` catches exceptions during LLM initialization and classification, logging them and returning an "Error" classification string.
    *   LangGraph execution itself doesn't add explicit error handling in this simple setup, but errors within nodes propagate up and would likely be caught by the `try...except` block in `main.py`.

## 10. Potential Improvements

*   **Robust Error Handling:** Implement more specific exception handling in the backend (e.g., for network errors connecting to Azure). Provide clearer error messages to the frontend.
*   **Logging:** Replace `print` statements in the backend with a proper logging library (like Python's built-in `logging`).
*   **Input Validation:** Add more robust validation on both frontend and backend (e.g., ensure threshold is a positive number).
*   **Security:**
    *   Consider user authentication/authorization if this were a real application.
    *   Sanitize user inputs more thoroughly.
    *   Review CORS configuration for production environments.
*   **Database Integration:** Log requests and their outcomes to a database for auditing and tracking.
*   **LLM Prompt Engineering:** Refine the system prompt in `azure_gpt.py` for better accuracy or to handle edge cases (e.g., ambiguous replies). Could potentially ask for a reason alongside the classification.
*   **Graph Complexity:** The LangGraph structure is simple. It could be expanded with more steps (e.g., escalation path if rejected, request clarification if the reply is ambiguous).
*   **Frontend UX:** Improve the user interface (loading spinners, better feedback messages, styling).
*   **Testing:** Add unit tests (e.g., for `get_reply_classification`, graph nodes) and integration tests (testing the API endpoint).
*   **Configuration Management:** Use a more structured configuration approach for larger applications (e.g., Pydantic's `BaseSettings`).
*   **Deployment:** Add instructions and configurations for deploying the frontend and backend (e.g., using Docker, serverless platforms, etc.).

---