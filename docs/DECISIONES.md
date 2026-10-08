# Decisiones del piloto TechTop

## Alcance

El televisor RCA Roku TV ejecutará una app propia. Los dos televisores mostrarán la misma vista de importaciones y exportaciones. No habrá computadora dedicada a proyectar. El servidor interno existente lee los itinerarios y entrega únicamente los datos necesarios para la pantalla. El código en este repositorio usa datos inventados; no contiene rutas, cuentas ni documentos internos.

## Fuente de datos: dos XLSX originales

La primera integración leerá **directamente los dos itinerarios originales, en modo solo lectura**. No se mantendrá un tercer Excel. Un tercer archivo introduciría otro trabajo de actualización y podría quedar desfasado justo cuando cambie una fecha. El servidor hará la selección y transformación en memoria; `/api/board` ya representa el contrato de salida de esa transformación.

La lectura real depende de validar encabezados, nombres de hojas, rangos combinados, permisos y sincronización con archivos verdaderos dentro de TechTop. El piloto admite archivos XLSX locales: IT puede comenzar con una copia sincronizada, protegida en el servidor, y definir después un acceso de solo lectura mediante Microsoft Graph si la carpeta está en SharePoint/OneDrive. El adaptador Graph **aún no existe**. La sincronización de OneDrive bajo la sesión de un empleado no es la solución final elegida.

### Reglas de datos aprobadas

El archivo de exportaciones puede tener una pestaña por mes. `sheet: "*"` lee todas las pestañas con estructura del itinerario, sin depender de sus nombres ni de cambiar de pestaña cada mes. Incluye las ocultas y descubre pestañas nuevas al releer el archivo. Combina filas y filtra por fechas reales de salida, para conservar todos los movimientos de hoy y futuros, incluidos próximos meses/años. Las hojas sin estructura de itinerario se omiten; las reconocibles pero incompletas generan error. No elimina registros repetidos entre pestañas automáticamente. La selección por nombre exacto sigue disponible y `null` conserva la selección anterior de primera hoja visible.

| Fuente | Regla de lectura | Regla para la pantalla |
| --- | --- | --- |
| Importaciones | `ETA`, `HBL` y otras celdas compartidas se heredan cuando hay celdas combinadas. `ATP` (llegada a planta) pertenece a cada contenedor. | Mostrar HBL, Container e Items. Usar ATP si existe y rotular «ATP · Llegada a planta»; si está vacío, usar ETA y rotular «ETA · Arribo estimado al puerto». Excluir `Arrived`. Fecha elegida entre hoy y hoy + 30 días, ambos inclusive; seleccionar solo los veinte más próximos. No hay cuadro portuario separado. |
| Exportaciones | Leer `Origin`, `Reservation`, `Container`, `Transfer` y `Deliver at TTICR`. | Mostrar HBL (Reservation), Container, Origin como destino, Transfer y fecha de salida desde hoy. Exigir fecha y Transfer; HBL y contenedor pueden estar pendientes. No mostrar contenido de carga. |

Las fechas de ambas listas se comparan con el día actual de Costa Rica y se ordenan de la más cercana a la más lejana. El servidor filtra la agenda; web y Roku vuelven a descartar fechas pasadas al cambiar de día, incluso al mostrar la última lectura válida.

Al agregar ATP, la tarjeta deja de mostrar ETA y cambia de posición según ATP. Un ATP pasado no habilita volver al ETA: el contenedor se excluye. Sin ninguna de las dos fechas, no aparece. El contrato JSON de importaciones conserva `plant` (ATP o `null`) y agrega `displayDate` (fecha elegida) y `dateType` (`ATP` o `ETA`); no incluye un ETA adicional cuando existe ATP.

Desde 0.7.0-pilot, importaciones muestra como máximo veinte contenedores en dos páginas de diez. El límite es estricto incluso si una fecha tiene más de veinte; un grupo de fecha puede repartirse entre páginas. En empates se ordena por Container para estabilizar la selección. Cada lectura reconstruye la agenda completa: al salir un registro o actualizar ATP, entran los siguientes elegibles del horizonte móvil. Este acuerdo del 8 de octubre de 2026 sustituye la regla anterior de mostrar todos los contenedores de una misma fecha. Exportaciones mantiene cinco por página y tantas páginas como necesite, sin horizonte de treinta días. Se conserva la fecha/hora de última lectura exitosa y la última selección válida si la siguiente falla; mientras falle, no se pueden incorporar registros que quedaron fuera de esa selección.

