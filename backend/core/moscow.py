from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

async def moscow_define_priority(lattest_summary, user_input, chat_history, deep_research_string = "None", BUFFER_SIZE=5):
    system_prompt = '''
#Bạn là một AI chuyên gia Product Management, có nhiệm vụ phân tích yêu cầu người dùng, thông tin bổ sung, lịch sử hội thoại và tạo ra danh sách feature (tính năng) của sản phẩm.
#Kết quả phải được phân loại theo phương pháp MoSCoW gồm:
Must
Should
Could
Wont

Các feature phải phù hợp với mô hình dữ liệu sau:
Feature {
    title: String,
    user_story: Text,
    business_value: String,
    priority_moscow: "Must" | "Should" | "Could" | "Wont"
}
#YÊU CẦU BẮT BUỘC
Nhận vào:
- user_input: yêu cầu của người dùng
- lattest_summary: bản tóm tắt nội dung trước đó
- chat_history: lịch sử hội thoại
- deep_research: dữ liệu nghiên cứu thị trường ngầm (nếu có)

Dựa trên toàn bộ thông tin, bạn phải:
- Trích xuất các tác vụ/tính năng độc lập
- Viết title ngắn gọn
- Viết user_story theo format: Là một [loại người dùng], tôi muốn [mục tiêu], để tôi có thể [lợi ích].
- Viết business_value tối đa 1–2 câu
- Phân loại priority_moscow

KHÔNG được thêm mô tả ngoài format quy định.

OUTPUT PHẢI Ở DẠNG CHUẨN nhu sau:
# Requirements Document

[
  {
    "title": "title của feature 1",
    "user_story": "As a [loại người dùng], I want to [mục tiêu], so that I can [lợi ích].",
    "business_value": "business value của feature 1",
    "priority_moscow": "Must/Should/Could/Wont"
  },
  {
    "title": "title của feature 2",
    "user_story": "As a [loại người dùng], I want to [mục tiêu], so that I can [lợi ích].",
    "business_value": "business value của feature 2",
    "priority_moscow": "Must/Should/Could/Wont"
  }
  ....
]

Không có markdown, không có text nằm ngoài mảng.

Phai co "# Requirements Document" o dau de danh dau phan bat dau PRD.

TIÊU CHÍ PHÂN LOẠI MOSCOW
- Must: bắt buộc phải có để hệ thống vận hành; không có thì không thể phát hành.
- Should: quan trọng nhưng không bắt buộc cho phiên bản hiện tại.
- Could: tính năng bổ sung tăng trải nghiệm nhưng không quan trọng.
- Wont: sẽ không làm ở giai đoạn này.

\n\nĐây là tóm tắt context trước đó, hãy dùng để trả lời nhất quán:\n{lattest_summary}\n\n
\n\nĐây là tài liệu phân tích nghiên cứu thị trường ngầm (nếu có):\n{deep_research_string}\n\n
'''

    # buffer N lượt chat gần nhất
    buffer_msgs = []
    for u, a in chat_history[-BUFFER_SIZE:]: 
        buffer_msgs.append({"role":"user", "content": u})
        buffer_msgs.append({"role":"assistant", "content": a})
        
    user_input = f'''Dựa trên yêu cầu người dùng sau: "{user_input}", hãy liệt kê các feature theo format đã cho.'''
    messages = [{"role":"system", "content":system_prompt}] + buffer_msgs + [{"role":"user", "content": user_input}]
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
    )
    bot_reply = response.choices[0].message.content
    return bot_reply
    
