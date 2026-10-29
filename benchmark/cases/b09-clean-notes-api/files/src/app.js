const express = require("express");
const bcrypt = require("bcrypt");
const db = require("./db");
const log = require("./log");

const app = express();
app.use(express.json());

function requireAuth(req, res, next) {
  const s = db.sessions.get(req.header("authorization"));
  if (!s) return res.status(401).end();
  req.userId = s.userId;
  next();
}

app.post("/signup", async (req, res) => {
  const hash = await bcrypt.hash(String(req.body.password), 12);
  const user = db.createUser(req.body.email, hash);
  db.recordConsent(user.id, "product-updates", req.body.productUpdates === true, "notice-v3");
  log.info("signup", { userId: user.id });
  res.status(201).json({ id: user.id });
});

app.get("/notes/:id", requireAuth, (req, res) => {
  const note = db.notes.get(Number(req.params.id));
  if (!note || note.ownerId !== req.userId) return res.status(404).end();
  res.json(note);
});

app.delete("/account", requireAuth, (req, res) => {
  db.eraseUser(req.userId);
  log.info("erase", { userId: req.userId });
  res.status(204).end();
});

module.exports = app;
