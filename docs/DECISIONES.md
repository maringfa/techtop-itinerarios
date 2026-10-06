# Decisiones del piloto TechTop

## Alcance

El televisor RCA Roku TV ejecutará una app propia. Los dos televisores mostrarán la misma vista de importaciones y exportaciones. No habrá computadora dedicada a proyectar. El servidor interno existente lee los itinerarios y entrega únicamente los datos necesarios para la pantalla. El código en este repositorio usa datos inventados; no contiene rutas, cuentas ni documentos internos.

## Fuente de datos: dos XLSX originales

La primera integración leerá **directamente los dos itinerarios originales, en modo solo lectura**. No se mantendrá un tercer Excel. Un tercer archivo introduciría otro trabajo de actualización y podría quedar desfasado justo cuando cambie una fecha. El servidor hará la selección y transformación en memoria; `/api/board` ya representa el contrato de salida de esa transformación.

La lectura real depende de validar encabezados, nombres de hojas, rangos combinados, permisos y sincronización con archivos verdaderos dentro de TechTop. El piloto admite archivos XLSX locales: IT puede comenzar con una copia sincronizada, protegida en el servidor, y definir después un acceso de solo lectura mediante Microsoft Graph si la carpeta está en SharePoint/OneDrive. El adaptador Graph **aún no existe**. La sincronización de OneDrive bajo la sesión de un empleado no es la solución final elegida.

### Reglas de datos aprobadas

| Fuente | Regla de lectura | Regla para la pantalla |
| --- | --- | --- |
| Importaciones | `ETA`, `HBL` y otras celdas compartidas se heredan cuando hay celdas combinadas. `Llegada a planta` pertenece a cada contenedor. | Mostrar contenedor, HBL, contenido y fecha individual de planta. `Arrived` significa llegada a planta. ETA activa seguimiento portuario desde dos días antes; nunca sustituye la llegada a planta. |
| Exportaciones | Leer `Origin`, `Reservation`, `Container`, `Transfer` y `Deliver at TTICR`. | Mostrar solo filas con fecha de salida y Transfer. HBL y contenedor se muestran pendientes si aún no están asignados. |

El navegador piloto presenta hasta diez importaciones y cinco exportaciones por página, pero genera tantas páginas como hagan falta; no hay límite de contenedores por fecha. Muestra fecha y hora de la última lectura exitosa y conserva la última lectura válida si la siguiente falla.

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
