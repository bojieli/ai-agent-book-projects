# Capítulo 9 · Multimodalidad e Interacción en Tiempo Real

> Extensión del texto a la voz, GUI y mundo físico: tres paradigmas de voz, Computer Use, robótica

← [Volver al README principal](../docs/es/README.md) · 📖 [Leer texto del capítulo](../book-es/chapter9.es.md)

## Proyectos Complementarios

| Exp. | Proyecto | Tipo | Descripción |
| :--: | --- | :--: | --- |
| 9-1 | [live-audio](live-audio/) | ✅ | La [evidencia real de una ronda](live-audio/backend/validation/real_pipeline_20260729_localwhisper_ark_fish/evidence.json) completa micrófono → Silero VAD → Whisper local → LLM ARK en streaming → Fish S1; los cinco hashes de medios/modelos coinciden, aunque no representa carga concurrente o de producción |
| 9-2 | [phone-agent](phone-agent/) | 🚧 | Se implementaron los brazos directo y ReAct del SDK oficial `pine-voice`, pero no hay un número E.164 autorizado con un participante que haya dado su consentimiento; la [prevalidación](phone-agent/validation/preflight.json) registra que no se marcó ni existe transcripción |
| 9-3 | [streaming-speech](streaming-speech/) | ✅ | La [aceptación local canónica](streaming-speech/validation/runs/exp9-3-qwen2audio-whisper-provenance-20260730-v3/manifest.json) ejecuta estrictamente prefijos incrementales Qwen2-Audio y VAD de 600 ms + Whisper; 8/8 puertas de ejecución y procedencia pasan, aunque los resultados solo reproducen 2/6 casos |
| 9-4 | [end-to-end-speech](end-to-end-speech/) | ✅ | MiniCPM-o 4.5, con revisión fijada, se ejecutó localmente en una RTX PRO 6000: end-to-end y self-cascade obtuvieron 3/4 con fallos semánticos/paralingüísticos complementarios; se conservaron audio real de 24kHz y evidencia de aceptación. |
| 9-5 | [controllable-tts](controllable-tts/) | ✅ | Biblioteca real Fish Audio S1 con 4×3×2=24 audios de referencia y medios A/B/C; tres evaluaciones reales ciegas y equilibradas de Voxtral sitúan a C en primer lugar y separan el estado de aceptación de los resultados negativos |
| 9-6 | `claude-quickstarts/computer-use-demo/` | 📖 | Corresponde a Anthropic Computer Use Demo, no a toda la colección de *quickstarts*: escritorio Ubuntu en contenedor y bucle de Agent con Computer Use de Claude |
| 9-7 | `browser-use/` | 📖 | *Checkout* externo de `browser-use/browser-use`; la tarea abre Google, consulta el clima de San Francisco e inspecciona la trayectoria de acciones del Agent visual |
| 9-8 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | Ruta externa de reproducción del [commit fijado de XLeRobot](https://github.com/Vector-Wangel/XLeRobot/tree/3d14695e40c9c68229c0aacffca6053c75cd3eb6) para teleoperación con teclado, Xbox, Joy-Con y VR; solo se validaron el código y una prevalidación sin actuadores |
| 9-9 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Ruta externa con [XLeRobot fijado](https://github.com/Vector-Wangel/XLeRobot/tree/3d14695e40c9c68229c0aacffca6053c75cd3eb6) y [RoboCrew v0.3.1 fijado](https://github.com/Grigorij-Dudnik/RoboCrew/tree/c749148f29bd14e61347f9fc3530c343fff0d994), usando estrictamente `gemini-robotics-er-1.5-preview`, anotaciones angulares y tres herramientas de movimiento |
| 9-10 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | Ruta externa del flujo RGB→PPO→SO-100 de cinco etapas del [commit fijado de `lerobot-sim2real`](https://github.com/StoneT2000/lerobot-sim2real/tree/87d6c1d969f6e0ca4dc5697940804e231118a63a); las etapas 3–4 pueden ejecutarse solo con GPU, mientras que la etapa 1 reinicia el robot real |

## Tipos de Proyectos

| Icono | Tipo | Significado |
| :--: | --- | --- |
| ✅ | **Autónomo** | Código completo en este repositorio, se ejecuta tras configurar la Clave API |
| 📖 | **Guía de Reproducción** | Documento detallado que depende de **repositorios externos** para realizar `git clone` |
| 🚧 | **En curso** | Existe una implementación, pero faltan la ejecución real, participantes autorizados, hardware o evidencia de aceptación que exige el texto |
