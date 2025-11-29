const conversations = new Map();

function ensureChat(sessionId, factory) {
  if (!conversations.has(sessionId)) {
    conversations.set(sessionId, factory());
  }
  return conversations.get(sessionId);
}

function getChat(sessionId) {
  return conversations.get(sessionId);
}

function resetChat(sessionId) {
  const chat = conversations.get(sessionId);
  if (chat) {
    chat.reset();
  }
}

function clear() {
  conversations.clear();
}

module.exports = {
  ensureChat,
  getChat,
  resetChat,
  clear,
};
