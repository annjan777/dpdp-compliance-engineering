// Minimal Express API (fixture). Users keep notes; auth is a stubbed session.
const express = require("express");
const db = require("./db");

const app = express();
app.use(express.json());

// shortcut: header-based fake session for the fixture; real app uses cookie sessions
function requireAuth(req, res, next) {
  const uid = Number(req.header("x-user-id"));
  if (!uid || !db.users.has(uid)) return res.status(401).json({ error: "login required" });
  req.userId = uid;
  next();
}

app.get("/me", requireAuth, (req, res) => res.json(db.users.get(req.userId)));
app.get("/notes", requireAuth, (req, res) => res.json(db.notes.filter((n) => n.userId === req.userId)));
app.post("/notes", requireAuth, (req, res) => {
  const note = { id: db.notes.length + 1, userId: req.userId, text: String(req.body.text || "") };
  db.notes.push(note);
  res.status(201).json(note);
});

module.exports = app;
