# Actualizar a 0.7.0-pilot y trasladar la configuración

Esta guía parte de una laptop con el tablero ya instalado y una configuración real que funciona. No requiere Visual Studio Code, Git, cambios a los Excel ni reinstalar Python. Las dependencias de esta versión no cambiaron.

## 1. Detener y reemplazar el código

En la ventana PowerShell donde corre el tablero, pulsar `Ctrl+C`. Descargar el ZIP actualizado desde [el repositorio](https://github.com/maringfa/techtop-itinerarios) mediante **Code → Download ZIP** y extraerlo.

Copiar el contenido de la carpeta extraída dentro de `%USERPROFILE%\TechTop\Proyecto`, aceptando reemplazar archivos. `app.py`, `paths.py`, `VERSION`, `scripts`, `web` y `roku` deben quedar directamente dentro de `Proyecto`, sin una carpeta adicional intermedia. Conservar `.venv`. La configuración real está fuera, en `%USERPROFILE%\TechTop\Configuracion\config.local.json`; no reemplazarla por `config.example.json`.

Comprobar la versión:

```powershell
Set-Location "$env:USERPROFILE\TechTop\Proyecto"
Get-Content .\VERSION
```

Debe mostrar `0.7.0-pilot`.

## 2. Adaptar la configuración actual a OneDrive

Los dos Excel deben estar sincronizados bajo la misma carpeta base y con **Mantener siempre en este dispositivo**. Ejecutar desde `Proyecto`:

```powershell
.\.venv\Scripts\python.exe scripts\configurar_onedrive.py --config "$env:USERPROFILE\TechTop\Configuracion\config.local.json"
```

Si funciona, informa que adaptó la configuración y que leyó ambos Excel. El script convierte únicamente las rutas, conserva nombres de hoja, `headerRow`, `dateOrder`, modo real y ajustes del servidor. Agrega `"pathBase": "onedrive"` a cada origen y guarda la parte interna de la ruta, sin tu perfil Windows. No muestra las rutas ni los registros.

Antes de guardar verifica el acceso y los encabezados de ambos archivos. Si falla, deja la configuración intacta. Crea `config.local.json.bak` junto al original como primer respaldo y no lo reemplaza al repetir el comando. Los Excel se mantienen sin cambios. Configuración y respaldo son archivos privados de la empresa y permanecen fuera de GitHub.

Una estructura resultante ilustrativa (no copiar estas rutas sobre las reales) sería:

```json
{
  "demo": false,
  "bind": "127.0.0.1",
  "port": 8765,
  "refreshSeconds": 60,
  "dateOrder": "MDY",
  "imports": {
    "pathBase": "onedrive",
    "path": "Logistica/Importaciones.xlsx",
    "sheet": "Importaciones",
    "headerRow": null
  },
  "exports": {
    "pathBase": "onedrive",
    "path": "Logistica/Exportaciones.xlsx",
    "sheet": "*",
    "headerRow": null
  }
}
```

El detector considera el OneDrive empresarial de la cuenta que ejecuta el programa. No busca Excel por todo el equipo ni toma una cuenta personal como alternativa. Si dos raíces contienen los mismos archivos, detiene la detección para que IT seleccione la correcta.

## 3. Iniciar y comprobar

```powershell
$env:TECHTOP_BOARD_CONFIG = "$env:USERPROFILE\TechTop\Configuracion\config.local.json"
.\.venv\Scripts\python.exe app.py
```

Abrir `http://127.0.0.1:8765/`. Si la pestaña ya estaba abierta, recargar con `Ctrl+F5` para cargar el nuevo JavaScript. Comprobar:

- Etiqueta **ITINERARIO INTERNO** y hora/fecha de última lectura exitosa.
- Importaciones: solo las veinte más próximas entre hoy y hoy + 30 días; diez por página, máximo dos. Si hay menos de once, solo una.
- ATP reemplaza ETA cuando existe; Arrived y fechas pasadas salen de la vista. En empates por fecha se ordena por Container.
- Un grupo de veinte o más en un día no genera páginas adicionales. Los restantes siguen en Excel y entran cuando les corresponda dentro del límite.
- Exportaciones mantiene el funcionamiento anterior. Revisar las páginas que necesite.

La selección se recalcula en cada lectura, normalmente cada 60 segundos. La vista consulta cada 30 segundos; dejar hasta 90 segundos después de que el cambio esté disponible localmente. OneDrive puede añadir tiempo de sincronización. Si falla una lectura, se mantiene la última selección válida con advertencia: no entran los contenedores siguientes hasta recuperarse la lectura.

## 4. Llevarlo al servidor u otra laptop

Aaron prepara Python y las dependencias en el equipo destino siguiendo `PRUEBA_LOCAL_WINDOWS.md`; no copiar `.venv` desde otro equipo. Instala el código y lleva la configuración portable por un canal interno, fuera del repositorio. Configura OneDrive bajo la cuenta que realmente ejecutará el programa, con acceso a ambos archivos y la misma estructura interna.

Antes de iniciar, comprobar sin cambiar nada:

```powershell
Set-Location "$env:USERPROFILE\TechTop\Proyecto"
.\.venv\Scripts\python.exe scripts\configurar_onedrive.py --config "$env:USERPROFILE\TechTop\Configuracion\config.local.json" --check
```

Si responde que ambos Excel se pueden leer, ejecutar los comandos del paso 3. La carpeta base se detecta nuevamente en ese equipo. Si cambia la estructura interna o el nombre de un archivo, corregir esa parte de la configuración local.

Si el detector no encuentra la raíz, la biblioteca SharePoint está en otra carpeta o hay varias raíces válidas, IT puede señalar la base explícitamente en la misma sesión PowerShell:

```powershell
$env:TECHTOP_ONEDRIVE_ROOT = "C:\RUTA_LOCAL\CarpetaBase"
```

Usar la carpeta real que contiene las rutas internas de ambos Excel. La barra `\` es correcta en este comando PowerShell; en JSON se usan `/`. Luego repetir comprobación e inicio en esa misma ventana. Para volver a detección automática:

```powershell
Remove-Item Env:TECHTOP_ONEDRIVE_ROOT -ErrorAction SilentlyContinue
```

Si el proceso será un servicio o tarea programada, Aaron debe configurar esa variable bajo su identidad de ejecución y validar sincronización, disponibilidad y permisos después de reiniciar/cerrar sesión. La detección no inicia sesión en Microsoft ni garantiza que OneDrive siga sincronizando en esas condiciones. El piloto continúa escuchando solo en loopback: no habilita acceso desde Roku por sí solo; HTTPS y autorización corresponden al despliegue con IT.

## Recuperación

Si se necesita volver a la configuración original de rutas absolutas, detener el programa y copiar el primer respaldo sobre el archivo actual:

```powershell
Copy-Item "$env:USERPROFILE\TechTop\Configuracion\config.local.json.bak" "$env:USERPROFILE\TechTop\Configuracion\config.local.json"
```

Ese respaldo tiene rutas del primer equipo y requiere revisión antes de usarlo en otro. La reversión del código se hace reinstalando la versión anterior desde GitHub; conservar siempre `.venv` y la configuración externa. No se han modificado filas de los itinerarios.
