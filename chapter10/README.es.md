# Capítulo 10 · Colaboración Multi-Agente

> Inteligencia colectiva > individual: marcos de colaboración, compartición/aislamiento de contexto, "Sociedad de Agentes" emergente

← [Volver al README principal](../docs/es/README.md) · 📖 [Leer texto del capítulo](../book-es/chapter10.es.md)

## Cómo leer los experimentos

El texto usa skeletons breves para explicar el flujo de control; el directorio de experimentos contiene adaptadores SDK completos, registros, pruebas y evidencias de aceptación. No hace falta leer cada archivo línea por línea.

- **Starter:** Empieza por el objetivo, el comando mínimo y la aceptación; comienza con [parallel-web-research](parallel-web-research/);
- **Builder:** Sigue el punto de entrada, el bucle central, el esquema de estado/mensajes, las herramientas y el verificador.
- **Maintainer:** Después revisa pruebas, manifiestos, fallos, rollback y adaptadores de proveedores.

En la primera pasada puedes omitir credenciales, presentación y compatibilidad de proveedores; vuelve al reproducir una cifra.

## Proyectos Complementarios

| Exp. | Proyecto | Tipo | Descripción |
| :--: | --- | :--: | --- |
| 10-1 | [multi-role-transfer](multi-role-transfer/) | ✅ | Transferencia encadenada de funciones con contexto compartido mediante `transfer_to_agent` |
| 10-2 | [book-translation](book-translation/) | ✅ | Modo administrador con Agentes especializados (glosario, traducción, revisión) y persistencia en disco |
| 10-3 | `use-computer-while-calling/` + [autonomous-phone-registration](autonomous-phone-registration/) | 📖 / 🚧 | Colaboración paralela entre Agente telefónico (Node.js) y Agente de navegador (Python) vía WebSocket (TalkAct) Están implementados y verificados el formulario real de Playwright, el Phone Agent activado de forma autónoma por un LLM, la validación, las repreguntas, el paralelismo bidireccional, la cronología desidentificada y el envío selectivo; PSTN y audio humano siguen sin ejecutarse por falta de participantes autorizados |
| 10-4 | [parallel-web-research](parallel-web-research/) | ✅ | Búsqueda paralela con N subagentes homólogos, terminación en cascada y bus de mensajes |
| 10-5 | `generative_agents/` | 📖 | Agentes generativos en el entorno "Smallville" de Stanford (código de simulación externo) |
| 10-6 | [voice-werewolf](voice-werewolf/) | 🚧 | Añade un simulador de usuario LLM real que solo ve el contexto de su asiento, debe llamar herramientas y entra únicamente mediante audio sintetizado y ASR de audio real de OpenRouter. La revalidación estricta rechazó dos ejecuciones tempranas que confundieron una mala transcripción con abstención; v2 supera E2E, aislamiento, ganador y tres ciclos, pero falla estrategia al expulsar un aldeano al vidente. |

## Tipos de Proyectos

| Icono | Tipo | Significado |
| :--: | --- | --- |
| ✅ | **Autónomo** | Código completo en este repositorio, se ejecuta tras configurar la Clave API |
| 📖 | **Guía de Reproducción** | Documento detallado que depende de **repositorios externos** para realizar `git clone` |
| 🚧 | **En curso** | La implementación o la evidencia de aceptación requerida por el experimento aún no está completa; puede existir código ejecutable, pero no debe considerarse una aceptación completa |
