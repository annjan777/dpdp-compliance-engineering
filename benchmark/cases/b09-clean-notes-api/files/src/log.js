// Structured logger: only ids and event names are ever passed in; values are never request bodies.
module.exports = { info: (event, fields) => process.stdout.write(JSON.stringify({ event, ...fields }) + "\n") };
