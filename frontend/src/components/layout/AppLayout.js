import { renderChatWindow } from "../chat/ChatWindow.js";
import { renderCanvasPanel } from "../canvas/CanvasPanel.js";

export function renderAppLayout(container, state) {
  container.innerHTML = `
    <div class="fixed inset-0 flex bg-gray-100">
        

      <!-- CHAT PANEL -->
      <div class="w-[40%] flex flex-col bg-white border-r">

        <!-- Header -->
        <div class="h-14 px-4 flex items-center border-b font-semibold">
          AI Chat
        </div>

        <!-- Messages -->
        <div id="chat-window" class="flex-1 overflow-y-auto p-4 space-y-4"></div>

        <!-- Input -->
        <div id="chat-input" class="border-t p-3 bg-white"></div>
      </div>

      <!-- CANVAS PANEL -->
      <div class="w-[60%] flex flex-col">

        <!-- Header -->
        <div class="h-14 px-6 flex items-center border-b bg-white font-semibold">
          Software Requirements Specification (SRS)
        </div>

        <!-- Content -->
        <div id="canvas-panel" class="flex-1 overflow-y-auto p-6 bg-gray-50"></div>
      </div>

    </div>
  `;

  renderChatWindow(
    container.querySelector("#chat-window"),
    state.messages,
    state.loading
  );

  renderCanvasPanel(
    container.querySelector("#canvas-panel"),
    state
  );
}
