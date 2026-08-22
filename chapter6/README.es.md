# Capítulo 6 · Interacción: la expansión de los espacios de observación y de acción

> Extensión del texto a la voz, GUI y mundo físico: tres paradigmas de voz, Computer Use, robótica

← [Volver al README principal](../docs/es/README.md) · 📖 [Leer texto del capítulo](../book-es/chapter6.es.md)

## Cómo leer los experimentos

El texto usa skeletons breves para explicar el flujo de control; el directorio de experimentos contiene adaptadores SDK completos, registros, pruebas y evidencias de aceptación. No hace falta leer cada archivo línea por línea.

- **Starter:** Empieza por el objetivo, el comando mínimo y la aceptación; comienza con [live-audio](live-audio/);
- **Builder:** Sigue el punto de entrada, el bucle central, el esquema de estado/mensajes, las herramientas y el verificador.
- **Maintainer:** Después revisa pruebas, manifiestos, fallos, rollback y adaptadores de proveedores.

En la primera pasada puedes omitir credenciales, presentación y compatibilidad de proveedores; vuelve al reproducir una cifra.

## Proyectos Complementarios

| Exp. | Proyecto | Tipo | Descripción |
| :--: | --- | :--: | --- |
| 6-1 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | Agente FastAPI orientado a eventos con integración asíncrona de herramientas MCP |
| 6-2 | [async-agent](async-agent/) | ✅ | Marco Flux orientado a eventos asíncronos monohilo con colas por prioridad e interrupción |
| 6-3 | [live-audio](live-audio/) | ✅ | La [evidencia real de una ronda](live-audio/backend/validation/real_pipeline_20260729_localwhisper_ark_fish/evidence.json) completa micrófono → Silero VAD → Whisper local → LLM ARK en streaming → Fish S1; los cinco hashes de medios/modelos coinciden, aunque no representa carga concurrente o de producción |
| Add-on | [phone-agent](phone-agent/) | ✅ | El proyecto WebRTC local conserva las ejecuciones directa y ReAct con RTP de micrófono del navegador, Whisper local, LLM externo real, TTS y RTP de bajada; ambas pasan 20/20 puertas. PSTN/E.164 queda fuera de este alcance local. La [manifest](phone-agent/validation/runs/phone-agent-webrtc-audio-20260731-v1/manifest.json) conserva el identificador histórico. |
| 6-4 | [streaming-speech](streaming-speech/) | ✅ | La [aceptación local canónica](streaming-speech/validation/runs/exp6-4-qwen2audio-whisper-provenance-20260730-v3/manifest.json) ejecuta estrictamente prefijos incrementales Qwen2-Audio y VAD de 600 ms + Whisper; 8/8 puertas de ejecución y procedencia pasan, aunque los resultados solo reproducen 2/6 casos |
| 6-5 | [end-to-end-speech](end-to-end-speech/) | ✅ | MiniCPM-o 4.5, con revisión fijada, se ejecutó localmente en una RTX PRO 6000: end-to-end y self-cascade obtuvieron 3/4 con fallos semánticos/paralingüísticos complementarios; se conservaron audio real de 24kHz y evidencia de aceptación. |
| 6-6 | [controllable-tts](controllable-tts/) | ✅ | Biblioteca real Fish Audio S1 con 4×3×2=24 audios de referencia y medios A/B/C; tres evaluaciones reales ciegas y equilibradas de Voxtral sitúan a C en primer lugar y separan el estado de aceptación de los resultados negativos |
| 6-7 | `claude-quickstarts/computer-use-demo/` | 📖 | Corresponde a Anthropic Computer Use Demo, no a toda la colección de *quickstarts*: escritorio Ubuntu en contenedor y bucle de Agent con Computer Use de Claude |
| 6-8 | `browser-use/` | 📖 | *Checkout* externo de `browser-use/browser-use`; la tarea abre Google, consulta el clima de San Francisco e inspecciona la trayectoria de acciones del Agent visual |
| 6-9 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | Teleoperación del XLeRobot real para una misma tarea de ordenar el escritorio: poner la taza roja en la bandeja, el papel amarillo en el cubo de basura y volver a observar para verificar el estado |
| 6-10 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Medición en simulador del límite superior de control ideal para la misma tarea; no implica que se haya ejecutado el robot real |
| 6-11 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Gemini Robotics-ER 1.5 controla de forma autónoma el XLeRobot real para completar la misma tarea de ordenar el escritorio |
| 6-12 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Comparación en simulador de ejecución abierta, comprobación paso a paso y control cerrado predictivo para la misma tarea |
| 6-13 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | Prueba RGB entre entornos para la misma tarea, variando fondo, apariencia, iluminación y ruido visual |

## Tipos de Proyectos

| Icono | Tipo | Significado |
| :--: | --- | --- |
| ✅ | **Autónomo** | Código completo en este repositorio, se ejecuta tras configurar la Clave API |
| 📖 | **Guía de Reproducción** | Documento detallado que depende de **repositorios externos** para realizar `git clone` |
| 🚧 | **En curso** | Existe una implementación, pero faltan la ejecución real, participantes autorizados, hardware o evidencia de aceptación que exige el texto |
