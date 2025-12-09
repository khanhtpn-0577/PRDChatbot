// src/components/chat/ChatWindow.js

export function renderChatWindow(container, messages, loading) {
  container.innerHTML = messages
    .map((msg) => {
      const alignment = msg.role === "user" ? "justify-end" : "justify-start";
      const bubbleColor =
        msg.role === "user"
          ? "bg-blue-600 text-white"
          : "bg-gray-200 text-gray-800";

      return `
        <div class="flex ${alignment}">
          <div class="px-4 py-2 rounded-lg max-w-[70%] ${bubbleColor}">
            ${msg.content}
          </div>
        </div>
      `;
    })
    .join("");

  // Loading indicator
  if (loading) {
    container.innerHTML += `
      <div class="flex justify-start">
        <div class="px-4 py-2 rounded-lg bg-gray-300 text-gray-700 animate-pulse">
          ...
        </div>
      </div>
    `;
  }

  container.scrollTop = container.scrollHeight;
}
