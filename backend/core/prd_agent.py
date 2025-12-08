from openai import OpenAI
from dotenv import load_dotenv
from core.summarizer import get_latest_summary
from core.moscow import moscow_define_priority

load_dotenv()
client = OpenAI()

async def prd_chatbot(section_id, user_input, chat_history, BUFFER_SIZE=5):
    latest_summary = get_latest_summary(section_id)
    deep_research = "None"  # Placeholder for deep research data if available
    
    prd_output = await moscow_define_priority(
        lattest_summary=latest_summary,
        user_input=user_input,
        chat_history=chat_history,
        deep_research=deep_research,
        BUFFER_SIZE=BUFFER_SIZE
    )
    
    #print("PRD OUTPUT FROM MOSCOW FUNCTION:", prd_output)
    return prd_output