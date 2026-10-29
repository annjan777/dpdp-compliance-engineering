// In-memory store with synthetic data only.
const users = new Map([
  [1, { id: 1, name: "Test User One", email: "one@example.test", phone: "0000000001" }],
  [2, { id: 2, name: "Test User Two", email: "two@example.test", phone: "0000000002" }],
]);
const notes = [
  { id: 1, userId: 1, text: "pick up groceries" },
  { id: 2, userId: 2, text: "call the bank" },
];
const loginEvents = [{ userId: 1, at: "2026-10-01T10:00:00Z", ip: "203.0.113.5" }];
module.exports = { users, notes, loginEvents };
