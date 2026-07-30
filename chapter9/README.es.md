# Capítulo 9 · Multimodalidad e Interacción en Tiempo Real

> Extensión del texto a la voz, GUI y mundo físico: tres paradigmas de voz, Computer Use, robótica

← [Volver al README principal](../docs/es/README.md) · 📖 [Leer texto del capítulo](../book-es/chapter9.es.md)

## Proyectos Complementarios

| Exp. | Proyecto | Tipo | Descripción |
| :--: | --- | :--: | --- |
| 9-1 | [live-audio](live-audio/) | ✅ | Chat de voz en tiempo real integrando VAD + ASR + LLM + TTS mediante WebSocket de baja latencia |
| 9-2 | [phone-agent](phone-agent/) | ✅ | Agente ReAct estándar que realiza llamadas telefónicas mediante la API `make_phone_call` |
| 9-3 | [streaming-speech](streaming-speech/) | ✅ | Procesamiento de voz por bloques para ASR en streaming reduciendo la latencia del primer paquete |
| 9-4 | [end-to-end-speech](end-to-end-speech/) | ✅ | Razonamiento de voz de extremo a extremo ("escuchar → pensar → hablar") frente a modelos en cascada |
| 9-5 | [controllable-tts](controllable-tts/) | ✅ | Salida de LLM con marcadores de control (emoción, velocidad, risas) mapeados a perfiles de voz |
| 9-6 | `claude-quickstarts/` | 📖 | Ejemplos de inicio rápido y mejores prácticas con la API de Claude para diversos escenarios |
| 9-7 | `browser-use/` | 📖 | Marco de automatización de navegador impulsado por LLM para navegación y extracción de datos |

## Tipos de Proyectos

| Icono | Tipo | Significado |
| :--: | --- | --- |
| ✅ | **Autónomo** | Código completo en este repositorio, se ejecuta tras configurar la Clave API |
| 📖 | **Guía de Reproducción** | Documento detallado que depende de **repositorios externos** para realizar `git clone` |
| 🚧 | **Documento de Diseño** | Solo arquitectura/plan de implementación, el código ejecutable aún está en desarrollo |
