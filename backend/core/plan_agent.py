import os
import sys
import uuid
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.db_models import PRD, Architecture, Plan, Base

# ================== CONFIG ==================
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

client = OpenAI(api_key=OPENAI_API_KEY)

def plan_chatbot(user_input):
    system_prompt = '''
Bạn là một Software Architect có kinh nghiệm.
Hãy đọc kỹ Requirements Document và Design Document được cung cấp, sau đó tạo ra Implementation Plan chi tiết, mô tả toàn bộ các bước triển khai hệ thống từ backend, frontend, services, đến testing và deployment.

Yêu cầu đầu ra: Trả về một Implementation Plan có cấu trúc như sau:

# Implementation Plan

- 1. [Tên hạng mục lớn]  
  - [Các tác vụ cụ thể cần thực hiện]
  - _Requirements: [liệt kê các mã requirement liên quan, ví dụ 2.1, 4.3, 7.2]_

- 2. [Tên hạng mục lớn]  
  - [Các tác vụ cụ thể cần thực hiện]
  - _Requirements: [các mã requirement liên quan]_
...


Quy tắc và hướng dẫn:
1)Phân tích Requirements và Design song song:
- Mapping từng Requirement đến các thành phần trong Design (service, component, model).
- Xác định rõ phần nào thuộc backend, phần nào frontend.

2)Nhóm các bước theo logic triển khai:
- Bắt đầu từ thiết lập môi trường & cấu trúc dự án,
- Tiếp theo là data models, authentication, core services,
-Sau đó đến frontend components, analytics, notifications,
-Cuối cùng là testing, security, deployment.

3)Mỗi bước phải có mô tả hành động cụ thể:
- Ví dụ: “Tạo database migrations cho bảng Post và User”, “Implement OAuth flow cho Facebook, Twitter”, “Viết tests cho API endpoints”…
-Tránh mô tả chung chung như “Xây dựng backend”.

4)Mapping rõ ràng đến Requirements:
- Sau mỗi nhóm hoặc task, thêm dòng _Requirements: 1.1, 2.2, 3.1_ để thể hiện mối liên hệ.

5)Không cần lặp lại nội dung của Requirements hoặc Design – chỉ tóm tắt và triển khai hành động tương ứng.

6)Format đầu ra:
- Giữ nguyên dạng markdown như ví dụ mẫu.
- Mỗi mục lớn bắt đầu bằng “- [số thứ tự]. [Tên hạng mục]”.
- Các tiểu mục bên trong dùng “-” thụt dòng.
- Các phần con (ví dụ 4.1, 5.2) chỉ dùng khi cần chia nhỏ bước rõ ràng.

Mục tiêu:
Tạo ra một kế hoạch triển khai thực tế, có thể chuyển trực tiếp cho team dev để bắt đầu coding.

Ví dụ tóm tắt (để tham chiếu cấu trúc, không cần lặp lại):
# Implementation Plan

- 1. Thiết lập cấu trúc dự án và cấu hình cơ bản  
  - Tạo cấu trúc thư mục cho frontend (React) và backend (Node.js)
  - Cấu hình TypeScript, ESLint, Prettier
  - Thiết lập database PostgreSQL và Redis
  - _Requirements: 7.1, 7.2_

- 2. Implement core data models và database schema  
  - Tạo migrations cho User, Post, ConnectedAccount, ScheduledJob
  - Implement interfaces TypeScript cho models
  - _Requirements: 1.1, 3.1_
'''
    
    messages = [{"role":"system", "content":system_prompt}] + [{"role":"user", "content": user_input}]
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
    )
    bot_reply = response.choices[0].message.content
            
    return bot_reply

