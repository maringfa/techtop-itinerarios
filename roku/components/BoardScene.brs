sub init()
    m.top.SetFocus(true)
    m.rows = m.top.FindNode("rows")
    m.updated = m.top.FindNode("updated")
    m.notice = m.top.FindNode("notice")
    m.refreshTimer = m.top.FindNode("refreshTimer")
    m.pageTimer = m.top.FindNode("pageTimer")
    m.refreshTimer.ObserveField("fire", "fetchBoard")
    m.pageTimer.ObserveField("fire", "nextPage")
    m.page = 0
    m.pending = false
    m.board = invalid
    m.stale = false
    m.url = GetBoardUrl()
    if m.url = "" then
        m.notice.text = "SERVIDOR PENDIENTE · IT debe configurar la URL segura de /api/board"
    else
        fetchBoard()
    end if
    m.refreshTimer.control = "start"
    m.pageTimer.control = "start"
end sub

sub fetchBoard()
    if m.url = "" or m.pending = true then return
    m.pending = true
    m.fetchTask = CreateObject("roSGNode", "BoardFetch")
    m.fetchTask.url = m.url
    m.fetchTask.ObserveField("response", "onResponse")
    m.fetchTask.control = "run"
end sub

sub onResponse()
    m.pending = false
    raw = m.fetchTask.response
    data = invalid
    if raw <> "" then data = ParseJson(raw)
    if type(data) = "roAssociativeArray" and type(data.board) = "roAssociativeArray" then
        if type(data.board.imports) = "roArray" and type(data.board.exports) = "roArray" then
            m.board = data.board
            m.lastRead = data.lastSuccessfulReadLocal
            if m.lastRead = invalid then m.lastRead = data.lastSuccessfulRead
            m.stale = data.error <> invalid and data.error <> ""
            drawBoard()
            return
        end if
    end if
    m.stale = true
    if m.board = invalid then
        m.notice.text = "SIN CONEXIÓN · Verificar el servidor con IT"
    else
        drawBoard()
    end if
end sub

sub nextPage()
    if m.board = invalid then return
    m.page = m.page + 1
    drawBoard()
end sub

function safeText(value as Dynamic) as String
    if value = invalid then return ""
    if type(value) = "roString" or type(value) = "String" then return value
    return value.ToStr()
end function

function clipText(value as String, limit as Integer) as String
    if Len(value) <= limit then return value
    return Left(value, limit - 1) + "…"
end function

function addLabel(parent as Object, x as Integer, y as Integer, w as Integer, h as Integer, content as String, size as Integer, color as String)
    label = CreateObject("roSGNode", "Label")
    label.translation = [x, y]
    label.width = w
    label.height = h
    label.text = clipText(content, 100)
    label.color = color
    label.maxLines = 1
    font = CreateObject("roSGNode", "Font")
    font.uri = "font:MediumSystemFont"
    font.size = size
    label.font = font
    parent.AppendChild(label)
end function

sub addCard(x as Integer, y as Integer, w as Integer, h as Integer, heading as String, details as Object, accent as String)
    card = CreateObject("roSGNode", "Rectangle")
    card.translation = [x, y]
    card.width = w
    card.height = h
    card.color = "0x1D3B49FF"
    m.rows.AppendChild(card)
    stripe = CreateObject("roSGNode", "Rectangle")
    stripe.translation = [0, 0]
    stripe.width = 6
    stripe.height = h
    stripe.color = accent
    card.AppendChild(stripe)
    addLabel(card, 20, 3, w - 35, 34, heading, 27, "0xFFFFFFFF")
    for i = 0 to details.Count() - 1
        addLabel(card, 20, 36 + i * 27, w - 35, 26, details[i], 21, "0xB8CCD2FF")
    end for
end sub

function currentPlantDay() as String
    clock = CreateObject("roDateTime")
    ' Costa Rica usa UTC-6; no depende de la zona configurada en el televisor.
    clock.FromSeconds(clock.AsSeconds() - 21600)
    return Left(clock.ToISOString(), 10)
end function

