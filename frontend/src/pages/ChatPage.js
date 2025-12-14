// src/pages/ChatPage.js

import { chatStore } from "../state/chatStore.js";
import { sendMessageToBot } from "../lib/api.js";
import { renderChatWindow } from "../components/chat/ChatWindow.js";
import { setupChatInput } from "../components/chat/ChatInputForm.js";

export function setupChatPage() {
  const chatWindow = document.getElementById("chat-window");

  // Render UI khi state thay đổi
  chatStore.subscribe((state) => {
    renderChatWindow(chatWindow, state.messages, state.loading);
  });

  // Setup input form
  setupChatInput(async (text) => {
    chatStore.addUserMessage(text);

    chatStore.setLoading(true);
    const reply = await sendMessageToBot(text);
    chatStore.setLoading(false);

    if (reply.flag === "prd_related") {
      // reply.message là array JSON chứa các feature
      chatStore.addBotMessage(reply.message, "table");
    } else {
      chatStore.addBotMessage(reply.message, "text");
    }
  });

}
