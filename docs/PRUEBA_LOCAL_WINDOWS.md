# Prueba del tablero en una laptop Windows

La prueba se ejecuta en el navegador de la laptop. Los Excel permanecen dentro de TechTop y se leen sin modificarlos. Requiere Python 3.11 o posterior; Visual Studio Code y Git no son necesarios. El servidor piloto escucha solo en `127.0.0.1`.

## 1. Comprobar Python

Abrir PowerShell desde Inicio y ejecutar:

```powershell
py --version
```

Si muestra Python 3.11 o posterior, continuar. Si no está instalado, descargar Python Install Manager desde [Python para Windows](https://www.python.org/downloads/windows/), instalarlo, cerrar y volver a abrir PowerShell. Ejecutar:

```powershell
pymanager install 3.13
py -3.13 --version
```

La versión 3.13 instalada puede seleccionarse al crear el entorno con `py -3.13 -m venv .venv`. Si la instalación está bloqueada por la empresa, solicitar a Aaron que habilite Python por el procedimiento interno.

## 2. Descargar el proyecto

Entrar a [GitHub](https://github.com/maringfa/techtop-itinerarios) con la cuenta que tiene acceso. Seleccionar **Code → Download ZIP** y extraer el ZIP.

Crear `TechTop` dentro de la carpeta de usuario de Windows, renombrar la carpeta extraída a `Proyecto` y colocarla dentro de `TechTop`. En el Explorador se puede abrir `%USERPROFILE%` para encontrar la carpeta de usuario.

La carpeta `%USERPROFILE%\TechTop\Proyecto` debe contener directamente `app.py`, `requirements.txt` y `config.example.json`.

## 3. Instalar las dependencias

En PowerShell:

```powershell
Set-Location "$env:USERPROFILE\TechTop\Proyecto"
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Si se instaló 3.13 junto a otra versión predeterminada, usar `py -3.13 -m venv .venv` en el segundo comando. No hace falta activar el entorno ni cambiar la política de ejecución de PowerShell. `tzdata` se instala en Windows para resolver la zona `America/Costa_Rica`.

## 4. Verificar el programa con ejemplos

```powershell
Remove-Item Env:TECHTOP_BOARD_CONFIG -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe generar_ejemplos.py
.\.venv\Scripts\python.exe app.py
```

Abrir `http://127.0.0.1:8765/`. Debe mostrar **PILOTO · DATOS FICTICIOS**. Dejar PowerShell abierto mientras se usa el tablero. Al comprobarlo, volver a PowerShell y pulsar `Ctrl+C` para detenerlo.

## 5. Preparar los dos Excel reales

Los archivos deben estar disponibles como `.xlsx` locales. Si están en OneDrive/SharePoint, abrirlos desde su carpeta sincronizada en el Explorador; una URL de la página web no es una ruta local válida para este lector.

En cada archivo, seleccionar **Mantener siempre en este dispositivo** y esperar a que termine la descarga/sincronización. Confirmar que las últimas modificaciones ya aparecen en la copia local.

| Archivo | Encabezados requeridos |
| --- | --- |
| Importaciones | `Items`, `Status`, `HBL`, `Container`, `ETA`, `ATP` |
| Exportaciones | `Origin`, `Reservation`, `Container`, `Transfer`, `Deliver at TTICR` |

ATP puede estar vacío por contenedor; su encabezado debe existir. Guardar las modificaciones en Excel para que la lectura del disco pueda detectarlas. El lector conserva el manejo de celdas combinadas del itinerario.

## 6. Crear la configuración local

En PowerShell, desde la carpeta `Proyecto`:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\TechTop\Configuracion" | Out-Null
Copy-Item .\config.example.json "$env:USERPROFILE\TechTop\Configuracion\config.local.json"
notepad "$env:USERPROFILE\TechTop\Configuracion\config.local.json"
```

Reemplazar el contenido por esta estructura y completar las rutas y pestañas reales:

```json
{
  "demo": false,
  "bind": "127.0.0.1",
  "port": 8765,
  "refreshSeconds": 60,
  "dateOrder": "MDY",
  "imports": {
    "path": "C:/RUTA_REAL/Importaciones.xlsx",
    "sheet": "NOMBRE_REAL_DE_LA_PESTANA_IMPORT",
    "headerRow": null
  },
  "exports": {
    "path": "C:/RUTA_REAL/Exportaciones.xlsx",
    "sheet": "*",
    "headerRow": null
  }
}
```

En importaciones, usar el nombre exacto de la pestaña interna del Excel, no el nombre del archivo. En exportaciones, `"sheet": "*"` lee todas las pestañas mensuales que tengan los encabezados del itinerario, sin cambiar la configuración cada mes. También incluye meses futuros y pestañas nuevas en la siguiente lectura. El filtro usa la fecha real de Deliver at TTICR: solo hoy y futuras, ordenadas por proximidad; el nombre del mes no determina qué aparece. Si importaciones también se divide por meses, se puede usar `*` allí.

`headerRow: null` detecta encabezados dentro de las primeras 40 filas de cada pestaña; si están más abajo, colocar el número de fila. Las portadas o resúmenes sin estructura de itinerario se omiten. Una hoja reconocible con encabezados incompletos provoca un error de lectura para poder corregirla. Si una hoja de resumen repite los mismos registros y encabezados, se leerá también; este modo no elimina duplicados automáticamente.

Para obtener cada ruta, usar **Copiar como ruta** en el Explorador. Quitar las comillas externas de la ruta copiada, cambiar `\` por `/` y pegarla dentro de las comillas JSON de `path`. Conservar las comillas y comas de la estructura.

`dateOrder` solo afecta fechas guardadas como texto: `MDY` para mes/día/año; `DMY` para día/mes/año. Las fechas reales de Excel se leen como fechas. Guardar en UTF-8; la versión 0.5.1 también admite UTF-8 con BOM. Verificar que el nombre siga siendo `config.local.json`, sin `.txt` al final.

## 7. Ejecutar con los Excel reales

```powershell
Set-Location "$env:USERPROFILE\TechTop\Proyecto"
$env:TECHTOP_BOARD_CONFIG = "$env:USERPROFILE\TechTop\Configuracion\config.local.json"
.\.venv\Scripts\python.exe app.py
```

Abrir `http://127.0.0.1:8765/`. La etiqueta debe decir **ITINERARIO INTERNO**. También se puede consultar `http://127.0.0.1:8765/health`; `healthy: true` indica que ambos itinerarios se leyeron correctamente, sin revelar registros.

## 8. Comprobar el resultado

- Comparar HBL, Container e Items de importaciones y HBL/Reservation, Container, Origin y Transfer de exportaciones contra los Excel.
- Sin ATP: mostrar **ETA · Arribo estimado al puerto**. Con ATP: mostrar **ATP · Llegada a planta** y usar ATP para filtrar y ordenar.
- Excluir fechas elegidas anteriores a hoy y contenedores con Status Arrived; sin ATP ni ETA, no aparece la importación.
- Exigir fecha Deliver at TTICR y Transfer para exportaciones; reserva y contenedor pueden estar pendientes.
- Revisar todas las páginas cuando haya más de diez importaciones o cinco exportaciones. Rotan cada 16 segundos.
- Comprobar la fecha y hora de la última lectura y un cambio guardado legítimo. La lectura ocurre cada 60 segundos y la pantalla consulta el resultado cada 30; dejar hasta 90 segundos después de que el cambio esté disponible localmente.

Para simular cambios, configurar dos copias locales de prueba guardadas dentro de la empresa. Los itinerarios reales y `config.local.json` permanecen fuera de GitHub.

## 9. Detener y volver a abrir

Detener con `Ctrl+C` en PowerShell. Para volver a ejecutar, repetir los tres comandos del paso 7. La variable de configuración se establece para esa sesión; el programa no se inicia automáticamente al encender la laptop.

## Errores frecuentes

| Mensaje o síntoma | Qué revisar |
| --- | --- |
| `py` no se reconoce | Completar la instalación de Python y volver a abrir PowerShell. |
| No se encuentra `app.py` o `requirements.txt` | Entrar a la carpeta que contiene esos archivos; puede haber una carpeta adicional dentro del ZIP. |
| `Falta agregar la columna ATP` | Agregar el encabezado ATP en el itinerario de importaciones y guardar. |
| `No se encontró un archivo de itinerario configurado` | Revisar `path`, extensión `.xlsx` y disponibilidad local de OneDrive. |
| `No se encontró la hoja configurada` | Copiar el nombre exacto de la pestaña del Excel. |
| `Faltan encabezados requeridos` | Revisar nombres y fila de encabezados, en la pestaña configurada. |
| `Fecha no reconocida` | Revisar la celda indicada y el orden MDY/DMY si es texto. |
| Error de JSON al iniciar | Revisar comillas, comas y barras de las rutas en `config.local.json`. |
| Sigue diciendo datos ficticios | Confirmar `demo: false` y la variable TECHTOP_BOARD_CONFIG del paso 7. |
| No aparecen tarjetas | Revisar que haya registros con fechas elegidas desde hoy y estados/Transfer elegibles; puede ser una agenda correctamente vacía. |
| Cambio guardado no aparece | Confirmar que OneDrive lo sincronizó localmente y esperar el ciclo de lectura/pantalla. |

Si se pide ayuda, compartir el mensaje de error sin valores del itinerario, rutas privadas ni capturas con datos reales. Esta prueba no habilita acceso desde los televisores; la publicación protegida y la prueba Roku se realizan después con IT.

Referencias: [Python en Windows](https://docs.python.org/3/using/windows.html), [zona horaria y tzdata](https://docs.python.org/3/library/zoneinfo.html), [archivos locales de OneDrive](https://support.microsoft.com/en-us/onedrive/save-disk-space-with-onedrive-files-on-demand-for-windows).