function importWindowEnd() as String
    clock = CreateObject("roDateTime")
    clock.FromSeconds(clock.AsSeconds() - 21600 + 30 * 86400)
    return Left(clock.ToISOString(), 10)
end function

function upcoming(items as Object, dateKey as String, today as String) as Object
    result = []
    windowEnd = importWindowEnd()
    for each item in items
        day = safeText(item[dateKey])
        if dateKey = "displayDate" and day = "" then day = safeText(item.plant)
        if day <> "" and day >= today then
            if dateKey <> "displayDate" then
                result.Push(item)
            else if day <= windowEnd and result.Count() < 20 then
                result.Push(item)
            end if
        end if
    end for
    return result
end function

function pageCount(items as Object, size as Integer) as Integer
    if items.Count() = 0 then return 1
    return Int((items.Count() + size - 1) / size)
end function

function lastIndex(count as Integer, index as Integer) as Integer
    if count - 1 < index then return count - 1
    return index
end function

sub drawBoard()
    if m.board = invalid then return
    while m.rows.GetChildCount() > 0
        m.rows.RemoveChild(m.rows.GetChild(0))
    end while
    today = currentPlantDay()
    imports = upcoming(m.board.imports, "displayDate", today)
    exports = upcoming(m.board.exports, "departure", today)
    inPages = pageCount(imports, 10)
    outPages = pageCount(exports, 5)
    inPage = m.page mod inPages
    outPage = m.page mod outPages
    m.top.FindNode("importsTitle").text = "IMPORTACIONES · " + imports.Count().ToStr() + " PRÓXIMAS · " + (inPage + 1).ToStr() + "/" + inPages.ToStr()
    m.top.FindNode("exportsTitle").text = "EXPORTACIONES · " + exports.Count().ToStr() + " PRÓXIMAS · " + (outPage + 1).ToStr() + "/" + outPages.ToStr()
    for i = inPage * 10 to lastIndex(imports.Count(), inPage * 10 + 9)
        item = imports[i]
        day = safeText(item.displayDate)
        if day = "" then day = safeText(item.plant)
        dateLabel = "ATP " + day + " · Llegada a planta"
        accent = "0x5AD5C9FF"
        if safeText(item.dateType) = "ETA" then
            dateLabel = "ETA " + day + " · Arribo estimado al puerto"
            accent = "0xDDAE2CFF"
        end if
        heading = dateLabel + "   ·   " + safeText(item.container)
        details = ["HBL " + safeText(item.hbl) + "   ·   " + safeText(item.items)]
        addCard(60, 247 + (i mod 10) * 72, 1110, 65, heading, details, accent)
    end for
    for i = outPage * 5 to lastIndex(exports.Count(), outPage * 5 + 4)
        item = exports[i]
        heading = safeText(item.departure) + "   ·   TRANSFER " + safeText(item.transfer)
        container = safeText(item.container)
        if container = "" then container = "pendiente"
        reservation = safeText(item.reservation)
        if reservation = "" then reservation = "pendiente"
        details = ["Destino: " + safeText(item.origin), "Container: " + container, "HBL: " + reservation]
        addCard(1225, 250 + (i mod 5) * 141, 638, 126, heading, details, "0xFFA65DFF")
    end for
    if imports.Count() = 0 then addLabel(m.rows, 65, 280, 1000, 55, "Sin importaciones próximas con ATP o ETA", 28, "0xB8CCD2FF")
    if exports.Count() = 0 then addLabel(m.rows, 1230, 280, 610, 55, "Sin salidas con fecha y Transfer", 25, "0xB8CCD2FF")
    stamp = safeText(m.lastRead)
    if stamp = "" then stamp = "pendiente"
    m.updated.text = "Actualizado (CR): " + Left(stamp, 16)
    if m.stale then
        m.notice.text = "ATENCIÓN · Lectura fallida; se muestran los últimos datos válidos"
    else if m.board.demo = true then
        m.notice.text = "PILOTO · DATOS FICTICIOS · Configurar servidor para los datos reales"
    else
        m.notice.text = ""
    end if
end sub
