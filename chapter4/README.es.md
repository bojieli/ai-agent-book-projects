# Capítulo 4 · Herramientas

> Las herramientas son las manos del Agente: protocolo MCP, herramientas de percepción/ejecución/colaboración, Agentes asíncronos orientados a eventos

← [Volver al README principal](../docs/es/README.md) · 📖 [Leer texto del capítulo](../book-es/chapter4.es.md)

## Proyectos Complementarios

| Exp. | Proyecto | Tipo | Descripción |
| :--: | --- | :--: | --- |
| 4-1 | [perception-tools](perception-tools/) | ✅ | Herramientas MCP de percepción: búsqueda web, comprensión multimodal, sistema de archivos y fuentes abiertas |
| 4-2 | [multimodal-agent](multimodal-agent/) | ✅ | Multimodal processing: compare native multimodal, extract-to-text, and tool-based analysis. |
| 4-3 | [execution-tools](execution-tools/) | ✅ | Herramientas MCP de ejecución: operaciones de archivos, intérprete de código, terminal virtual e integración externa |
| 4-4 | [collaboration-tools](collaboration-tools/) | ✅ | Herramientas MCP de colaboración: automatización de navegador, HITL, notificaciones y temporizadores |
| 4-5 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | Agente FastAPI orientado a eventos con integración asíncrona de herramientas MCP |
| 4-6 | [async-agent](async-agent/) | ✅ | Marco Flux orientado a eventos asíncronos monohilo con colas por prioridad e interrupción |
| 4-7 | [active-tool-discovery](active-tool-discovery/) | ✅ | Comparación entre inyección completa de esquemas e inyección bajo demanda mediante meta-herramientas |
| — | [active-tool-selection](active-tool-selection/) | ✅ | Selección activa de la combinación de herramientas más adecuada según los requisitos de la tarea |

> Además, [`chapter4/docker-compose.yml`](docker-compose.yml) y [`chapter4/DOCKER_DEPLOYMENT.md`](DOCKER_DEPLOYMENT.md) proporcionan esquemas de despliegue en contenedores para los servidores MCP.

## Tipos de Proyectos

| Icono | Tipo | Significado |
| :--: | --- | --- |
| ✅ | **Autónomo** | Código completo en este repositorio, se ejecuta tras configurar la Clave API |
| 📖 | **Guía de Reproducción** | Documento detallado que depende de **repositorios externos** para realizar `git clone` |
| 🚧 | **Documento de Diseño** | Solo arquitectura/plan de implementación, el código ejecutable aún está en desarrollo |
