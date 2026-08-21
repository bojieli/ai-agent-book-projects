# Capítulo 1 · Fundamentos de los Agentes de IA

> **Agente = LLM + Contexto + Herramientas**; La ingeniería del Harness es la verdadera ventaja competitiva

← [Volver al README principal](../docs/es/README.md) · 📖 [Leer texto del capítulo](../book-es/chapter1.es.md)

## Cómo leer los experimentos

El texto usa skeletons breves para explicar el flujo de control; el directorio de experimentos contiene adaptadores SDK completos, registros, pruebas y evidencias de aceptación. No hace falta leer cada archivo línea por línea.

- **Starter:** Empieza por el objetivo, el comando mínimo y la aceptación; comienza con [context](context/);
- **Builder:** Sigue el punto de entrada, el bucle central, el esquema de estado/mensajes, las herramientas y el verificador.
- **Maintainer:** Después revisa pruebas, manifiestos, fallos, rollback y adaptadores de proveedores.

En la primera pasada puedes omitir credenciales, presentación y compatibilidad de proveedores; vuelve al reproducir una cifra.

## Proyectos Complementarios

| Exp. | Proyecto | Tipo | Descripción |
| :--: | --- | :--: | --- |
| 1-1 | [context](context/) | ✅ | Experimentos de ablación sistemática que muestran la importancia de los componentes del contexto; compatible con SiliconFlow Qwen, ByteDance Doubao y Moonshot Kimi |
| 1-2 | [web-search-agent](web-search-agent/) | ✅ | Agente Kimi K3 con capacidad de búsqueda profunda básica, capaz de realizar búsquedas multirronda e integración de información |
| 1-3 | [search-codegen](search-codegen/) | ✅ | Integración de herramientas nativas de GPT-5, utilizando búsqueda web y sandbox de código para análisis complejos |
| 1-4 | [image-gen-workflow](image-gen-workflow/) | ✅ | Comparación real de dos clases de necesidades (concretas/amplias) × dos rutas, workflow (reescritura con kimi-k3 + Tongyi Wanxiang) y nativa (Gemini / GPT-Image 2): con necesidades concretas la ruta nativa es más fiel (el nodo de reescritura envió el texto del cartel a los prompts negativos); con necesidades amplias la concreción de la escena mediante la reescritura aporta imaginación, pero GPT-Image 2 ya aporta ideas por sí mismo—evidencia empírica de la internalización de la capa de adaptación por el modelo |
| 7-1, 7-2 | [learning-from-experience](learning-from-experience/) | ✅ | Comparación entre Q-learning tradicional y aprendizaje en contexto basado en LLM, reproduciendo la eficiencia de muestra (250–400x) |

## Tipos de Proyectos

| Icono | Tipo | Significado |
| :--: | --- | --- |
| ✅ | **Autónomo** | Código completo en este repositorio, se ejecuta tras configurar la Clave API |
| 📖 | **Guía de Reproducción** | Documento detallado que depende de **repositorios externos** para realizar `git clone` |
| 🚧 | **Documento de Diseño** | Solo arquitectura/plan de implementación, el código ejecutable aún está en desarrollo |
