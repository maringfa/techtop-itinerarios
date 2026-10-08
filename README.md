# TechTop · tablero de itinerarios (piloto local)

**Versión: 0.7.0-pilot.** Backend y pantalla web funcionales; el coordinador reportó una prueba local satisfactoria con los Excel reales dentro de TechTop. Esta actualización se verificó con datos ficticios: veinte importaciones como máximo dentro de treinta días, dos páginas de diez y configuración portable de OneDrive. Falta probar esta actualización en Windows, en el servidor y en los televisores Roku. Ver [decisiones](docs/DECISIONES.md), [actualización en Windows](docs/ACTUALIZAR_WINDOWS.md) e [instalación Roku](docs/ROKU_PILOTO.md).

Este repositorio se alojará inicialmente **privado en la cuenta personal del coordinador**, con acceso concedido a IT para revisión. Antes de usar datos operativos, IT definirá si se transfiere a una organización de TechTop y quién administra los permisos. `samples/` solo contiene ejemplos generados con `generar_ejemplos.py`; `.gitignore` excluye otros XLSX y la configuración local. Revisar `git status` antes de publicar cualquier cambio. Los itinerarios reales y las credenciales no pertenecen al repositorio.

El backend ofrece la vista de importaciones y exportaciones a navegadores locales y a la app Roku. Los dos archivos de `samples/` contienen **solo datos inventados**. El programa lee XLSX en el servidor; no abre archivos de OneDrive desde los televisores ni escribe en los Excel.

## Primera ejecución con datos ficticios

Para la prueba en una laptop Windows, seguir la [guía paso a paso](docs/PRUEBA_LOCAL_WINDOWS.md). La instalación incluye `tzdata` en Windows para usar la fecha de Costa Rica; la configuración admite UTF-8 con o sin BOM.

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

La fecha elegida (ATP o, en su ausencia, ETA) debe estar entre hoy y hoy + 30 días, incluidos ambos extremos, según el calendario de Costa Rica. Se ordenan por esa fecha y, en empates, por Container; se muestran únicamente los veinte primeros. Web y Roku presentan diez por página y nunca más de dos páginas de importaciones. Una misma fecha puede quedar repartida entre páginas o parcialmente fuera del límite: el máximo de veinte es estricto. En cada lectura se recalcula toda la selección; al pasar una fecha, marcar Arrived o actualizar ATP, se incorporan los siguientes elegibles. No se borran filas de Excel. Un ATP pasado o fuera del horizonte excluye el contenedor aunque ETA sea elegible; no se vuelve a ETA cuando ya hay ATP. Sin ATP ni ETA, el contenedor no aparece.

**Exportaciones:** se leen `Origin`, `Reservation`, `Container`, `Transfer` y `Deliver at TTICR`. Las tarjetas muestran Reservation como HBL, Container, Origin como destino, Transfer y la fecha de salida de planta. Una salida aparece cuando tiene fecha y Transfer; Reservation y Container pueden quedar pendientes. No se muestra contenido de la carga.

Ambas listas incluyen el día actual y fechas futuras, ordenadas de la más cercana a la más lejana según el calendario de Costa Rica. Las pantallas web y Roku también descartan fechas pasadas cuando cambia el día, incluso si una lectura fallida obliga a conservar datos anteriores. Se conserva la fecha y hora de la última lectura exitosa.

El horizonte de treinta días y el máximo de veinte se aplican solo a importaciones. Exportaciones conserva su selección anterior de hoy y futuro, con cinco tarjetas por página. Si falla una lectura, la pantalla conserva la última selección válida: no puede incorporar los siguientes contenedores hasta que vuelva a leer ambos archivos correctamente.

La lectura se repite cada `refreshSeconds` (60 por defecto). Si falla un archivo, mantiene **ambos conjuntos de la última lectura válida** y muestra una advertencia. `/health` devuelve estado de lectura sin datos del itinerario; `/api/board` sí devuelve HBL, contenedores y Transfer a los navegadores autorizados.

**Itinerarios por mes:** usar `"sheet": "*"` para leer todas las pestañas del archivo que contengan la estructura del itinerario, incluidas las ocultas. `headerRow: null` detecta la fila de encabezados en cada pestaña. Se omiten portadas/resúmenes sin estructura de itinerario; una hoja reconocible con encabezados incompletos produce un error de lectura en vez de ocultar sus movimientos. La siguiente lectura descubre nuevas pestañas. Se combinan sus filas y se filtran/ordenan por las fechas reales de ATP/ETA o Deliver at TTICR, no por el nombre del mes. Este modo no elimina registros repetidos automáticamente: si una hoja de resumen copia el mismo itinerario con los mismos encabezados, también se leerá. Para leer una sola pestaña, usar su nombre exacto.

## Rutas adaptables de OneDrive

Para convertir una configuración local que ya funciona, ejecutar desde el proyecto:

