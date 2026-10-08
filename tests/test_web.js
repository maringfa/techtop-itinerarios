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
let currentTime = "2026-10-08T18:00:00Z";
class Clock extends Date {
  constructor(...args) { super(...(args.length ? args : [currentTime])); }
}
const imports = [];
for (let i = 0; i < 26; i++) {
  const day = i < 7 ? "2026-10-08" : i < 14 ? "2026-10-09" : "2026-10-10";
  imports.push({displayDate: day, dateType: "ETA", plant: null, container: "C" + i, hbl: "FICTICIO", items: "Plywood"});
}
imports.unshift({...imports[0], container: "PASADO", displayDate: "2026-10-07"});
imports.push({...imports[0], container: "LEJANO", displayDate: "2026-12-01"});
const intervals = new Map();
const payload = {board: {imports, exports: [], demo: true, today: "2026-10-08",
  importsPendingByDate: {"2026-10-08": 7, "2026-10-09": 7, "2026-10-10": 12, "2026-12-01": 14}}, error: null,
  lastSuccessfulRead: "2026-10-08T18:00:00Z"};
const context = vm.createContext({document, Date: Clock, Intl,
  fetch: async () => ({ok: true, json: async () => payload}),
  setInterval(callback, interval) { intervals.set(interval, callback); }});
vm.runInContext(fs.readFileSync(path.join(__dirname, "../web/app.js"), "utf8"), context);

setImmediate(async () => {
  assert.equal(elements.get("importCount").textContent, "Primeros 20 de 40 pendientes · página 1/2");
  assert.equal(elements.get("importRows").children.length, 10);
  assert.equal(elements.get("importRows").children[0].children[1].children[1].textContent, "C0");
  intervals.get(16000)();
  assert.equal(elements.get("importCount").textContent, "Primeros 20 de 40 pendientes · página 2/2");
  assert.equal(elements.get("importRows").children.length, 10);
  assert.equal(elements.get("importRows").children[0].children[1].children[1].textContent, "C10");
  intervals.get(16000)();
  assert.equal(elements.get("importCount").textContent, "Primeros 20 de 40 pendientes · página 1/2");
  payload.board.imports = payload.board.imports.filter(x => x.displayDate >= "2026-10-08").slice(0, 19);
  payload.board.importsPendingByDate = {"2026-10-08": 7, "2026-10-09": 7, "2026-10-10": 5, "2026-12-01": 21};
  await intervals.get(30000)();
  assert.equal(elements.get("importCount").textContent, "Primeros 19 de 40 pendientes · página 1/2");
  intervals.get(16000)();
  assert.equal(elements.get("importCount").textContent, "Primeros 19 de 40 pendientes · página 2/2");
  assert.equal(elements.get("importRows").children.length, 9);
  // El total descarta fechas pasadas incluso con una lectura retenida y más filas que tarjetas.
  currentTime = "2026-10-09T18:00:00Z";
  payload.error = "Lectura fallida";
  payload.board.importsPendingByDate["2026-10-08"] = 30;
  await intervals.get(30000)();
  assert.equal(elements.get("importCount").textContent, "Primeros 12 de 33 pendientes · página 2/2");
  payload.board.imports = [];
  payload.board.importsPendingByDate = {"2026-12-01": 40};
  await intervals.get(30000)();
  assert.equal(elements.get("importCount").textContent, "Primeros 0 de 40 pendientes · página 1/1");
  delete payload.board.importsPendingByDate;
  await intervals.get(30000)();
  assert.equal(elements.get("importCount").textContent, "Primeros 0 de 0 pendientes · página 1/1");
  console.log("Contador y paginación correctos: 20/40, 19/40, cero tarjetas y cambio de día con lectura retenida.");
});
