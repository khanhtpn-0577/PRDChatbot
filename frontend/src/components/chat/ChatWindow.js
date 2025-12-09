// src/components/chat/ChatWindow.js

// ----------------------
// Render bảng PRD
// ----------------------
function renderPRDTable(features) {
  const rows = features
    .map(
      (f) => `
      <tr class="border-b">
        <td class="p-2 font-semibold">${f.title}</td>
        <td class="p-2">${f.user_story}</td>
        <td class="p-2">${f.business_value}</td>
        <td class="p-2 font-bold">${f.priority_moscow}</td>
      </tr>`
    )
    .join("");

  return `
    <div class="bg-white border rounded-lg shadow p-4 overflow-x-auto my-2 max-w-[90%]">
      <table class="min-w-full border-collapse text-left text-sm">
        <thead>
          <tr class="border-b bg-gray-100">
            <th class="p-2 font-bold">Title</th>
            <th class="p-2 font-bold">User Story</th>
            <th class="p-2 font-bold">Business Value</th>
            <th class="p-2 font-bold">Priority</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

// ----------------------
// Render toàn bộ cửa sổ chat
// ----------------------
export function renderChatWindow(container, messages, loading) {
  container.innerHTML = messages
    .map((msg) => {
      const alignment = msg.role === "user" ? "justify-end" : "justify-start";
      const bubbleColor =
        msg.role === "user"
          ? "bg-blue-600 text-white"
          : "bg-gray-200 text-gray-800";

      // Nếu là bảng PRD
      if (msg.type === "table") {
        return `
          <div class="flex ${alignment} my-2">
            ${renderPRDTable(msg.content)}
          </div>
        `;
      }

      // Nếu là tin nhắn bình thường
      return `
        <div class="flex ${alignment} my-2">
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
      <div class="flex justify-start my-2">
        <div class="px-4 py-2 rounded-lg bg-gray-300 text-gray-700 animate-pulse">
          ...
        </div>
      </div>
    `;
  }

  // Auto scroll
  container.scrollTop = container.scrollHeight;
}
