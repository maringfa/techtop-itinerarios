(function () {
  "use strict";
  const $ = id => document.getElementById(id);
  const zone = "America/Costa_Rica";
  const dayFmt = new Intl.DateTimeFormat("es-CR", {timeZone:"UTC",weekday:"long",day:"numeric",month:"short"});
  const shortFmt = new Intl.DateTimeFormat("es-CR", {timeZone:"UTC",day:"numeric",month:"short"});
  const stampFmt = new Intl.DateTimeFormat("es-CR", {timeZone:zone,day:"numeric",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit",hour12:false});
  const calendarFmt = new Intl.DateTimeFormat("en", {timeZone:zone,year:"numeric",month:"2-digit",day:"2-digit"});
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
  function row(iso, title, description, detail, dateLabel) {
    const item = node("article", "row");
    const when = node("div", "datebox");
    when.append(node("strong", "relative", relative(iso)), node("span", "date", short(iso)));
    const body = node("div", "rowbody");
    if (dateLabel) body.append(node("small", "milestone", dateLabel));
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
  function importPages(items) {
    const pages = [];
    for (let i = 0; i < items.length; i += 10) pages.push(items.slice(i, i + 10));
    return pages.length ? pages : [[]];
  }
  function pendingImportCount(today, shown) {
    const byDate = board.importsPendingByDate;
    const total = byDate && typeof byDate === "object" && !Array.isArray(byDate)
      ? Object.entries(byDate).reduce((sum, [day, count]) => sum +
          (day >= today && Number.isInteger(count) && count > 0 ? count : 0), 0)
      : board.imports.filter(x => (x.displayDate || x.plant) >= today).length;
    return Math.max(shown, total);
  }
  function render() {
    const alert = $("readError");
    alert.hidden = !error;
    if (error) alert.textContent = board ? "La lectura más reciente falló. Se muestran los últimos datos válidos." : "Esperando lectura de los itinerarios.";
    if (!board) return;
    const calendar = Object.fromEntries(calendarFmt.formatToParts(new Date()).map(x => [x.type, x.value]));
    board.today = calendar.year + "-" + calendar.month + "-" + calendar.day;
    const horizon = date(board.today);
    horizon.setUTCDate(horizon.getUTCDate() + 30);
    const windowEnd = horizon.toISOString().slice(0, 10);
    const upcomingImports = board.imports.map(x => ({...x, displayDate: x.displayDate || x.plant}))
      .filter(x => x.displayDate >= board.today && x.displayDate <= windowEnd).slice(0, 20);
    const upcomingExports = board.exports.filter(x => x.departure >= board.today);
    $("headerDate").textContent = strip(dayFmt.format(date(board.today)));
    $("modeBadge").textContent = board.demo ? "PILOTO · DATOS FICTICIOS" : "ITINERARIO INTERNO";
    $("lastUpdated").textContent = "Última actualización: " + (lastSuccessfulRead ? strip(stampFmt.format(new Date(lastSuccessfulRead))) : "pendiente");
    const imports = importPages(upcomingImports);
    const exports = pagesByDate(upcomingExports, "departure", 5);
    const inPage = imports[page % imports.length], outPage = exports[page % exports.length];
    $("screen").className = inPage.length >= 6 ? "screen high-volume" : "screen";
    $("importRows").replaceChildren(); $("exportRows").replaceChildren();
    inPage.forEach(x => {
      const estimated = x.dateType === "ETA";
      const dateLabel = estimated ? "ETA · Arribo estimado al puerto" : "ATP · Llegada a planta";
      const card = row(x.displayDate, (inPage.length >= 6 ? "" : "Contenedor ") + x.container,
        "HBL " + (x.hbl || "pendiente"), x.items, dateLabel);
      if (estimated) card.classList.add("port-estimate");
      card.setAttribute("aria-label", dateLabel + " " + x.displayDate + ", contenedor " + x.container + ", " + x.items + ", " + x.hbl);
      $("importRows").append(card);
    });
    outPage.forEach(x => {
      const container = /^[A-Z]{4}[0-9]{7}$/.test(x.container.trim()) ? "Contenedor " + x.container : (x.container || "Contenedor pendiente");
      $("exportRows").append(row(x.departure, "Transfer " + x.transfer,
        "Destino " + x.origin + " · HBL " + (x.reservation || "pendiente"), container));
    });
    if (!upcomingImports.length) $("importRows").append(node("div", "empty", "Sin importaciones próximas con ATP o ETA"));
    if (!upcomingExports.length) $("exportRows").append(node("div", "empty", "Sin salidas con fecha y Transfer"));
    $("importCount").textContent = "Primeros " + upcomingImports.length + " de " +
      pendingImportCount(board.today, upcomingImports.length) + " pendientes · página " +
      (page % imports.length + 1) + "/" + imports.length;
    $("exportCount").textContent = upcomingExports.length + (upcomingExports.length === 1 ? " próxima" : " próximas") + (exports.length > 1 ? " · página " + (page % exports.length + 1) + "/" + exports.length : "");
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
