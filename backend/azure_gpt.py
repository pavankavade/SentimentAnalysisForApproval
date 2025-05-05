import os
import asyncio
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage # Keep imports for context

# Load environment variables from .env file, overriding existing OS variables
load_dotenv(override=True)

# --- Configuration ---
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

# --- Initialize LLM Client ---
llm = None
try:
    if not all([AZURE_ENDPOINT, AZURE_API_KEY, AZURE_DEPLOYMENT, AZURE_API_VERSION]):
        raise ValueError("One or more Azure OpenAI environment variables are missing.")

    llm = AzureChatOpenAI(
        azure_endpoint=AZURE_ENDPOINT,
        api_key=AZURE_API_KEY,
        azure_deployment=AZURE_DEPLOYMENT,
        api_version=AZURE_API_VERSION,
        temperature=0 # We want deterministic classification
    )
    print("AzureChatOpenAI client initialized successfully.")
except Exception as e:
    print(f"ERROR: Error initializing AzureChatOpenAI: {e}")
    # llm remains None

# --- Output Parser ---
output_parser = StrOutputParser()

# --- Prompt Template ---
# Using the tuple format ("role", "template_string") for reliable placeholder substitution
prompt_template = ChatPromptTemplate.from_messages([
    ("system", (
        "Analyze the user reply sentiment based on the original request email. Classify the reply as one of the following: 'Approved', 'Not Approved', or 'Clarification'. "
        "If the reply is an approval (e.g., contains 'approved', 'yes', 'proceed', 'good to go', 'ok', 'confirm', 'confirmation'), respond ONLY with 'Approved'. "
        "If the reply is a rejection or negative (e.g., 'no', 'not approved', 'cannot', 'reject'), respond ONLY with 'Not Approved'. "
        "If the reply asks for more information or clarification (e.g., contains questions like 'what', 'why', 'how', 'can you explain', 'need more info', 'clarify', 'details', 'please provide', 'could you'), respond ONLY with 'Clarification'. "
        "Do not add any explanation or commentary."
    )),
    ("human", (
        "Original Request Email:\n---\n{approval_email}\n---\n\n"
        "User's Reply:\n---\n{user_reply}"
    ))
])

# --- Clarification Extraction Function ---
clarification_prompt_template = ChatPromptTemplate.from_messages([
    ("system", (
        "You are an assistant that extracts required fields from a hiring manager's reply. "
        "Given the original approval email and the hiring manager's reply, extract the following fields: Name, Years of Experience, SL to SL change. "
        "Respond ONLY in the following JSON format: {{\"Name\": ..., \"Years of Experience\": ..., \"SL to SL change\": ...}}. "
        "If any field is missing or unclear, set its value to null. "
        "If all fields are present and non-null, respond with JSON and the word 'Approved' on a new line. "
        "If any field is missing, respond with JSON and the word 'Not Approved' on a new line. "
        "Do not add any explanation or commentary."
    )),
    ("human", (
        "Original Approval Email:\n---\n{approval_email}\n---\n\n"
        "Hiring Manager Reply:\n---\n{hiring_manager_reply}"
    ))
])

async def extract_hiring_manager_fields(approval_email: str, hiring_manager_reply: str) -> dict:
    """
    Uses Azure GPT to extract Name, Years of Experience, and SL to SL change from the hiring manager's reply.
    Returns a dict: { 'status': 'Approved'|'Not Approved'|'Error', 'extracted_data': {...}, 'missing_fields': [...] }
    """
    if not llm:
        print("ERROR: Azure LLM client is not initialized in extract_hiring_manager_fields.")
        return {"status": "Error", "extracted_data": {}, "missing_fields": ["LLM not initialized"]}

    required_fields = ["Name", "Years of Experience", "SL to SL change"]
    try:
        input_data = {
            "approval_email": approval_email,
            "hiring_manager_reply": hiring_manager_reply
        }
        chain = clarification_prompt_template | llm | output_parser
        result = await chain.ainvoke(input_data)
        # Expecting: JSON on first line, status on second line
        if isinstance(result, str):
            lines = result.strip().split("\n")
            json_part = lines[0]
            status = lines[1].strip() if len(lines) > 1 else "Not Approved"
            import json as pyjson
            try:
                extracted = pyjson.loads(json_part)
            except Exception as e:
                print(f"Failed to parse JSON from LLM: {e}, raw: {json_part}")
                extracted = {}
            # Check for missing fields
            missing = [field for field in required_fields if not extracted.get(field)]
            if missing:
                status = "Not Approved"
            return {"status": status, "extracted_data": extracted, "missing_fields": missing}
        else:
            print(f"Unexpected LLM output: {result}")
            return {"status": "Error", "extracted_data": {}, "missing_fields": ["Unexpected LLM output"]}
    except Exception as e:
        print(f"ERROR during clarification extraction: {e}")
        return {"status": "Error", "extracted_data": {}, "missing_fields": [str(e)]}

