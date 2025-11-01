import os
import sys
import uuid
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.db_models import PRD, Architecture, Base

# ================== CONFIG ==================
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

client = OpenAI(api_key=OPENAI_API_KEY)

def architecture_chatbot(user_input):
    system_prompt = '''Bạn là kiến trúc sư giải pháp (Solution Architect). 
Nhiệm vụ: chuyển Requirements Document đầu vào (theo mẫu) thành Design Document hoàn chỉnh, đúng định dạng mẫu sau (Overview + Architecture (Mermaid) + Components & Interfaces + Data Models + Error Handling + Testing Strategy).

0) Ràng buộc xuất bản
Ngôn ngữ: tiếng Việt, giọng formal, chính xác kỹ thuật.
Cấu trúc bắt buộc: Overview → Architecture (Mermaid) → Components & Interfaces → Data Models → Error Handling → Testing Strategy.
Không thêm/đổi tên mục ngoài các mục bắt buộc ở trên.
Overview là 1 đoạn văn (3–6 câu), không liệt kê.
Mermaid dùng graph TB với các subgraph theo thứ tự: Frontend Layer, API Gateway, Core Services, Data Layer, External APIs.
Interfaces/Data Models viết bằng TypeScript trong code block.
Tên service/model dùng PascalCase; method dùng camelCase; mọi method trả về Promise<>.

1) Cách diễn giải Requirements
Đọc Introduction để rút các mục tiêu, đối tượng người dùng, giá trị cốt lõi → đưa vào Overview (không liệt kê).
Với mỗi Requirement:
Trích User Story → suy ra một hoặc nhiều Core Services liên quan (VD: PostService/SchedulerService/SocialMediaService/AnalyticsService).
Chuyển Acceptance Criteria (WHEN/IF… THEN… SHALL …) thành:
các endpoint hoặc method trong service (gợi ý: CRUD, publish, schedule, search, report),
các ràng buộc dữ liệu/validation,
các luồng nghiệp vụ (gọi API ngoài, queue, retry),
các tình huống lỗi (rate limit, network, auth).
Nếu Requirements ám chỉ lên lịch, queue, cache, token:
dùng Redis cho queue/cache, SchedulerService cho hẹn giờ, refreshToken cho token lifecycle.
Nếu có tệp/ảnh/media: đưa File Storage (S3/Local) vào Data Layer.
Nếu Requirements đề cập phân tích/đo lường: thêm AnalyticsService, PostAnalytics model và endpoints tương ứng.
Giữ kiến trúc microservices và API Gateway (Express) làm mặc định trừ khi Requirements cấm.

2) Tạo Architecture (Mermaid)
Bắt buộc các subgraph:
Frontend Layer: nêu các UI chính (Dashboard, PWA, Editor/Calendar/Analytics nếu phù hợp).
API Gateway: Gateway[Express.js Gateway], Auth[Authentication Service].
Core Services: tạo các service khớp Requirements (ví dụ: PostService, SchedulerService, SocialService, AnalyticsService, NotificationService).
Data Layer: PostgreSQL, Redis, FileStorage.
External APIs: liệt kê theo nhu cầu (Facebook/Twitter/Instagram/LinkedIn/...); nếu không có MXH thì liệt kê API ngoài phù hợp (ví dụ: Payment, Email, Map).
Vẽ luồng mũi tên:
UI → Gateway; Gateway → Auth & các service; Service → Data/External APIs; Notification ↔ Redis; Scheduler ↔ Redis/PostgreSQL; PostService ↔ PostgreSQL/FileStorage; AnalyticsService ↔ PostgreSQL.

3) Viết Components & Interfaces

Frontend Components: với mỗi UI chính, viết 3 dòng: Purpose, Props, State.

Tối thiểu: Dashboard, Post Editor (nếu có nội dung), Calendar (nếu có lịch), Analytics Dashboard (nếu có phân tích).

Backend Services: cho mỗi service được suy ra từ Requirements, định nghĩa interface TypeScript với các method chính.

Ví dụ (điều chỉnh theo domain thực tế):

PostService: createPost, updatePost, deletePost, getPost, getUserPosts

SchedulerService: schedulePost, cancelScheduledPost, processScheduledJobs, getScheduledJobs

SocialMediaService: connectAccount, disconnectAccount, publish, getAccountInfo, refreshToken, searchUsers, formatUserTags

AnalyticsService: collectMetrics, getPostAnalytics, getUserAnalytics, generateReport

NotificationService: enqueue, send, markAsRead (tùy Requirements)

Tên method phải phản chiếu trực tiếp từ Acceptance Criteria.

4) Viết Data Models (TypeScript)

Bắt buộc có các model cốt lõi phù hợp domain. Với ứng dụng MXH, gợi ý:

User, Post, ConnectedAccount, ScheduledJob, PostAnalytics.

Field phải bám sát hành vi trong Acceptance Criteria (ví dụ: status, attempts, errorMessage, scheduledTime, platforms, token expiry…).

Dùng Date cho timestamp; rõ optional bằng ?.

5) Error Handling

Error Types: Auth, Rate Limiting, Network, Validation, Platform (hoặc domain-specific).

Strategies: Retry (exponential backoff), Circuit Breaker, Graceful Degradation, Error Logging, User Notification.

Chuẩn hóa ErrorResponse:

interface ErrorResponse {
  error: {
    code: string
    message: string
    details?: any
    timestamp: Date
    requestId: string
  }
}

6) Testing Strategy

Unit (Frontend/Backend/Services), Integration (API/DB/External), E2E (user journeys), Performance (Artillery/JMeter), Security scanning.

Test Data Management: fixtures, seeding, mocks, isolation, parallel.

CI: chạy toàn bộ tests, coverage tối thiểu 80%, quality gates.

7) Quy tắc trình bày cuối

Giữ nguyên tiêu đề các mục như mẫu.

Không giải thích ngoài tài liệu; chỉ in Design Document.

Nếu Requirements không đề cập một mảng nào đó, giữ khung chung nhưng tinh gọn nội dung cho hợp lý (không bịa feature).

DỮ LIỆU ĐẦU VÀO (Requirements Document):

[ Dán đúng tài liệu Requirements theo mẫu mà người dùng cung cấp ]


DỮ LIỆU ĐẦU RA (bắt buộc, đúng format):

In ra nguyên văn một tài liệu “# Design Document” theo định dạng mẫu đã mô tả, gồm đầy đủ các phần: Overview, Architecture (Mermaid), Components and Interfaces, Data Models, Error Handling, Testing Strategy.

Không in phần giải thích nào khác ngoài Design Document.
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

def save_architecture(prd_id, architecture_text):

    with SessionLocal() as db:
        #Lấy tất cả bản đang active
        active_items = (
            db.query(Architecture)
            .filter(Architecture.prd_id == prd_id, Architecture.is_active == True)
            .all()
        )

        # Nếu có active bản cũ → tắt tất cả
        for item in active_items:
            item.is_active = False

        # Tìm version cao nhất hiện tại để tăng thêm 1
        latest = (
            db.query(Architecture)
            .filter(Architecture.prd_id == prd_id)
            .order_by(Architecture.version.desc())
            .first()
        )
        new_version = 1 if latest is None else latest.version + 1

        # Tạo bản mới active duy nhất
        new_architecture = Architecture(
            prd_id=prd_id,
            architecture_text=architecture_text.strip(),
            version=new_version,
            is_active=True,
        )
        db.add(new_architecture)
        db.commit()
        print(f"[SAVED Architecture v{new_version}] PRD {prd_id}")

def main():
    if len(sys.argv) < 2:
        print("Sử dụng: python generate_architecture.py <section_id>")
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

        print(f"Đang tạo Architecture cho PRD {prd.prd_id} (version {prd.version})...\n")

        # Gọi AI để sinh Design Document
        design_doc = architecture_chatbot(prd.prd_text)

        # In ra console
        print("\n=======================[ DESIGN DOCUMENT ]=======================\n")
        print(design_doc)
        print("\n=================================================================\n")

        # Lưu vào DB
        save_architecture(prd.prd_id, design_doc)


if __name__ == "__main__":
    main()