input = '''# Requirements Document

## Introduction
Ứng dụng cải thiện bản thân được tích hợp các bài tập gym cơ bản và nâng cao nhằm hỗ trợ người dùng phát triển thể chất hiệu quả và an toàn. Ứng dụng cung cấp hướng dẫn chi tiết, dễ hiểu và phù hợp với nhiều trình độ tập luyện, giúp người dùng xây dựng thói quen tập luyện khoa học và bền vững hơn.        

## Requirements

### Requirement 1
**User Story:** Là một người dùng, tôi muốn truy cập danh sách các bài tập gym cơ bản và nâng cao để lựa chọn bài tập phù hợp với trình độ và mục tiêu của mình.

#### Acceptance Criteria
1. WHEN người dùng mở phần bài tập THEN hệ thống SHALL hiển thị danh sách các bài tập gym phân loại theo cơ bản và nâng cao.
2. WHEN người dùng chọn bài tập THEN hệ thống SHALL cung cấp mô tả chi tiết gồm hình ảnh, video và hướng dẫn thực hiện đúng kỹ thuật.
3. IF người dùng là người mới tập THEN hệ thống SHALL gợi ý các bài tập cơ bản phù hợp và an toàn.
4. WHEN người dùng muốn tìm hiểu thêm THEN hệ thống SHALL cung cấp liên kết tham khảo đến bài viết hướng dẫn chi tiết về các bài tập gym.

### Requirement 2
**User Story:** Là một người dùng, tôi muốn được hướng dẫn cách thực hiện đúng kỹ thuật các bài tập gym để tránh chấn thương và tối ưu hiệu quả luyện tập.

#### Acceptance Criteria
1. WHEN người dùng chọn bài tập THEN hệ thống SHALL cung cấp video hoặc hình ảnh minh họa kỹ thuật thực hiện.
2. WHEN người dùng xem hướng dẫn THEN hệ thống SHALL nhấn mạnh các điểm cần lưu ý để đảm bảo an toàn.
3. IF người dùng bỏ qua hướng dẫn kỹ thuật THEN hệ thống SHALL đưa ra cảnh báo khuyến cáo nên theo dõi kỹ trước khi tập.
4. WHEN người dùng hoàn thành bài tập THEN hệ thống SHALL ghi nhận và đề xuất bài tập kế tiếp phù hợp.

### Requirement 3
**User Story:** Là một người dùng, tôi muốn ứng dụng tổng hợp các bài tập gym từ nguồn đáng tin cậy để đảm bảo nội dung chính xác và có căn cứ khoa học. 

#### Acceptance Criteria
1. WHEN hệ thống cập nhật dữ liệu bài tập THEN SHALL lấy thông tin từ các nguồn uy tín như bài viết hướng dẫn trên Tiki.
2. WHEN người dùng yêu cầu chi tiết bài tập THEN hệ thống SHALL cung cấp nội dung tổng hợp từ các nguồn tham khảo đã được xác thực.
3. IF có cập nhật bài tập mới THEN hệ thống SHALL tự động thông báo để người dùng dễ dàng tiếp cận kiến thức mới.
4. WHEN người dùng truy cập phần tài liệu hỗ trợ THEN hệ thống SHALL dẫn liên kết trực tiếp tới nguồn tham khảo chính thức để nghiên cứu thêm.'''

def save_plan(architecture_id, plan_text):

    with SessionLocal() as db:
        #Lấy tất cả bản đang active
        active_items = (
            db.query(Plan)
            .filter(Plan.architecture_id == architecture_id, Plan.is_active == True)
            .all()
        )

        # Nếu có active bản cũ → tắt tất cả
        for item in active_items:
            item.is_active = False

        # Tìm version cao nhất hiện tại để tăng thêm 1
        latest = (
            db.query(Plan)
            .filter(Plan.architecture_id == architecture_id)
            .order_by(Plan.version.desc())
            .first()
        )
        new_version = 1 if latest is None else latest.version + 1

        # Tạo bản mới active duy nhất
        new_plan = Plan(
            architecture_id=architecture_id,
            plan_text=plan_text.strip(),
            version=new_version,
            is_active=True,
        )
        db.add(new_plan)
        db.commit()
        print(f"[SAVED Plan v{new_version}] Architecture {architecture_id}")

def main():
    if len(sys.argv) < 2:
        print("Sử dụng: python plan_agent.py <section_id>")
        sys.exit(1)

    section_id_arg = sys.argv[1]
    try:
        section_uuid = uuid.UUID(section_id_arg)
    except ValueError:
        print("section_id không hợp lệ (phải là UUID).")
        sys.exit(1)

    with SessionLocal() as db:
        # Tìm PRD đang active của section
        prd = (
            db.query(PRD)
            .filter(PRD.section_id == section_uuid, PRD.is_active == True)
            .first()
        )

        if not prd:
            print(f"Không tìm thấy PRD đang active cho section_id: {section_id_arg}")
            sys.exit(1)
        
        architecture = (
            db.query(Architecture)
            .filter(Architecture.prd_id == prd.prd_id, Architecture.is_active == True)
            .first()
        )

        print(f"Đang tạo Plan cho Architecture {architecture.architecture_id} (version {architecture.version})...\n")

        input = f'''
{prd.prd_text}
{architecture.architecture_text}
'''
        # Gọi AI để sinh Design Document
        plan_doc = plan_chatbot(input)

        # In ra console
        print("\n=======================[ Plan ]=======================\n")
        print(plan_doc)
        print("\n=================================================================\n")

        # Lưu vào DB
        save_plan(architecture.architecture_id, plan_doc)


if __name__ == "__main__":
    main()