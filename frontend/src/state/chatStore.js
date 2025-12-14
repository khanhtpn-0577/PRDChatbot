// src/state/chatStore.js

/**
 * Chat store quản lý toàn bộ state của cuộc hội thoại.
 * Sử dụng pattern Observable đơn giản: UI có thể đăng ký lắng nghe thay đổi.
 */

class ChatStore {
  constructor() {
    // Lấy lại session_id nếu người dùng reload trang
    this.sectionId = sessionStorage.getItem("section_id") || null;
    this.messages = []; // [{ role: 'user' | 'bot', content: string }]
    this.loading = false;

    // Danh sách callback để UI subscribe
    this.listeners = [];
  }

  // ==== OBSERVER PATTERN ====

  /**
   * Đăng ký hàm lắng nghe state thay đổi
   * @param {Function} listener 
   */
  subscribe(listener) {
    this.listeners.push(listener);
  }

  /**
   * Gọi tất cả listener mỗi khi state thay đổi
   */
  notify() {
    this.listeners.forEach((listener) => listener(this.getState()));
  }

  // ==== STATE GETTERS ====

  getState() {
    return {
      sectionId: this.sectionId,
      messages: this.messages,
      loading: this.loading,
    };
  }

  // ==== SESSION MANAGEMENT ====

  /**
   * Lưu sectionId (UUID) khi backend trả về lần đầu tiên
   */
  setSectionId(id) {
    this.sectionId = id;
    sessionStorage.setItem("section_id", id);
    this.notify();
  }

  /**
   * Reset hoàn toàn session chat (phục vụ nút "New Chat")
   */
  clearSession() {
    this.sectionId = null;
    sessionStorage.removeItem("section_id");
    this.messages = [];
    this.loading = false;
    this.notify();
  }
  // ==== MUTATIONS ====

  addUserMessage(content) {
    this.messages.push({
      role: "user",
      content,
    });
    this.notify();
  }

  addBotMessage(content, type = "text") {
    this.messages.push({
      role: "bot",
      content,
      type, // "text" | "table"
    });
    this.notify();
  }


  setLoading(state) {
    this.loading = state;
    this.notify();
  }

  clearChat() {
    this.messages = [];
    this.loading = false;
    this.notify();
  }
}

// Singleton: chỉ tạo 1 instance duy nhất
export const chatStore = new ChatStore();
