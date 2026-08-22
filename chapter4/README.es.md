# Capítulo 4 · Herramientas

> Las herramientas son las manos del Agente: protocolo MCP, herramientas de percepción/ejecución/colaboración, Agentes asíncronos orientados a eventos

← [Volver al README principal](../docs/es/README.md) · 📖 [Leer texto del capítulo](../book-es/chapter4.es.md)

## Cómo leer los experimentos

El texto usa skeletons breves para explicar el flujo de control; el directorio de experimentos contiene adaptadores SDK completos, registros, pruebas y evidencias de aceptación. No hace falta leer cada archivo línea por línea.

- **Starter:** Empieza por el objetivo, el comando mínimo y la aceptación; comienza con [execution-tools](execution-tools/);
- **Builder:** Sigue el punto de entrada, el bucle central, el esquema de estado/mensajes, las herramientas y el verificador.
- **Maintainer:** Después revisa pruebas, manifiestos, fallos, rollback y adaptadores de proveedores.

En la primera pasada puedes omitir credenciales, presentación y compatibilidad de proveedores; vuelve al reproducir una cifra.

## Proyectos Complementarios

| Exp. | Proyecto | Tipo | Descripción |
| :--: | --- | :--: | --- |
| 4-1 | [perception-tools](perception-tools/) | ✅ | Herramientas MCP de percepción: búsqueda web, comprensión multimodal, sistema de archivos y fuentes abiertas |
| 4-2 | [multimodal-agent](multimodal-agent/) | ✅ | Multimodal processing: compare native multimodal, extract-to-text, and tool-based analysis. |
| 4-3 | [execution-tools](execution-tools/) | ✅ | Herramientas MCP de ejecución: operaciones de archivos, intérprete de código, terminal virtual e integración externa |
| 4-4 | [collaboration-tools](collaboration-tools/) | ✅ | Herramientas MCP de colaboración: automatización de navegador, HITL, notificaciones y temporizadores |
| 4-5 | [active-tool-discovery](active-tool-discovery/) | ✅ | Comparación entre inyección completa de esquemas e inyección bajo demanda mediante meta-herramientas |
| — | [active-tool-selection](active-tool-selection/) | ✅ | Selección activa de la combinación de herramientas más adecuada según los requisitos de la tarea |

> Además, [`chapter4/docker-compose.yml`](docker-compose.yml) y [`chapter4/DOCKER_DEPLOYMENT.md`](DOCKER_DEPLOYMENT.md) proporcionan esquemas de despliegue en contenedores para los servidores MCP.

## Tipos de Proyectos

| Icono | Tipo | Significado |
| :--: | --- | --- |
| ✅ | **Autónomo** | Código completo en este repositorio, se ejecuta tras configurar la Clave API |
| 📖 | **Guía de Reproducción** | Documento detallado que depende de **repositorios externos** para realizar `git clone` |
| 🚧 | **Documento de Diseño** | Solo arquitectura/plan de implementación, el código ejecutable aún está en desarrollo |
