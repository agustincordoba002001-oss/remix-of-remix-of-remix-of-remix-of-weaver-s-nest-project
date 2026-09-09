# Guardar videos y proyectos de edición

## Objetivo
El video elegido se subirá al almacenamiento permanente del proyecto. Al volver a la página, el último video y su guion seguirán disponibles para editar frase por frase.

## Cambios
- Guardar videos grandes de forma permanente, mostrando progreso y estado de carga.
- Crear un registro del proyecto para vincular cada video con su guion y sus cambios aprobados.
- Abrir automáticamente el último proyecto guardado al entrar.
- Usar el video ya incluido como proyecto inicial, sin pedir otra subida.
- Mantener la aprobación aislada: modificar una frase no cambia las demás.

## Detalles técnicos
- Almacenamiento privado con límite de 500 MB por video.
- La página recibe enlaces temporales seguros para reproducir el archivo.
- El guion y las correcciones se conservan como datos estructurados.
- Se verificará la carga, reapertura, reproducción y edición en computadora y celular.
