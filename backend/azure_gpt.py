import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables from .env file
load_dotenv()

# Configure the Azure OpenAI client
try:
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature=0 # We want deterministic classification
    )
except Exception as e:
    print(f"Error initializing AzureChatOpenAI: {e}")
    # Consider raising the exception or handling it more gracefully
    # depending on application requirements. For now, we print and exit
    # or allow subsequent code to fail if llm is None.
    llm = None # Ensure llm is defined, even if initialization fails

# Define a simple output parser
output_parser = StrOutputParser()

# Define the classification prompt template
# We ask for a single word response for easy parsing.
prompt_template = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are an assistant that analyzes email replies to determine if they signify approval or rejection. Respond with only the single word 'positive' if the reply indicates approval, and 'negative' if it indicates rejection or asks for more information."),
    HumanMessage(content="Here is the user's reply:\n\n{user_reply}")
])


async def get_reply_classification(user_reply: str) -> str:
    """
    Classifies the user's reply as 'positive' or 'negative' using Azure GPT-4o.

    Args:
        user_reply: The text content of the user's reply.

    Returns:
        A string, either 'positive' or 'negative'.
        Returns 'error' if classification fails.
    """
    if not llm:
        print("Azure LLM client is not initialized.")
        return "error"
    
    if not user_reply or not user_reply.strip():
        return "negative" # Treat empty replies as negative

    try:
        # Create the chain
        chain = prompt_template | llm | output_parser

        # Invoke the chain asynchronously
        result = await chain.ainvoke({"user_reply": user_reply})

        # Basic validation of the result
        cleaned_result = result.strip().lower()
        if cleaned_result == "positive":
            return "positive"
        else:
            # Default to negative if the response isn't exactly "positive"
            return "negative"

    except Exception as e:
        print(f"Error during LLM classification: {e}")
        return "error" # Indicate failure

# Example usage (optional, for testing)
# import asyncio
# async def main():
#     test_reply_positive = "Yes, I approve this request."
#     test_reply_negative = "No, I cannot approve this at this time."
#     classification_pos = await get_reply_classification(test_reply_positive)
#     classification_neg = await get_reply_classification(test_reply_negative)
#     print(f"Positive reply classification: {classification_pos}")
#     print(f"Negative reply classification: {classification_neg}")

# if __name__ == "__main__":
#     asyncio.run(main()) 