# Capítulo 3 · Memoria de Usuario y Base de Conocimiento

> Memoria de usuario entre sesiones y conocimiento externo: memoria de usuario, RAG, índices estructurados, grafos de conocimiento

← [Volver al README principal](../docs/es/README.md) · 📖 [Leer texto del capítulo](../book-es/chapter3.es.md)

## Proyectos Complementarios

| Exp. | Proyecto | Tipo | Descripción |
| :--: | --- | :--: | --- |
| 3-1, 3-2 | [user-memory](user-memory/) | ✅ | Sistema de memoria de usuario a largo plazo para recordar preferencias e interacciones históricas |
| 3-1 | [user-memory-evaluation](user-memory-evaluation/) | ✅ | Evaluación sistemática de la precisión, relevancia y efectividad del sistema de memoria de usuario |
| 3-2 | [mem0](mem0/) · [memobase](memobase/) | ✅ | Implementaciones de referencia de memoria de usuario utilizando los marcos de código abierto mem0 y Memobase |
| 3-3 | [log-sanitization](log-sanitization/) | ✅ | Sistema inteligente de sanitización de registros para proteger datos sensibles manteniendo la información de depuración |
| 3-4 | [dense-embedding](dense-embedding/) | ✅ | Servicio de búsqueda por similitud vectorial comparando algoritmos ANN (ANNOY y HNSW) |
| 3-5 | [sparse-embedding](sparse-embedding/) | ✅ | Motor de búsqueda de vectores dispersos basado en BM25 construido desde cero |
| 3-6 | [retrieval-pipeline](retrieval-pipeline/) | ✅ | Pipeline completo de recuperación densa + dispersa + reordenamiento neuronal |
| 3-7 | [structured-index](structured-index/) | ✅ | Comparación de índices estructurados RAPTOR (árbol de abstracción recursiva) y GraphRAG (grafo de conocimiento) |
| 3-8 | [agentic-rag](agentic-rag/) | ✅ | Comparación entre RAG no agente y RAG agente iterativo guiado por ReAct |
| 3-9 | [agentic-rag-for-user-memory](agentic-rag-for-user-memory/) | ✅ | Gestión del historial de conversaciones del usuario mediante Agentic RAG |
| 3-10 | [contextual-retrieval](contextual-retrieval/) | ✅ | Recuperación sensible al contexto de Anthropic generando resúmenes de prefijo para fragmentos |
| 3-11 | [contextual-retrieval-for-user-memory](contextual-retrieval-for-user-memory/) | ✅ | Estructura de memoria de dos capas combinando JSON Cards avanzadas y RAG sensible al contexto |
| 3-12 | [structured-knowledge-extraction](structured-knowledge-extraction/) | ✅ | Extracción de conocimiento estructurado en tres etapas: descubrimiento de factores, prototipos y recomendaciones |

## Tipos de Proyectos

| Icono | Tipo | Significado |
| :--: | --- | --- |
| ✅ | **Autónomo** | Código completo en este repositorio, se ejecuta tras configurar la Clave API |
| 📖 | **Guía de Reproducción** | Documento detallado que depende de **repositorios externos** para realizar `git clone` |
| 🚧 | **Documento de Diseño** | Solo arquitectura/plan de implementación, el código ejecutable aún está en desarrollo |
