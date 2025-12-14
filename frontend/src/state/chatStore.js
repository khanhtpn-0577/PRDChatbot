/**
 * Chat store quản lý toàn bộ state của cuộc hội thoại + document (SRS).
 * Sử dụng pattern Observable đơn giản.
 */

class ChatStore {
  constructor() {
    // ===== SESSION =====
    this.sectionId = sessionStorage.getItem("section_id") || null;

    // ===== CHAT STATE =====
    this.messages = []; // [{ role: 'user' | 'bot', content, type }]
    this.loading = false;

    // ===== DOCUMENT STATE (SRS) =====
    this.srsContent = ""; // nội dung SRS
    this.hasSRS = false;  // đã generate SRS hay chưa

    // ===== OBSERVERS =====
    this.listeners = [];
  }

  // =====================
  // OBSERVER PATTERN
  // =====================

  subscribe(listener) {
    this.listeners.push(listener);
  }

  notify() {
    this.listeners.forEach((listener) => listener(this.getState()));
  }

  // =====================
  // STATE GETTERS
  // =====================

  getState() {
    return {
      sectionId: this.sectionId,

      // chat
      messages: this.messages,
      loading: this.loading,

      // document
      srsContent: this.srsContent,
      hasSRS: this.hasSRS,
    };
  }

  // =====================
  // SESSION MANAGEMENT
  // =====================

  setSectionId(id) {
    this.sectionId = id;
    sessionStorage.setItem("section_id", id);
    this.notify();
  }

  clearSession() {
    this.sectionId = null;
    sessionStorage.removeItem("section_id");

    this.messages = [];
    this.loading = false;

    this.srsContent = "";
    this.hasSRS = false;

    this.notify();
  }

  // =====================
  // CHAT MUTATIONS
  // =====================

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
      type, // "text" | "table" | (sau này có thể thêm "system")
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

  // =====================
  // DOCUMENT (SRS) MUTATIONS
  // =====================

  /**
   * Set nội dung SRS sau khi gọi /api/generate_srs
   */
  setSRSContent(content) {
    this.srsContent = content || "";
    this.hasSRS = Boolean(content && content.length > 0);
    this.notify();
  }

  /**
   * Update SRS khi user chỉnh sửa trong canvas
   * (dùng cho live edit / autosave sau này)
   */
  updateSRSContent(content) {
    this.srsContent = content;
    this.hasSRS = true;
    this.notify();
  }

  /**
   * Reset document (dùng khi New Chat / New Document)
   */
  clearSRS() {
    this.srsContent = "";
    this.hasSRS = false;
    this.notify();
  }
}

// Singleton
export const chatStore = new ChatStore();
