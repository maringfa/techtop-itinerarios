sub init()
    m.top.functionName = "download"
end sub

sub download()
    url = m.top.url
    if url = "demo" then
        m.top.response = ReadAsciiFile("pkg:/assets/demo.json")
        return
    end if
    if Left(url, 8) <> "https://" then
        m.top.response = "{ " + Chr(34) + "error" + Chr(34) + ":" + Chr(34) + "connection" + Chr(34) + " }"
        return
    end if
    transfer = CreateObject("roUrlTransfer")
    transfer.SetUrl(url)
    transfer.SetCertificatesFile("common:/certs/ca-bundle.crt")
    transfer.EnablePeerVerification(true)
    transfer.EnableHostVerification(true)
    transfer.AddHeader("X-Roku-Reserved-Dev-Id", "")
    transfer.InitClientCertificates()
    port = CreateObject("roMessagePort")
    transfer.SetMessagePort(port)
    if transfer.AsyncGetToString() then
        event = wait(10000, port)
        if type(event) = "roUrlEvent" and event.GetResponseCode() = 200 then
            body = event.GetString()
            if Len(body) <= 1000000 then
                m.top.response = body
                return
            end if
        end if
        transfer.AsyncCancel()
    end if
    m.top.response = "{ " + Chr(34) + "error" + Chr(34) + ":" + Chr(34) + "connection" + Chr(34) + " }"
end sub