```powershell
.\.venv\Scripts\python.exe scripts\configurar_onedrive.py --config "$env:USERPROFILE\TechTop\Configuracion\config.local.json"
```

El script detecta cuentas empresariales del usuario de ejecución, comprueba que las rutas existentes estén dentro de una misma carpeta base y lee ambos Excel antes de modificar la configuración. Conserva un primer respaldo `.bak` y realiza el reemplazo de forma atómica. No modifica los itinerarios, no muestra sus registros ni rutas y no incluye credenciales.

Cada origen convertido incorpora `"pathBase": "onedrive"` y una ruta interna, por ejemplo `"path": "Logistica/Importaciones.xlsx"` (nombre ilustrativo). Al iniciar, el programa vuelve a detectar la carpeta base y la combina con esa ruta interna; la configuración se puede llevar a otro usuario con la misma estructura de carpetas. Sin `pathBase`, las rutas absolutas y las relativas a la carpeta de configuración siguen funcionando como antes. No convertir `config.example.json`: sus datos ficticios son relativos al proyecto.

La detección usa `OneDriveCommercial` y las cuentas Business registradas en Windows para el usuario de ejecución. Solo acepta una raíz que contenga todos los archivos configurados como OneDrive. No busca archivos por nombre en el disco, no elige una cuenta personal ni adivina entre dos raíces válidas. IT puede indicar explícitamente la carpeta base con `TECHTOP_ONEDRIVE_ROOT` cuando la detección no sea suficiente o la biblioteca SharePoint se sincronice fuera de la raíz empresarial habitual. Consultar [actualización y traslado](docs/ACTUALIZAR_WINDOWS.md).

Comprobar una configuración sin modificarla:

```powershell
.\.venv\Scripts\python.exe scripts\configurar_onedrive.py --config "$env:USERPROFILE\TechTop\Configuracion\config.local.json" --check
```

La detección no inicia sesión ni instala/sincroniza OneDrive. La cuenta que ejecuta el programa debe tener acceso, sincronización activa y archivos disponibles localmente. La lectura correcta no prueba por sí sola que la copia sincronizada sea la más reciente. Las rutas internas también son información de la empresa: mantener configuración y respaldo fuera de GitHub.

## Despliegue en los televisores

Esta versión escucha **solo en loopback** y rechaza configuraciones que intenten exponerla a la red: sirve para verificar el funcionamiento en el equipo del servidor. Roku OS no abre la pantalla web como navegador general; la app en `roku/` dibuja la información mediante SceneGraph. Se genera el paquete con `python scripts/build_roku.py` y se instala como piloto en cada TV, siguiendo `docs/ROKU_PILOTO.md`. IT debe incorporar autorización, HTTPS, segmentación de red y un proceso supervisado antes de conectar los Roku al backend real. No se debe exponer `/api/board` a Internet ni abrir el puerto directamente a toda la red.

Consultar [revisión para IT](docs/REVISION_IT.md) antes de conectar archivos reales o distribuir la app Roku.

La carpeta compartida de OneDrive puede estar sincronizada en una máquina de prueba, pero la sincronización no queda verificada por este paquete. Para operación permanente sin depender de la sesión de OneDrive, IT debe confirmar si la carpeta pertenece a SharePoint o al OneDrive de una cuenta y provisionar una lectura mediante Microsoft Graph con permisos de solo lectura limitados al recurso. Ese adaptador requiere identificadores y permisos del tenant; **no está implementado en este piloto**. El lector XLSX y la pantalla se reutilizan cuando se agregue.

## Datos y diagnóstico

- El archivo de configuración con rutas reales no forma parte del ZIP de desarrollo. No guardar credenciales ni rutas reales en HTML, JavaScript o repositorios compartidos.
- Los errores mostrados y `/health` no incluyen rutas, valores de celdas ni trazas. Los televisores sí muestran los datos operativos aprobados.
- Si una prueba local falla, compartir solo el mensaje genérico y los encabezados o una **copia verdaderamente anonimizada** que conserve celdas combinadas y formatos. Una copia idéntica con otro nombre conserva toda la información confidencial.
- La prueba local previa con archivos reales fue reportada por el coordinador; esta actualización se probó con datos inventados en el entorno de desarrollo. IT debe verificar detección Windows, acceso, frescura de OneDrive/Graph, permisos y comportamiento en servidor y televisores antes de usarla en operaciones.

## Verificación de desarrollo

```text
python -m unittest discover -s tests -v
node tests/test_web.js
python scripts/build_roku.py
```

Node solo se utiliza para la prueba de paginación de desarrollo; no es necesario instalarlo para ejecutar el tablero. La prueba de JavaScript verifica lógica con un DOM simulado, no legibilidad en un navegador real. El empaquetado Roku tampoco sustituye una prueba en el televisor. La detección nativa de cuentas Windows debe comprobarse en el equipo destino; las pruebas automatizadas usan carpetas y cuentas simuladas.
