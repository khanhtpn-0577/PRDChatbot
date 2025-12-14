export function setupChatInput(onSend) {
  const container = document.getElementById("chat-input");
  if (!container) return;

  container.innerHTML = `
    <div class="flex items-end gap-2">
      <textarea
        id="chat-textarea"
        rows="1"
        placeholder="Nhập yêu cầu của bạn..."
        class="flex-1 resize-none rounded-xl border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      ></textarea>

      <button
        id="chat-send"
        class="h-9 px-4 rounded-xl bg-blue-600 text-white text-sm hover:bg-blue-700"
      >
        Send
      </button>
    </div>
  `;

  const textarea = container.querySelector("#chat-textarea");
  const sendBtn = container.querySelector("#chat-send");

  const send = () => {
    const text = textarea.value.trim();
    if (!text) return;
    textarea.value = "";
    onSend(text);
  };

  sendBtn.onclick = send;

  textarea.onkeydown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };
}
