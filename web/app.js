(function () {
  "use strict";
  const $ = id => document.getElementById(id);
  const zone = "America/Costa_Rica";
  const dayFmt = new Intl.DateTimeFormat("es-CR", {timeZone:"UTC",weekday:"long",day:"numeric",month:"short"});
  const shortFmt = new Intl.DateTimeFormat("es-CR", {timeZone:"UTC",day:"numeric",month:"short"});
  const stampFmt = new Intl.DateTimeFormat("es-CR", {timeZone:zone,day:"numeric",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit",hour12:false});
  let board = null, page = 0, error = null, lastSuccessfulRead = null;
  const strip = s => s.replace(/\./g, "");
  const date = iso => new Date(iso + "T12:00:00Z");
  const short = iso => strip(shortFmt.format(date(iso))).toUpperCase();
  function relative(iso) {
    const n = Math.round((date(iso) - date(board.today)) / 86400000);
    if (n === 0) return "HOY";
    if (n === 1) return "MAÑANA";
    if (n === -1) return "AYER";
    return strip(dayFmt.format(date(iso)).split(",")[0]).toUpperCase();
  }
  function node(tag, cls, value) {
    const x = document.createElement(tag);
    if (cls) x.className = cls;
    if (value !== undefined) x.textContent = String(value);
    return x;
  }
  function row(iso, title, description, detail, isExport) {
    const item = node("article", "row");
    const when = node("div", "datebox");
    when.append(node("strong", "relative", relative(iso)), node("span", "date", short(iso)));
    const body = node("div", "rowbody");
    body.append(node("strong", "", title), node("span", "", description));
    if (detail) body.append(node("small", "", detail));
    item.append(when, body);
    return item;
  }
  function pagesByDate(items, key, size) {
    const pages = []; let current = [], i = 0;
    while (i < items.length) {
      const same = []; const day = items[i][key];
      while (i < items.length && items[i][key] === day) same.push(items[i++]);
      if (same.length <= size && current.length && current.length + same.length > size) {
        pages.push(current); current = [];
      }
      while (same.length) {
        current.push(...same.splice(0, size - current.length));
        if (current.length === size) { pages.push(current); current = []; }
      }
    }
    if (current.length) pages.push(current);
    return pages.length ? pages : [[]];
  }
  function render() {
    const alert = $("readError");
    alert.hidden = !error;
    if (error) alert.textContent = board ? "La lectura más reciente falló. Se muestran los últimos datos válidos." : "Esperando lectura de los itinerarios.";
    if (!board) return;
    $("headerDate").textContent = strip(dayFmt.format(date(board.today)));
    $("modeBadge").textContent = board.demo ? "PILOTO · DATOS FICTICIOS" : "ITINERARIO INTERNO";
    $("lastUpdated").textContent = "Última actualización: " + (lastSuccessfulRead ? strip(stampFmt.format(new Date(lastSuccessfulRead))) : "pendiente");
    const imports = pagesByDate(board.imports, "plant", 10);
    const exports = pagesByDate(board.exports, "departure", 5);
    const inPage = imports[page % imports.length], outPage = exports[page % exports.length];
    $("screen").className = inPage.length >= 6 ? "screen high-volume" : "screen";
    $("importRows").replaceChildren(); $("exportRows").replaceChildren();
    inPage.forEach(x => {
      const card = row(x.plant, (inPage.length >= 6 ? "" : "Contenedor ") + x.container, x.items + " · " + x.hbl, "");
      card.setAttribute("aria-label", "Contenedor " + x.container + ", " + x.items + ", " + x.hbl);
      $("importRows").append(card);
    });
    outPage.forEach(x => {
      const container = /^[A-Z]{4}[0-9]{7}$/.test(x.container.trim()) ? "Contenedor " + x.container : (x.container || "Contenedor pendiente");
      $("exportRows").append(row(x.departure, "Transfer " + x.transfer,
        "Destino " + x.origin + " · " + (x.reservation || "HBL pendiente"), container));
    });
    if (!board.imports.length) $("importRows").append(node("div", "empty", "Sin llegadas a planta programadas"));
    if (!board.exports.length) $("exportRows").append(node("div", "empty", "Sin salidas con fecha y Transfer"));
    $("importCount").textContent = board.imports.length + (board.imports.length === 1 ? " próxima" : " próximas") + (imports.length > 1 ? " · página " + (page % imports.length + 1) + "/" + imports.length : "");
    $("exportCount").textContent = board.exports.length + (board.exports.length === 1 ? " próxima" : " próximas") + (exports.length > 1 ? " · página " + (page % exports.length + 1) + "/" + exports.length : "");
    const notice = $("portNotice"); notice.replaceChildren();
    notice.className = "notice" + (board.port.watchCount ? "" : " quiet");
    notice.append(node("strong", "", board.port.eta ? "ETA AL PUERTO · " + short(board.port.eta) : "SEGUIMIENTO DE PUERTO"),
      node("span", "", board.port.eta ? "Rastrear y preparar DUA · " + board.port.unscheduledCount + " contenedores sin fecha de planta"
        : (board.port.unscheduledCount ? board.port.unscheduledCount + " contenedores sin fecha de planta" : "No hay contenedores pendientes de programar")));
  }
  async function refresh() {
    try {
      const response = await fetch("/api/board", {cache:"no-store"});
      if (!response.ok) throw new Error("Respuesta del servidor");
      const payload = await response.json();
      if (payload.board) board = payload.board;
      error = payload.error;
      lastSuccessfulRead = payload.lastSuccessfulRead;
    } catch (_) { error = "Sin conexión con el servidor"; }
    render();
  }
  refresh();
  setInterval(refresh, 30000);
  setInterval(() => {
    if (board && (board.imports.length > 10 || board.exports.length > 5)) { page++; render(); }
  }, 16000);
}());