Desde 0.7.1-pilot, el encabezado muestra **«Primeros X de Y pendientes · página N/P»**. X es la selección visible total (hasta veinte dentro de treinta días), no las tarjetas de una sola página. Y cuenta todos los contenedores pendientes desde hoy, incluidos los de fechas más lejanas, usando ATP si existe y ETA en su ausencia; excluye Arrived, fechas pasadas y registros sin fecha. Por ejemplo, diecinueve seleccionados de cuarenta pendientes muestran «Primeros 19 de 40 pendientes · página 2/2» en la segunda página, sin llenar el espacio restante con fechas fuera del horizonte. El total se actualiza con cada lectura exitosa; web y Roku descartan del conteo las fechas que pasan al cambiar de día, incluso con una lectura retenida.

El contrato agrega `importsPendingByDate`: cantidades agrupadas por fecha elegida para todos los pendientes desde hoy. Para registros fuera de las veinte tarjetas no se envían identificadores ni contenido adicional. No se eliminan duplicados entre hojas: el conteo usa los mismos registros elegibles que las tarjetas.

### Configuración portable de OneDrive

Las rutas operativas y su respaldo permanecen fuera del código. El script `scripts/configurar_onedrive.py` transforma una configuración existente de rutas absolutas a rutas internas con `pathBase: "onedrive"`, después de comprobar ambos itinerarios. Al arrancar, el backend obtiene la carpeta OneDrive empresarial de la cuenta que ejecuta el proceso y resuelve esas rutas internas. Si hay dos raíces válidas, se exige selección explícita mediante `TECHTOP_ONEDRIVE_ROOT`; no se adivina ni se buscan Excel por todo el equipo. Rutas absolutas y relativas a la configuración conservan compatibilidad.

Esto adapta el prefijo del usuario, no el contenido ni los permisos. Requiere la misma estructura interna, OneDrive configurado, sincronización activa y archivos locales disponibles bajo la identidad de ejecución. No sustituye una integración Graph ni garantiza operación después de cerrar sesión. Una biblioteca sincronizada fuera de la raíz detectada requiere carpeta base explícita de IT.

## App para Roku

La web ya disponible es la referencia visual aprobada, pero Roku OS no abre HTML como un navegador general. La app SceneGraph en `roku/` consulta el JSON de `/api/board` y dibuja tarjetas nativas. Incluye datos ficticios para probar su instalación. No se ha probado en un televisor real ni conectado a archivos reales; IT debe validar su funcionamiento en el firmware de ambos Roku antes de operar.

La app se instalará en cada TV durante el piloto en Developer Mode. Una PC se usa para cargar el paquete, sin quedar conectada para la operación. La distribución beta de Roku caduca a los 120 días; antes de operar permanentemente, IT debe validar el mecanismo de distribución autorizado y el comportamiento tras reinicios del TV.

## Seguridad y operación

- Repositorio privado provisional en la cuenta personal del coordinador; IT revisará permisos y transferencia a una organización de TechTop antes de operación.
- Nunca subir los XLSX reales, claves, URLs de uso interno o configuración local. La app Roku no recibe acceso directo a OneDrive ni credenciales de Microsoft.
- Los televisores y el servidor deben tener conectividad permitida entre sí a través de un proxy HTTPS autorizado. El piloto actual solo escucha en loopback; la publicación del proxy, autorización y certificados requieren implementación de IT.
- `/health` no revela registros; `/api/board` contiene identificadores operativos y necesita protección antes de abrirse a los televisores.
- Registrar la fecha de último dato válido y un estado visible si la actualización falla. La pantalla no debe mostrar una agenda vieja como si fuera actual.

## Por validar con IT en TechTop

1. Dueño del repositorio privado y miembros con acceso.
2. Cuenta/carpeta real de OneDrive o sitio SharePoint, identidad de servicio y permisos de lectura.
3. Forma de acceso de ambos televisores al servidor interno, control de acceso y ruta HTTPS.
4. Tamaño/resolución de los dos RCA Roku TV y prueba de legibilidad de la interfaz nativa.
5. Procedimiento permanente de distribución de la app Roku.
