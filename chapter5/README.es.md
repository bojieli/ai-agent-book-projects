# Capítulo 5 · Coding Agent y Generación de Código

> El código es una "herramienta para crear nuevas herramientas"; panorama completo de un Coding Agent de grado de producción

← [Volver al README principal](../docs/es/README.md) · 📖 [Leer texto del capítulo](../book-es/chapter5.es.md)

## Cómo leer los experimentos

El texto usa skeletons breves para explicar el flujo de control; el directorio de experimentos contiene adaptadores SDK completos, registros, pruebas y evidencias de aceptación. No hace falta leer cada archivo línea por línea.

- **Starter:** Empieza por el objetivo, el comando mínimo y la aceptación; comienza con [coding-agent](coding-agent/);
- **Builder:** Sigue el punto de entrada, el bucle central, el esquema de estado/mensajes, las herramientas y el verificador.
- **Maintainer:** Después revisa pruebas, manifiestos, fallos, rollback y adaptadores de proveedores.

En la primera pasada puedes omitir credenciales, presentación y compatibilidad de proveedores; vuelve al reproducir una cifra.

## Proyectos Complementarios

| Exp. | Proyecto | Tipo | Descripción |
| :--: | --- | :--: | --- |
| 5-1 | [provider-failover](provider-failover/) | ✅ | Traspaso real de una traza a medias entre seis pares de proveedores × tres variantes: el formato neutral cambió 6/6 y siempre llegó al total correcto, el traspaso literal 3/6 y el borrado de todo el razonamiento 4/6; cada fallo conserva el error real del proveedor |
| 5-2 | [provider-failover](provider-failover/) | ✅ | Recuperación de un flujo cortado a mitad de razonamiento, de prosa o de argumento: la continuación ahorra entre 15% y 66% de tokens en prosa, pero con un argumento truncado produce JSON válido y a la vez semánticamente incorrecto; la meta-instrucción costó más que reenviar el turno completo en todas las celdas |
| 5-3 | [code-for-math](code-for-math/) | ✅ | Comparación entre cadena de pensamiento pura y asistencia por código ejecutado en sandbox sympy/numpy/scipy |
| 5-4 | [code-for-logic](code-for-logic/) | ✅ | Conversión de acertijos lógicos a CSP utilizando `python-constraint` para su resolución |
| 5-5 | [small-model-codified-rules](small-model-codified-rules/) | ✅ | Experimento de Tau-bench sobre reglas de reembolso codificadas en funciones/herramientas |
| 5-6 | [paper-to-ppt](paper-to-ppt/) | ✅ | Generación de presentaciones PPT mediante código Slidev y revisión visual automatizada |
| 5-7 | [paper-to-video](paper-to-video/) | ✅ | Síntesis de video explicativo con voz a partir de código Slidev y síntesis TTS con ffmpeg |
| 5-8 | [video-edit](video-edit/) | ✅ | Edición de video con visión y lenguaje natural en dos pasos con iteración de revisión |
| 5-9 | [cad-vs-diffusion](cad-vs-diffusion/) | ✅ | Prueba real de una misma especificación de brida por dos rutas: el CadQuery de 17 líneas escrito por Kimi, con desviación cero en todas las dimensiones; Hunyuan3D-2.1 (Space público de HF) perdió los 4 orificios pasantes y desvió el diámetro exterior un −99,4 %. Cambio M5→M6: la ruta de código modifica una línea de parámetro, con 0 llamadas al LLM y deriva cero en las demás dimensiones; la ruta generativa reejecuta todo el conjunto con una deriva del diámetro exterior de +283 % e inversión axial. Grupo de control de la planta en maceta: naturalidad 3 frente a 8, con la frontera de aplicabilidad invertida |
| 5-10 | [adaptive-log-parser](adaptive-log-parser/) | ✅ | Generación dinámica y actualización en caliente de funciones `parse` ante nuevos formatos de registro |
| 5-11 | [log-diagnosis](log-diagnosis/) | ✅ | Agente de diagnóstico para análisis de registros, generación de pruebas de regresión y verificación |
| 5-12 | [dynamic-form](dynamic-form/) | ✅ | Generación dinámica de formularios HTML interactivos para completar información faltante |
| 5-13 | [erp-agent](erp-agent/) | ✅ | Conversión de lenguaje natural a SQL en modo artefacto para evitar transferencia innecesaria de datos |
| 5-14 | [conversational-ui](conversational-ui/) | ✅ | Personalización de UI por lenguaje natural modificando código React con actualización HMR vía Vite |
| 5-15 | [permission-embedded-data-objects](permission-embedded-data-objects/) | ✅ | Almacén de objetos sobre PostgreSQL que aplica autorización, validación e integridad referencial bajo código de aplicación generado dinámicamente |
| 5-16 | [coding-agent](coding-agent/) | ✅ | Asistente de código basado en Claude con 17 herramientas implementadas en Python puro sin dependencias de CLI |

## Tipos de Proyectos

| Icono | Tipo | Significado |
| :--: | --- | --- |
| ✅ | **Autónomo** | Código completo en este repositorio, se ejecuta tras configurar la Clave API |
| 📖 | **Guía de Reproducción** | Documento detallado que depende de **repositorios externos** para realizar `git clone` |
| 🚧 | **Documento de Diseño** | Solo arquitectura/plan de implementación, el código ejecutable aún está en desarrollo |
