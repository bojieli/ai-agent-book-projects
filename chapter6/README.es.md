# Capítulo 6 · Evaluación de Agentes

> Convertir el rendimiento en señales comparables: entornos, métricas, significación estadística, selección guiada por evaluación

← [Volver al README principal](../docs/es/README.md) · 📖 [Leer texto del capítulo](../book-es/chapter6.es.md)

## Proyectos Complementarios

| Exp. | Proyecto | Tipo | Descripción |
| :--: | --- | :--: | --- |
| 6-1, 6-2 | `tau2-bench/` | 📖 | Evaluación de capacidades de razonamiento complejo y uso de herramientas en tareas de dominio |
| 6-2 | `terminal-bench/` | 📖 | Evaluación de capacidades extremo a extremo en entorno de terminal real (compilación, entrenamiento, despliegue) |
| 6-2 | `SWE-bench/` | 📖 | Evaluación de solución de problemas reales de GitHub en múltiples versiones |
| 6-2 | `GAIA/` | 📖 | Evaluación de capacidades autónomas y de búsqueda con 450+ preguntas no triviales |
| 6-2 | `OSWorld/` | 📖 | Evaluación de tareas complejas en entorno de sistema operativo completo |
| 6-2, 6-10 | `android_world/` | 📖 | Evaluación de navegación de aplicaciones e interacción en entorno Android (repositorio externo) |
| 6-5 | [tts-quality-eval](tts-quality-eval/) | ✅ | Evaluación de calidad TTS con sintaxis y puntuación por LLM-as-a-Judge según rúbricas |
| 6-6 | [elo-leaderboard](elo-leaderboard/) | ✅ | Tabla de clasificación de rendimiento de Agentes basada en puntuación ELO |
| 6-7 | [agent-cost-analysis](agent-cost-analysis/) | ✅ | Desglose de costos extremo a extremo en tareas de Agentes y cuantificación de ahorro A/B |
| 6-8 | [model-benchmark](model-benchmark/) | ✅ | Benchmarking de latencia TTFT, p50/p95, rendimiento y tasa de éxito en API compatibles con OpenAI |
| 6-10 | [android-world](android-world/) | 📖 | Notas de análisis de evaluación y fallos de T3A Agent en AndroidWorld (documento interno) |
| — | [public-health-reporting-eval](public-health-reporting-eval/) | ✅ | Evaluación objetiva de llamadas a herramientas, precisión de cálculo y referencias en informes de salud pública |

## Tipos de Proyectos

| Icono | Tipo | Significado |
| :--: | --- | --- |
| ✅ | **Autónomo** | Código completo en este repositorio, se ejecuta tras configurar la Clave API |
| 📖 | **Guía de Reproducción** | Documento detallado que depende de **repositorios externos** para realizar `git clone` |
| 🚧 | **Documento de Diseño** | Solo arquitectura/plan de implementación, el código ejecutable aún está en desarrollo |