# --- Classification Function ---
async def get_reply_classification(approval_email: str, user_reply: str) -> str:
    """
    Classifies the user's reply as 'Approved', 'Not Approved', or 'Clarification' using Azure GPT-4o,
    considering the context of the original email.

    Args:
        approval_email: The content of the original email sent for approval.
        user_reply: The text content of the user's reply.

    Returns:
        A string: 'Approved', 'Not Approved', or 'Clarification'.
        Returns 'Error' if classification fails or LLM is not available.
    """
    if not llm:
        print("ERROR: Azure LLM client is not initialized in get_reply_classification.")
        return "Error"

    # Basic validation
    if not isinstance(approval_email, str) or not isinstance(user_reply, str):
        print(f"ERROR: Invalid input types. Email: {type(approval_email)}, Reply: {type(user_reply)}")
        return "Error"

    cleaned_user_reply = user_reply.strip()
    if not cleaned_user_reply:
        return "Not Approved"

    try:
        input_data = {
            "approval_email": approval_email,
            "user_reply": user_reply
        }

        chain = prompt_template | llm | output_parser
        result = await chain.ainvoke(input_data)
        print(f"LLM Result: {result}")
        if result and isinstance(result, str):
            result_clean = result.strip().lower()
            if result_clean == "approved":
                return "Approved"
            elif result_clean == "clarification":
                return "Clarification"
            else:
                return "Not Approved"
        else:
            print(f"WARNING: LLM produced unexpected output: '{result}'. Classifying as Not Approved.")
            return "Not Approved"

    except Exception as e:
        print(f"ERROR during LLM classification: {e}")
        print(f"Occurred with endpoint: {AZURE_ENDPOINT}, deployment: {AZURE_DEPLOYMENT}")
        return "Error"

# --- Example Usage (Optional) ---
async def main():
    print("\n--- Running Example Classification ---")
    if not llm:
        print("Cannot run example: LLM client not initialized.")
        return

    test_approval_email = 'Subject: Action Required: test\n\nPlease review the request for Service Line: test (Threshold: 33).\n\nYour confirmation is needed to proceed. Please reply with your decision.\n\nThanks.'
    test_user_reply_approve = 'Approved'
    test_user_reply_confirm = 'confirmation'
    test_user_reply_reject = 'No, cannot approve this now.'
    test_user_reply_question = 'What is this for?'
    test_user_reply_empty = ''

    test_cases = {
        "Direct 'Approved'": test_user_reply_approve,
        "Confirmation": test_user_reply_confirm,
        "Rejection": test_user_reply_reject,
        "Question": test_user_reply_question,
        "Empty Reply": test_user_reply_empty,
    }

    for name, reply in test_cases.items():
        print(f"\n--- Testing Case: {name} ---")
        print(f"User Reply: '{reply}'")
        classification_result = await get_reply_classification(test_approval_email, reply)
        # Print the final outcome clearly
        print(f"Classification Result: {classification_result}")
        # await asyncio.sleep(1) # Optional delay

    print("\n--- Example Classification Finished ---")


if __name__ == "__main__":
    if llm:
        try:
            asyncio.run(main())
        except Exception as main_e:
            print(f"ERROR: Error running main async function: {main_e}")
    else:
        print("Script finished: LLM client failed to initialize, cannot run example.")