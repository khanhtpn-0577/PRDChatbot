// src/state/chatStore.js

/**
 * Chat store quản lý toàn bộ state của cuộc hội thoại.
 * Sử dụng pattern Observable đơn giản: UI có thể đăng ký lắng nghe thay đổi.
 */

class ChatStore {
  constructor() {
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
      messages: this.messages,
      loading: this.loading,
    };
  }

  // ==== MUTATIONS ====

  addUserMessage(content) {
    this.messages.push({
      role: "user",
      content,
    });
    this.notify();
  }

  addBotMessage(content) {
    this.messages.push({
      role: "bot",
      content,
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
