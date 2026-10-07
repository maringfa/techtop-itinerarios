# TechTop · tablero de itinerarios (piloto local)

**Estado:** backend y pantalla web funcionales con XLSX ficticios; código de app Roku SceneGraph con demostración integrada y empaquetador ZIP. Falta validar el paquete en un televisor real y conectar los archivos reales dentro de TechTop. Ver [decisiones](docs/DECISIONES.md) y [instalación Roku](docs/ROKU_PILOTO.md).

Este repositorio se alojará inicialmente **privado en la cuenta personal del coordinador**, con acceso concedido a IT para revisión. Antes de usar datos operativos, IT definirá si se transfiere a una organización de TechTop y quién administra los permisos. `samples/` solo contiene ejemplos generados con `generar_ejemplos.py`; `.gitignore` excluye otros XLSX y la configuración local. Revisar `git status` antes de publicar cualquier cambio. Los itinerarios reales y las credenciales no pertenecen al repositorio.

El backend ofrece la vista de importaciones y exportaciones a navegadores locales y a la app Roku. Los dos archivos de `samples/` contienen **solo datos inventados**. El programa lee XLSX en el servidor; no abre archivos de OneDrive desde los televisores ni escribe en los Excel.

## Primera ejecución con datos ficticios

En una computadora con Python 3.11 o posterior:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe generar_ejemplos.py
.\.venv\Scripts\python.exe app.py
```

Abrir `http://127.0.0.1:8765/`. El modo de demostración usa `config.example.json`; muestra la etiqueta **PILOTO · DATOS FICTICIOS**. `generar_ejemplos.py` renueva las fechas ficticias cuando se repite la prueba en otro día.

## Prueba local con itinerarios de TechTop

1. IT crea un archivo `config.local.json` **fuera de la carpeta versionada del paquete**. Copia la estructura de `config.example.json`, cambia `demo` a `false` y reemplaza las dos rutas por las ubicaciones locales de los archivos que el servidor puede leer. No hace falta compartir esas rutas en ChatGPT.
2. Si los nombres de hoja o el número de fila de encabezados difieren, ajusta `sheet` y `headerRow` en ese archivo. Omite `headerRow` para detección dentro de las primeras 40 filas. Las fechas de texto se interpretan como mes/día/año (`MDY`); cambia a `DMY` si esa fuente usa día/mes/año. Las fechas reales de Excel conservan su fecha independientemente de ese ajuste.
3. En PowerShell, fija la ubicación de la configuración y ejecuta:

```powershell
$env:TECHTOP_BOARD_CONFIG = "C:\ruta-interna\config.local.json"
.\.venv\Scripts\python.exe app.py
```

**Importaciones:** cada fila con `Container` se interpreta como un contenedor. Se leen `Items`, `Status`, `HBL`, `ETA` y una nueva columna por contenedor llamada `ATP` (llegada a planta) (también acepta los encabezados anteriores `Llegada a planta`, `Llegada programada a planta` o `Arribo a planta`). El lector resuelve `Status`, `HBL` y `ETA` si están combinados entre varios contenedores. Las tarjetas muestran `HBL`, `Container`, `Items` y una sola fecha: si hay ATP, **«ATP · Llegada a planta»**; mientras ATP esté vacío, **«ETA · Arribo estimado al puerto»**. Al registrar ATP, ETA deja de mostrarse y la tarjeta se reordena por ATP. No se muestra un panel portuario separado. Sin columna de planta, la lectura informa el cambio pendiente.

La fecha elegida (ATP o, en su ausencia, ETA) debe ser hoy o futura. Un ATP pasado excluye el contenedor aunque ETA sea futuro; no se vuelve a ETA cuando ya hay ATP. `Arrived` se excluye en ambos casos. Sin ATP ni ETA, el contenedor no aparece.

**Exportaciones:** se leen `Origin`, `Reservation`, `Container`, `Transfer` y `Deliver at TTICR`. Las tarjetas muestran Reservation como HBL, Container, Origin como destino, Transfer y la fecha de salida de planta. Una salida aparece cuando tiene fecha y Transfer; Reservation y Container pueden quedar pendientes. No se muestra contenido de la carga.

Ambas listas incluyen el día actual y fechas futuras, ordenadas de la más cercana a la más lejana según el calendario de Costa Rica. Las pantallas web y Roku también descartan fechas pasadas cuando cambia el día, incluso si una lectura fallida obliga a conservar datos anteriores. Se conserva la fecha y hora de la última lectura exitosa.

La lectura se repite cada `refreshSeconds` (60 por defecto). Si falla un archivo, mantiene **ambos conjuntos de la última lectura válida** y muestra una advertencia. `/health` devuelve estado de lectura sin datos del itinerario; `/api/board` sí devuelve HBL, contenedores y Transfer a los navegadores autorizados.

## Despliegue en los televisores

Esta versión escucha **solo en loopback** y rechaza configuraciones que intenten exponerla a la red: sirve para verificar el funcionamiento en el equipo del servidor. Roku OS no abre la pantalla web como navegador general; la app en `roku/` dibuja la información mediante SceneGraph. Se genera el paquete con `python scripts/build_roku.py` y se instala como piloto en cada TV, siguiendo `docs/ROKU_PILOTO.md`. IT debe incorporar autorización, HTTPS, segmentación de red y un proceso supervisado antes de conectar los Roku al backend real. No se debe exponer `/api/board` a Internet ni abrir el puerto directamente a toda la red.

Consultar [revisión para IT](docs/REVISION_IT.md) antes de conectar archivos reales o distribuir la app Roku.

La carpeta compartida de OneDrive puede estar sincronizada en una máquina de prueba, pero la sincronización no queda verificada por este paquete. Para operación permanente sin depender de la sesión de OneDrive, IT debe confirmar si la carpeta pertenece a SharePoint o al OneDrive de una cuenta y provisionar una lectura mediante Microsoft Graph con permisos de solo lectura limitados al recurso. Ese adaptador requiere identificadores y permisos del tenant; **no está implementado en este piloto**. El lector XLSX y la pantalla se reutilizan cuando se agregue.

## Datos y diagnóstico

- El archivo de configuración con rutas reales no forma parte del ZIP de desarrollo. No guardar credenciales ni rutas reales en HTML, JavaScript o repositorios compartidos.
- Los errores mostrados y `/health` no incluyen rutas, valores de celdas ni trazas. Los televisores sí muestran los datos operativos aprobados.
- Si una prueba local falla, compartir solo el mensaje genérico y los encabezados o una **copia verdaderamente anonimizada** que conserve celdas combinadas y formatos. Una copia idéntica con otro nombre conserva toda la información confidencial.
- El piloto no se ha probado contra archivos reales ni en el servidor de TechTop. IT debe verificar el acceso, la frescura de OneDrive/Graph, permisos y el comportamiento en los televisores antes de usarlo en operaciones.
