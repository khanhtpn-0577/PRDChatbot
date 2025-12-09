// src/components/chat/ChatInputForm.js

export function setupChatInput(onSend) {
  const input = document.getElementById("chat-input");
  const sendBtn = document.getElementById("chat-send");

  // Gửi khi nhấn nút Send
  sendBtn.addEventListener("click", () => {
    const text = input.value.trim();
    if (!text) return;
    onSend(text);
    input.value = "";
  });

  // Gửi khi nhấn Enter
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;
      onSend(text);
      input.value = "";
    }
  });
}
