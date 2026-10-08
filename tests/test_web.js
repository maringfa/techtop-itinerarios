// Verifica el comportamiento de páginas y filtros; no sustituye una prueba visual en navegador.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.textContent = ""; this.classList = {add() {}}; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; }
  setAttribute() {}
}
const elements = new Map();
const document = {
  getElementById(id) { if (!elements.has(id)) elements.set(id, new Element("div")); return elements.get(id); },
  createElement(tag) { return new Element(tag); }
};
class Clock extends Date {
  constructor(...args) { super(...(args.length ? args : ["2026-10-08T18:00:00Z"])); }
}
const imports = [];
for (let i = 0; i < 26; i++) {
  const day = i < 7 ? "2026-10-08" : i < 14 ? "2026-10-09" : "2026-10-10";
  imports.push({displayDate: day, dateType: "ETA", plant: null, container: "C" + i, hbl: "FICTICIO", items: "Plywood"});
}
imports.unshift({...imports[0], container: "PASADO", displayDate: "2026-10-07"});
imports.push({...imports[0], container: "LEJANO", displayDate: "2026-12-01"});
const intervals = new Map();
const payload = {board: {imports, exports: [], demo: true, today: "2026-10-08"}, error: null,
  lastSuccessfulRead: "2026-10-08T18:00:00Z"};
const context = vm.createContext({document, Date: Clock, Intl,
  fetch: async () => ({ok: true, json: async () => payload}),
  setInterval(callback, interval) { intervals.set(interval, callback); }});
vm.runInContext(fs.readFileSync(path.join(__dirname, "../web/app.js"), "utf8"), context);

setImmediate(() => {
  assert.equal(elements.get("importCount").textContent, "20 próximas · página 1/2");
  assert.equal(elements.get("importRows").children.length, 10);
  assert.equal(elements.get("importRows").children[0].children[1].children[1].textContent, "C0");
  intervals.get(16000)();
  assert.equal(elements.get("importCount").textContent, "20 próximas · página 2/2");
  assert.equal(elements.get("importRows").children.length, 10);
  assert.equal(elements.get("importRows").children[0].children[1].children[1].textContent, "C10");
  intervals.get(16000)();
  assert.equal(elements.get("importCount").textContent, "20 próximas · página 1/2");
  console.log("Paginación web correcta: 20 importaciones, dos páginas de diez, sin tercera página por grupos de fecha.");
});
