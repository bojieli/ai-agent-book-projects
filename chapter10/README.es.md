# Capítulo 10 · Colaboración Multi-Agente

> Inteligencia colectiva > individual: marcos de colaboración, compartición/aislamiento de contexto, "Sociedad de Agentes" emergente

← [Volver al README principal](../docs/es/README.md) · 📖 [Leer texto del capítulo](../book-es/chapter10.es.md)

## Proyectos Complementarios

| Exp. | Proyecto | Tipo | Descripción |
| :--: | --- | :--: | --- |
| 10-1 | [staged-system-prompt](staged-system-prompt/) | ✅ | Coding Agent por etapas (aclaración, implementación, revisión) con prompts y herramientas independientes |
| 10-2 | [multi-role-transfer](multi-role-transfer/) | ✅ | Transferencia encadenada de funciones con contexto compartido mediante `transfer_to_agent` |
| 10-3 | [book-translation](book-translation/) | ✅ | Modo administrador con Agentes especializados (glosario, traducción, revisión) y persistencia en disco |
| 10-4 | `use-computer-while-calling/` | 📖 | Colaboración paralela entre Agente telefónico (Node.js) y Agente de navegador (Python) vía WebSocket (TalkAct) |
| 10-5 | [autonomous-phone-registration](autonomous-phone-registration/) | 🚧 | Están implementados y verificados el formulario real de Playwright, el Phone Agent activado de forma autónoma por un LLM, la validación, las repreguntas, el paralelismo bidireccional, la cronología desidentificada y el envío selectivo; PSTN y audio humano siguen sin ejecutarse por falta de participantes autorizados |
| 10-6 | [parallel-web-research](parallel-web-research/) | ✅ | Búsqueda paralela con N subagentes homólogos, terminación en cascada y bus de mensajes |
| 10-7 | `generative_agents/` | 📖 | Agentes generativos en el entorno "Smallville" de Stanford (código de simulación externo) |
| 10-8 | [voice-werewolf](voice-werewolf/) | 🚧 | Se implementaron las puertas para 6–8 jugadores, roles exactos, asientos humanos, ASR/TTS e interrupciones, tres rondas, victoria, estrategia y aislamiento; sin participantes autorizados y con cuota de Audio API insuficiente, la aceptación permanece incompleta |

## Tipos de Proyectos

| Icono | Tipo | Significado |
| :--: | --- | --- |
| ✅ | **Autónomo** | Código completo en este repositorio, se ejecuta tras configurar la Clave API |
| 📖 | **Guía de Reproducción** | Documento detallado que depende de **repositorios externos** para realizar `git clone` |
| 🚧 | **En curso** | La implementación o la evidencia de aceptación requerida por el experimento aún no está completa; puede existir código ejecutable, pero no debe considerarse una aceptación completa |
