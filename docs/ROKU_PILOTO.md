# Instalación de la app Roku y conexión con el servidor

## Qué hay ahora

`roku/` contiene una app SceneGraph que dibuja directamente los datos de `/api/board`, sin navegador ni generación de imágenes. Presenta importaciones (máximo veinte en dos páginas de diez, dentro de hoy a hoy + 30 días), exportaciones (hasta cinco por página, sin el nuevo límite total), rota las páginas cada 16 segundos, reconsulta cada 30 segundos y conserva la última vista válida con un aviso si se pierde conexión. Al instalarla tal como está, funciona en **modo demostración con datos inventados** incluidos en `roku/assets/demo.json`. El encabezado de importaciones muestra «Primeros X de Y pendientes · página N/P»: X es la selección visible total y Y todos los futuros elegibles, incluidos los que quedan fuera del horizonte. El backend 0.7.1 entrega el total por fechas; con un servidor anterior o demo sin ese campo solo se pueden contar los registros recibidos. Sus fechas son fijas: actualizar las fechas ficticias antes de probar si quedaron en el pasado; el empaquetador no las renueva.

No se ha ejecutado en un televisor real ni compilado con herramientas Roku en este entorno. Aaron debe validar en el dispositivo y corregir cualquier diferencia de firmware o diseño observada.

Cada importación muestra una sola fecha: «ETA · Arribo estimado al puerto» mientras no haya ATP, o «ATP · Llegada a planta» cuando ya se agendó la llegada. ATP tiene prioridad y sustituye ETA en la tarjeta y su orden. Importaciones se limita a las veinte más cercanas del horizonte móvil; un empate de fecha no añade páginas. El servidor y el cliente descartan fechas elegidas anteriores a hoy en Costa Rica; el servidor también excluye contenedores con `Status = Arrived`.

## Instalar para ver la demostración en cada televisor

1. Activar Developer Mode en cada Roku, siguiendo la [guía de Roku](https://developer.roku.com/dev/docs/developer-setup), y guardar la contraseña de desarrollo en el gestor corporativo. La IP mostrada en este paso es la **del televisor**.
2. En el equipo de desarrollo, ejecutar `python scripts/build_roku.py` desde la raíz del repositorio. El ZIP aparece en `dist/techtop-itinerarios-roku.zip` y no se versiona.
3. En el navegador de ese equipo, abrir la IP del televisor, iniciar sesión como `rokudev` con la contraseña definida en el paso 1, seleccionar el ZIP y cargarlo. Repetir en el segundo Roku.
4. Abrir **TechTop Itinerarios** en ambos. Debería verse `PILOTO · DATOS FICTICIOS`; con once a veinte fechas ficticias elegibles, se muestran dos páginas. La computadora de desarrollo se retira después de instalar; no necesita permanecer conectada para mostrar el demo.

## Conectar los Excel originales para la prueba real

1. En el servidor, instalar Python y `requirements.txt`; configurar `TECHTOP_BOARD_CONFIG` con las dos rutas de Excel legibles en solo lectura, fuera del repositorio. Para rutas portables de OneDrive, seguir `ACTUALIZAR_WINDOWS.md` y ejecutar el script con `--check` bajo la cuenta real de ejecución. Validar `/health` y `/api/board` **en localhost**. `config.example.json` solo apunta a los archivos ficticios.
2. IT monta un proxy interno que atienda **HTTPS con certificado válido en los Roku**, autorización de ambos dispositivos y red limitada. El backend continúa en loopback. No publicar el proceso Python ni `/api/board` directamente en Internet o en toda la LAN. Roku usa el almacén de CA del sistema y verifica el nombre del servidor; la integración opcional con certificados de cliente Roku requiere configuración y validación del proxy por IT.
3. Antes de empaquetar, Aaron edita `roku/source/config.brs`, reemplaza `return "demo"` por `return "https://nombre-interno-autorizado/api/board"` y vuelve a generar el ZIP. La URL debe ser alcanzable desde los dos Roku; **no poner contraseñas, tokens, parámetros secretos o datos reales en ese archivo**. El cliente solo acepta HTTPS para datos de red.
4. Reinstalar el ZIP en ambos dispositivos y comparar una fecha/Transfer/HBL/contenedor contra los Excel originales dentro de TechTop. Verificar reinicio del servidor, archivo cerrado o modificado, pérdida de conexión y recuperación. En el Roku aparecerá la última lectura válida junto con aviso de error cuando falle.

Una ruta IP del servidor no se introduce en el navegador del Roku: el paquete contiene la URL de lectura y la app realiza la solicitud. Una IP sola en HTTPS requiere certificado válido para esa IP o un nombre DNS interno con certificado compatible.

## Distribución y operación

La instalación manual es para el **piloto**. El repositorio no publica una app en Roku Store, no abre una ficha pública y no configura el proceso de revisión de Roku. Para una instalación corporativa permanente IT debe elegir la distribución permitida por Roku, comprobar políticas vigentes, cuenta de desarrollador, firma, actualización y permanencia de la app. El ZIP de desarrollo se instala en cada TV; no es un enlace de la tienda para cualquier usuario. Roku documenta [instalación de desarrollo](https://developer.roku.com/dev/docs/developer-setup) y [empaquetado y publicación](https://developer.roku.com/dev/docs/packaging-channels).
