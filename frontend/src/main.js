// src/main.js
import { renderAppLayout } from "./components/layout/AppLayout.js";
import { setupChatPage } from "./pages/ChatPage.js";
import { chatStore } from "./state/chatStore.js";

const appRoot = document.getElementById("app");

// render lần đầu
renderAppLayout(appRoot, chatStore.getState());

// setup logic chat
setupChatPage();
