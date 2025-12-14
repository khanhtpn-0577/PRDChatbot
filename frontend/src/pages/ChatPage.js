// src/pages/ChatPage.js
import { chatStore } from "../state/chatStore.js";
import { sendMessageToBot, sendMessageToGenerateSRS } from "../lib/api.js";
import { setupChatInput } from "../components/chat/ChatInputForm.js";
import { renderAppLayout } from "../components/layout/AppLayout.js";

export function setupChatPage() {
  const appRoot = document.getElementById("app");

  const bindInput = () => {
    setupChatInput(async (text) => {
      const state = chatStore.getState();

      chatStore.addUserMessage(text);
      chatStore.setLoading(true);

      try {
        const isFirstPrompt = !state.sectionId || !state.hasSRS;

        if (isFirstPrompt) {
          const { chatResponse, srsContent } =
            await sendMessageToGenerateSRS(text);

          chatStore.addBotMessage(chatResponse);
          chatStore.setSRSContent(srsContent);
        } else {
          const reply = await sendMessageToBot(text);
          chatStore.addBotMessage(
            reply.message,
            reply.flag === "prd_related" ? "table" : "text"
          );
        }
      } catch (err) {
        console.error("[Chat Error]", err);
        chatStore.addBotMessage("Có lỗi xảy ra, vui lòng thử lại.");
      } finally {
        chatStore.setLoading(false);
      }
    });
  };

  // Render lần đầu + bind input
  renderAppLayout(appRoot, chatStore.getState());
  bindInput();

  // Re-render khi state đổi + bind input lại (vì DOM bị thay)
  chatStore.subscribe((state) => {
    renderAppLayout(appRoot, state);
    bindInput();
  });
}
