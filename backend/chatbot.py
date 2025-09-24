from openai import OpenAI

from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_prd(query: str) -> str:
    """
    Hàm nhận vào query (mô tả app), sinh ra bản PRD draft bằng GPT.
    """
    system_prompt = """
    Bạn là một Product Manager AI.
    Nhiệm vụ của bạn: nhận mô tả ngắn về một ứng dụng và sinh ra một PRD (Product Requirement Document) draft.
    PRD phải bao gồm các phần sau:
    1. Mục tiêu sản phẩm
    2. Persona & Use cases
    3. Các tính năng chính
    4. User flow (tóm tắt)
    5. Yêu cầu kỹ thuật cơ bản
    6. Rủi ro & giả định
    7. Success metrics

    Output phải ở dạng tài liệu, rõ ràng, có heading cho từng mục.
    """

    response = client.chat.completions.create(
        model="gpt-4.1",  # hoặc "gpt-4o-mini", tuỳ tài khoản
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content


# Ví dụ chạy thử
if __name__ == "__main__":
    user_query = "Tôi muốn làm một app quản lý chi tiêu cá nhân, có báo cáo trực quan và nhắc nhở khi vượt hạn mức."
    prd_output = generate_prd(user_query)
    print(prd_output)
