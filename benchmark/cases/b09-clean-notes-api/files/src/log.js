// Structured JSON logger.
module.exports = { info: (event, fields) => process.stdout.write(JSON.stringify({ event, ...fields }) + "\n") };
