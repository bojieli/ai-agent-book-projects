# Capítulo 6 · Evaluación de Agentes

> Convertir el rendimiento en señales comparables: entornos, métricas, significación estadística, selección guiada por evaluación

← [Volver al README principal](../docs/es/README.md) · 📖 [Leer texto del capítulo](../book-es/chapter6.es.md)

Los requisitos, la evidencia directa y los límites de cada experimento se detallan en el [registro de aceptación](EXPERIMENT_LEDGER.md).

## Proyectos Complementarios

| Exp. | Proyecto | Tipo | Descripción |
| :--: | --- | :--: | --- |
| 6-1 | `tau2-bench/` | 📖 | Ejecuta la evaluación multirronda con doble control de τ²-bench y la compara con las definiciones de tareas, condiciones de éxito y simulador de usuario de τ-bench |
| 6-2 | `tau2-bench/` | 📖 | Completa manualmente tareas graduadas de τ²-bench y registra sus trayectorias; es solo una de las seis clases de benchmarks que se muestrean en 6-2 |
| 6-2 | `terminal-bench/` | 📖 | Evalúa la capacidad integral del Agent en un entorno de terminal real (compilación, entrenamiento y despliegue), con unas 100 tareas y un marco de ejecución |
| 6-2 | `SWE-bench/` | 📖 | Evalúa la capacidad de los LLM para resolver incidencias reales de GitHub en las variantes SWE-bench, Lite, Verified y Multimodal |
| 6-2 | `GAIA/` | 📖 | Evalúa herramientas, búsqueda y autonomía mediante más de 450 preguntas no triviales con respuestas inequívocas y tres niveles de dificultad |
| 6-2 | `OSWorld/` | 📖 | Evalúa tareas complejas en un sistema operativo completo: gestión de archivos, uso de aplicaciones y configuración del sistema |
| 6-2, 6-12 | `android_world/` | 📖 | Evalúa navegación de aplicaciones, interacción con la IU y finalización de tareas en Android (repositorio de benchmark externo) |
| 6-3 | [user-memory-evaluation](../chapter3/user-memory-evaluation/) | ✅ | La rúbrica multidimensional de cuatro niveles se ejecutó sobre 180/180 evaluaciones reales (60 casos × 3 sistemas); el [índice independiente](user-memory-system-evaluation/results/full_6_3_structured_rubric_evidence.json) conserva razones, evidencia, casos límite y el veto por alucinación con estado `complete` |
| 6-4 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | 180/180 trayectorias reales (60 casos × 3 sistemas), sin errores y con precios completos en la moneda nativa; el [resultado de aceptación](user-memory-system-evaluation/results/full_6_4_60_cases_costed.json) tiene estado `complete` |
| 6-5 | [user-memory-policy-eval](user-memory-policy-eval/) | ✅ | Ejecuta 11 casos problemáticos de prefijos de trayectoria en representaciones de memoria JSON, Markdown y similares a Python, con llamadas reales a OpenRouter y comprobaciones deterministas de políticas. |
| 6-6 | [tts-quality-eval](tts-quality-eval/) | ✅ | La [aceptación real](tts-quality-eval/validation/mistral_multimodal_20260730/manifest.json) completa 8/8 evaluaciones Voxtral de cuatro dimensiones sobre dos proveedores y cuatro clases de muestras; cada audio candidato y de referencia tiene hash |
| 6-7 | [elo-leaderboard](elo-leaderboard/) | ✅ | Tabla de clasificación del rendimiento de Agentes basada en ELO y comparaciones directas |
| 6-8 | [model-action-threshold](model-action-threshold/) | ✅ | Compara GPT-5.6-sol y Claude Sonnet 5 en la transición de la exploración a la primera edición bajo el mismo Coding Harness neutral; se completaron 18/18 celdas sin errores de API y el [manifiesto](model-action-threshold/results/exp6-7-action-threshold-20260731-v1/manifest.json) vincula trayectorias y resúmenes mediante hashes verificables |
| 6-9 | [agent-cost-analysis](agent-cost-analysis/) | ✅ | Desglose integral de costos para una tarea multirronda de reembolso, con diseño compatible con caché KV y cuantificación A/B del ahorro por compresión de contexto |
| 6-10 | [model-benchmark](model-benchmark/) | 🚧 | Están implementadas las campañas 8K/32K/128K × 512/2048, rampas por límites, costos del Agent y disponibilidad durante 168 horas; el [manifiesto](model-benchmark/results/manifest.json) actual solo contiene pruebas reales de humo y disponibilidad |
| 6-11 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | La matriz completa 4×3×2×60 conserva 1.440/1.440 trayectorias reales sin errores ni uso sin precio, con métricas completas de recuperación y tareas, análisis de interacción y un verificador independiente aprobado. |
| 6-12 | [android-world](android-world/) | 📖 | Informe y notas de análisis de fallos de la evaluación de T3A Agent en AndroidWorld (punto de partida de 6-12, no código fuente del benchmark) |
| 6-13 | [openvla-robotwin2-eval](openvla-robotwin2-eval/) | ✅ | La campaña oficial con una GPU completó 256 episodios por brazo: chunk 1 obtuvo 0/256 y chunk 25 obtuvo 26/256, con hashes de los 512 rollouts. |
| — | [public-health-reporting-eval](public-health-reporting-eval/) | ✅ | Evalúa objetivamente las llamadas a herramientas, la exactitud de los cálculos, las citas de evidencia y las afirmaciones sin fundamento sobre datos agregados sintéticos al estilo DHIS2 |

> Los benchmarks externos entre comillas invertidas deben clonarse por separado. [`android-world/`](android-world/) (con guion) contiene las notas internas sobre la evaluación de T3A; no es la misma ruta que el código externo `android_world/`.

## Tipos de Proyectos

| Icono | Tipo | Significado |
| :--: | --- | --- |
| ✅ | **Autónomo** | Código completo en este repositorio, se ejecuta tras configurar la Clave API |
| 📖 | **Guía de Reproducción** | Documento detallado que depende de **repositorios externos** para realizar `git clone` |
| 🚧 | **En curso** | Existe una implementación, pero el alcance del experimento o su evidencia de aceptación aún no satisface todos los requisitos del texto |
