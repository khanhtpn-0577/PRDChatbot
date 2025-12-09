from openai import OpenAI
from dotenv import load_dotenv
from core.summarizer import get_latest_summary
from core.moscow import moscow_define_priority
from core.deep_research import *
from core.utils.json_parser import *

load_dotenv()
client = OpenAI()

async def prd_chatbot(section_id, user_input, chat_history, is_deep_research, BUFFER_SIZE=5):
    latest_summary = get_latest_summary(section_id)
    if is_deep_research:
        deep_research_output = await deep_research(user_input, 3)
    
    prd_output = await moscow_define_priority(
        lattest_summary=latest_summary,
        user_input=user_input,
        chat_history=chat_history,
        deep_research_string=deep_research_output,
        BUFFER_SIZE=BUFFER_SIZE
    )
    
    json_data = parse_prd_json(prd_output)

    return {
        "raw": prd_output,
        "json": json_data     # None nếu không parse được
    }