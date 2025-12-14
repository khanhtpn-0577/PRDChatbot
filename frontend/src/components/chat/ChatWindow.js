export function renderChatWindow(container, messages, loading) {
  container.innerHTML = messages
    .map((msg) => {
      const isUser = msg.role === "user";

      return `
        <div class="flex ${isUser ? "justify-end" : "justify-start"}">
          <div class="
            max-w-[75%]
            px-4 py-2
            rounded-2xl
            text-sm
            leading-relaxed
            ${
              isUser
                ? "bg-blue-600 text-white rounded-br-sm"
                : "bg-gray-200 text-gray-900 rounded-bl-sm"
            }
          ">
            ${msg.content}
          </div>
        </div>
      `;
    })
    .join("");

  if (loading) {
    container.innerHTML += `
      <div class="flex justify-start">
        <div class="px-4 py-2 rounded-2xl bg-gray-300 text-sm animate-pulse">
          Đang suy nghĩ...
        </div>
      </div>
    `;
  }

  container.scrollTop = container.scrollHeight;
}
