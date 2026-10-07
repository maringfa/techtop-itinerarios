# Revisión técnica antes del piloto en la red

## Estado comprobado en esta entrega

- Perfil: backend Python de prueba local, pantalla web interna y app Roku SceneGraph empaquetable. La app Roku tiene demostración ficticia; aún no se ha ejecutado en un TV real.
- Fuente: dos archivos `.xlsx` de solo lectura. Las rutas se configuran externamente; no existe conexión Microsoft Graph ni validación con los Excel reales.
- El servidor solo puede escuchar en loopback. `/api/board` no tiene autenticación y devuelve datos del itinerario; `/health` no incluye identificadores. **No publicar este proceso en la LAN ni mediante un proxy accesible sin controles.**
- Configuración local y archivos reales excluidos del repositorio; la ausencia de archivos de ejemplo confidenciales fue revisada en el árbol versionado. La seguridad definitiva requiere revisión de IT con datos y entorno propios.

## Antes de abrir acceso a los Roku

1. Confirmar titularidad del repositorio, conceder acceso nominal a IT y decidir transferencia a una organización corporativa. Mantener el repositorio privado, exigir revisión de cambios y limitar las personas que pueden publicarlo.
2. Definir un servicio de lectura de los XLSX originales con identidad de mínimo privilegio y permisos únicamente sobre la carpeta necesaria. Si se usa sincronización de OneDrive para la prueba, validar su continuidad tras reinicio y cierre de sesión. El adaptador Graph no forma parte de este release.
3. Validar nombres de hojas y columnas, celdas combinadas, formatos de fecha y la nueva fecha individual `ATP` (llegada a planta) con los dos archivos reales dentro de TechTop. No enviar copias con datos reales al repositorio.
4. Diseñar una versión de servidor para LAN con HTTPS y autenticación o autorización por dispositivo, segmentación y reglas de firewall para ambos TV; no exponer `/api/board` fuera del alcance autorizado. Guardar cualquier secreto únicamente en el servidor, nunca en el paquete Roku, JavaScript ni GitHub.
5. Empaquetar y probar la app Roku nativa en ambos modelos/firmwares. Comprobar el comportamiento con 12 contenedores en una fecha, pérdida de conectividad, lectura fallida y reinicio de los televisores. Revisar que los datos mostrados no se conserven de forma indebida en el dispositivo.
6. Preparar paquete versionado, revisión, `/health`, despliegue y procedimiento de reversión. Registrar responsable y fecha de publicación. Ninguna prueba en servidor, conexión OneDrive/Graph o televisor se ha realizado en esta entrega.

## Alcance de privacidad

El tablero mostrará HBL, contenedores, contenido y transfer en ambos televisores. IT debe confirmar que su ubicación física y audiencia están autorizadas para esos datos.
