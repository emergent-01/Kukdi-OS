import axios from "axios";

const BASE = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const BACKEND = process.env.REACT_APP_BACKEND_URL;

const http = axios.create({ baseURL: BASE });

export const api = {
  // Home
  home: () => http.get("/home").then((r) => r.data),
  setState: (state) => http.post("/home/state", { state }).then((r) => r.data),
  brief: () => http.get("/home/brief").then((r) => r.data),
  refreshBrief: () => http.post("/home/brief/refresh").then((r) => r.data),
  reminders: () => http.get("/reminders").then((r) => r.data),
  dismissReminder: (id) => http.post("/reminders/dismiss", { id }).then((r) => r.data),
  snoozeReminder: (id) => http.post("/reminders/snooze", { id }).then((r) => r.data),

  // Conversation
  sendMessage: (text, conversation_id) =>
    http.post("/conversation/message", { text, conversation_id }).then((r) => r.data),
  messages: (conversation_id) =>
    http.get("/conversation/messages", { params: { conversation_id } }).then((r) => r.data),
  transcribe: (formData) =>
    http.post("/conversation/transcribe", formData, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data),

  // Memory
  memories: (params) => http.get("/memory", { params }).then((r) => r.data),
  createMemory: (body) => http.post("/memory", body).then((r) => r.data),
  updateMemory: (id, body) => http.patch(`/memory/${id}`, body).then((r) => r.data),
  confirmMemory: (id) => http.post(`/memory/${id}/confirm`).then((r) => r.data),
  archiveMemory: (id) => http.delete(`/memory/${id}`).then((r) => r.data),
  getMemory: (id) => http.get(`/memory/${id}`).then((r) => r.data),
  linkMemory: (id, body) => http.post(`/memory/${id}/link`, body).then((r) => r.data),
  unlinkMemory: (id, body) => http.post(`/memory/${id}/unlink`, body).then((r) => r.data),
  pendingCandidates: () => http.get("/memory/candidates/pending").then((r) => r.data),
  confirmCandidate: (id, body = {}) =>
    http.post(`/memory/candidates/${id}/confirm`, body).then((r) => r.data),
  dismissCandidate: (id) => http.post(`/memory/candidates/${id}/dismiss`).then((r) => r.data),

  // Dream Offer
  dreamOverview: () => http.get("/dream/overview").then((r) => r.data),
  createCompany: (body) => http.post("/dream/companies", body).then((r) => r.data),
  updateCompany: (id, body) => http.patch(`/dream/companies/${id}`, body).then((r) => r.data),
  deleteCompany: (id) => http.delete(`/dream/companies/${id}`).then((r) => r.data),
  createPrep: (body) => http.post("/dream/prep", body).then((r) => r.data),
  updatePrep: (id, body) => http.patch(`/dream/prep/${id}`, body).then((r) => r.data),
  deletePrep: (id) => http.delete(`/dream/prep/${id}`).then((r) => r.data),
  countdown: () => http.get("/dream/countdown").then((r) => r.data),
  generateCountdown: (body = {}) => http.post("/dream/countdown/generate", body).then((r) => r.data),
  toggleCountdownTask: (taskId, done) =>
    http.patch(`/dream/countdown/task/${taskId}`, { done }).then((r) => r.data),

  // People
  people: () => http.get("/people").then((r) => r.data),
  createPerson: (body) => http.post("/people", body).then((r) => r.data),
  updatePerson: (id, body) => http.patch(`/people/${id}`, body).then((r) => r.data),
  deletePerson: (id) => http.delete(`/people/${id}`).then((r) => r.data),

  // Calendar
  events: () => http.get("/calendar").then((r) => r.data),
  createEvent: (body) => http.post("/calendar", body).then((r) => r.data),
  updateEvent: (id, body) => http.patch(`/calendar/${id}`, body).then((r) => r.data),
  deleteEvent: (id) => http.delete(`/calendar/${id}`).then((r) => r.data),
  askCalendar: (question) => http.post("/calendar/ask", { question }).then((r) => r.data),

  // Reflection
  weeklyReflection: (refresh = false) =>
    http.get("/reflection/weekly", { params: { refresh } }).then((r) => r.data),

  // Story Bank
  stories: () => http.get("/stories").then((r) => r.data),
  createStory: (body) => http.post("/stories", body).then((r) => r.data),
  updateStory: (id, body) => http.patch(`/stories/${id}`, body).then((r) => r.data),
  polishStory: (id) => http.post(`/stories/${id}/polish`).then((r) => r.data),
  matchStories: (question) => http.post("/stories/match", { question }).then((r) => r.data),
  deleteStory: (id) => http.delete(`/stories/${id}`).then((r) => r.data),

  // Knowledge
  knowledge: (q) => http.get("/knowledge", { params: { q } }).then((r) => r.data),
  searchKnowledge: (question) => http.post("/knowledge/search", { question }).then((r) => r.data),
  createKnowledge: (body) => http.post("/knowledge", body).then((r) => r.data),
  uploadKnowledge: (formData) =>
    http.post("/knowledge/upload", formData, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data),
  deleteKnowledge: (id) => http.delete(`/knowledge/${id}`).then((r) => r.data),
};

export function formatTime(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  } catch {
    return "";
  }
}

export function formatDay(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

export function confidenceLabel(c) {
  if (c >= 0.85) return "High";
  if (c >= 0.6) return "Medium";
  return "Low";
}
