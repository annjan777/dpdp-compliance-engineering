let nextId = 1;
const users = new Map(), notes = new Map(), sessions = new Map(), consents = [], processingLog = [];

function createUser(email, passwordHash) {
  const user = { id: nextId++, email, passwordHash };
  users.set(user.id, user);
  return user;
}

function recordConsent(userId, purpose, granted, noticeVersion) {
  consents.push({ userId, purpose, granted, noticeVersion, at: new Date().toISOString() });
}

function eraseUser(userId) {
  for (const [id, n] of notes) if (n.ownerId === userId) notes.delete(id);
  for (const [token, s] of sessions) if (s.userId === userId) sessions.delete(token);
  consents.push({ userId, purpose: "product-updates", granted: false, noticeVersion: "erasure", at: new Date().toISOString() });
  users.delete(userId);
  processingLog.push({ userId, action: "erase", at: new Date().toISOString() });
}

module.exports = { users, notes, sessions, consents, processingLog, createUser, recordConsent, eraseUser };
