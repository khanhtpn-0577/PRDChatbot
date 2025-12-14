import { API_BASE_URL } from "./config.js";
import { chatStore } from "../state/chatStore.js";

export async function sendMessageToBot(message) {
  const payload = {
    query: message,
    section_id: chatStore.sectionId,
  };
  console.log("%c[FE → BE] Payload:", "color: blue; font-weight: bold;", payload);
  
  const res = await fetch(`${API_BASE_URL}/api/generate_prd`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json();

  // Lưu section_id FE
  if (!chatStore.sectionId && data.section_id) {
    chatStore.setSectionId(data.section_id);
  }

  // Chuẩn hóa output
  const reply = data.response; // BE trả {'flag':..., 'message':...}

  return {
    flag: reply.flag,
    message: reply.message,
  };
}

export async function sendMessageToGenerateSRS(query) {
  const payload = {
    query,
    section_id: chatStore.sectionId, // có thể null ở lần đầu
  };

  console.log(
    "%c[FE → BE] Generate SRS Payload:",
    "color: green; font-weight: bold;",
    payload
  );

  const res = await fetch(`${API_BASE_URL}/api/generate_srs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json();

  // 1. Lưu session_id
  if (!chatStore.sectionId && data.section_id) {
    chatStore.setSectionId(data.section_id);
  }

  // 2. Tách response
  const response = data.response || {};

  return {
    chatResponse: response.ping_pong_response || "",
    srsContent: response.srs || "",
  };
}