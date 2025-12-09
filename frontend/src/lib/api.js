// src/lib/api.js

import { API_BASE_URL } from "./config.js";

/**
 * Gửi tin nhắn lên chatbot API của backend.
 * @param {string} message - Nội dung người dùng nhập.
 * @returns {Promise<{ content: string, raw: any }>} - Chuẩn hóa response để UI dễ render.
 */
export async function sendMessageToBot(message) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/generate_prd`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        query: message
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP Error ${response.status}`);
    }

    const data = await response.json();

    // Chuẩn hóa response (tuỳ backend)
    // Backend của anh thường trả { content: "...", ... }
    return {
      content: data?.content ?? "",
      raw: data
    };

  } catch (error) {
    console.error("API ERROR:", error);

    return {
      content: "Đã xảy ra lỗi khi gọi chatbot. Vui lòng thử lại.",
      error: true,
      raw: error
    };
  }
}
