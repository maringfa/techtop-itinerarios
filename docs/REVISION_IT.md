# Revisión técnica antes del piloto en la red

## Estado comprobado en esta entrega

- Perfil: backend Python de prueba local, pantalla web interna y app Roku SceneGraph empaquetable. La app Roku tiene demostración ficticia; aún no se ha ejecutado en un TV real.
- Fuente: dos archivos `.xlsx` de solo lectura. El coordinador reportó una prueba local previa satisfactoria con sus Excel. La versión 0.7.0 se verificó aquí con datos ficticios; no se validó en Windows, servidor ni Roku. Las rutas se configuran externamente; no existe conexión Microsoft Graph.
- Selección de importaciones: hoy a hoy + 30 días inclusive, ATP sobre ETA, excluir Arrived, ordenar fecha/Container y limitar a veinte. Web y Roku tienen un máximo de dos páginas de diez. Exportaciones mantiene sus reglas previas. Se probó incorporación del siguiente registro y desplazamiento por ATP, límite estricto en empates y ausencia de tercera página por grupos de fechas.
- OneDrive: conversión de la configuración con respaldo y reemplazo atómico; resolución de rutas internas al iniciar. Pruebas de traslado entre perfiles ficticios, ambigüedad de cuenta, raíz no disponible, incompatibilidad de archivo y rechazo de rutas que salen de la raíz. La lectura del registro Windows y la sincronización real requieren prueba en destino.
- El servidor solo puede escuchar en loopback. `/api/board` no tiene autenticación y devuelve datos del itinerario; `/health` no incluye identificadores. **No publicar este proceso en la LAN ni mediante un proxy accesible sin controles.**
- Configuración local y archivos reales excluidos del repositorio; la ausencia de archivos de ejemplo confidenciales fue revisada en el árbol versionado. La seguridad definitiva requiere revisión de IT con datos y entorno propios.

## Antes de abrir acceso a los Roku

1. Confirmar titularidad del repositorio, conceder acceso nominal a IT y decidir transferencia a una organización corporativa. Mantener el repositorio privado, exigir revisión de cambios y limitar las personas que pueden publicarlo.
2. Definir un servicio de lectura de los XLSX originales con identidad de mínimo privilegio y permisos únicamente sobre la carpeta necesaria. Si se usa sincronización de OneDrive para la prueba, validar su continuidad tras reinicio y cierre de sesión. El adaptador Graph no forma parte de este release.
   La detección se realiza bajo esa identidad, no bajo la del instalador: `OneDriveCommercial` y `HKCU\Software\Microsoft\OneDrive\Accounts\Business*\UserFolder`. La raíz debe contener las dos rutas internas. Si hay varias raíces válidas, una biblioteca externa a ellas o falta detección, fijar `TECHTOP_ONEDRIVE_ROOT` solo en el entorno del proceso; no en GitHub. La cuenta personal no se toma como sustituto. Revisar ACL de configuración y respaldo, disponibilidad offline y frescura independiente de la hora de lectura.
3. Validar nombres de hojas y columnas, celdas combinadas, formatos de fecha y la nueva fecha individual `ATP` (llegada a planta) con los dos archivos reales dentro de TechTop. No enviar copias con datos reales al repositorio.
   Para exportaciones con pestañas mensuales, verificar `sheet: "*"`, encabezados por pestaña, meses futuros y cambio de año. Confirmar que no haya hojas de resumen con la misma estructura que dupliquen registros; las hojas ocultas también se incluyen.
4. Diseñar una versión de servidor para LAN con HTTPS y autenticación o autorización por dispositivo, segmentación y reglas de firewall para ambos TV; no exponer `/api/board` fuera del alcance autorizado. Guardar cualquier secreto únicamente en el servidor, nunca en el paquete Roku, JavaScript ni GitHub.
5. Empaquetar y probar la app Roku nativa en ambos modelos/firmwares. Comprobar doce y más de veinte contenedores en una fecha, máximo de dos páginas de importaciones, ATP que cambia de posición, horizonte de treinta días, pérdida de conectividad, lectura fallida y reinicio de los televisores. Revisar que los datos mostrados no se conserven de forma indebida en el dispositivo.
6. Preparar paquete versionado, revisión, `/health`, despliegue y procedimiento de reversión. Registrar responsable y fecha de publicación. Ninguna prueba en servidor, conexión OneDrive/Graph o televisor se ha realizado en esta entrega.
   Seguir `docs/ACTUALIZAR_WINDOWS.md` para conservar el entorno y configuración local. El script escribe exclusivamente en la configuración externa y su respaldo, nunca en los XLSX; comprobar permisos de lectura de las fuentes con la cuenta del servicio.

## Alcance de privacidad

El tablero mostrará HBL, contenedores, contenido y transfer en ambos televisores. IT debe confirmar que su ubicación física y audiencia están autorizadas para esos datos.
