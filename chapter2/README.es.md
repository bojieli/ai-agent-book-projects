# Capítulo 2 · Ingeniería de Contexto

> El contexto limita la capacidad del Agente: KV Cache, ingeniería de prompts, Agent Skills, compresión de contexto

← [Volver al README principal](../docs/es/README.md) · 📖 [Leer texto del capítulo](../book-es/chapter2.es.md)

## Cómo leer los experimentos

El texto usa skeletons breves para explicar el flujo de control; el directorio de experimentos contiene adaptadores SDK completos, registros, pruebas y evidencias de aceptación. No hace falta leer cada archivo línea por línea.

- **Starter:** Empieza por el objetivo, el comando mínimo y la aceptación; comienza con [context-compression](context-compression/);
- **Builder:** Sigue el punto de entrada, el bucle central, el esquema de estado/mensajes, las herramientas y el verificador.
- **Maintainer:** Después revisa pruebas, manifiestos, fallos, rollback y adaptadores de proveedores.

En la primera pasada puedes omitir credenciales, presentación y compatibilidad de proveedores; vuelve al reproducir una cifra.

## Proyectos Complementarios

| Exp. | Proyecto | Tipo | Descripción |
| :--: | --- | :--: | --- |
| 2-1 | [local_llm_serving](local_llm_serving/) | ✅ | Despliegue local multiplataforma de LLM con selección automática de backend vLLM/Ollama |
| 2-2, 2-7 | [attention_visualization](attention_visualization/) | ✅ | Visualización de la secuencia completa de tokens y pesos de atención de LLM |
| 2-3 | [kv-cache](kv-cache/) | ✅ | Exploración del impacto de diferentes patrones de gestión de contexto en la eficiencia de KV Cache |
| 2-4 | [prompt-engineering](prompt-engineering/) | ✅ | Extensión de Tau-Bench para cuantificar el impacto del estilo, organización de instrucciones y descripciones de herramientas |
| 2-5 | [prompt-injection](prompt-injection/) | ✅ | Experimento comparativo de 3 escenarios de ataque × 4 configuraciones de defensa contra inyecciones de prompts |
| 2-6 | [agent-skills-ppt](agent-skills-ppt/) | ✅ | Reproducción de "divulgación progresiva" de Agent Skills para generar archivos `.pptx` con python-pptx |
| 2-7 | Experimento de texto | 🚧 | Crea un Skill de escritura ligero a partir de ejemplos personales, con condiciones de activación, reglas, ejemplos, alcance y mantenimiento iterativo. |
| 2-8 | [system-hint](system-hint/) | ✅ | Estudio del impacto de los prompts de sistema en el comportamiento del Agente |
| 2-9 | [context-compression](context-compression/) | ✅ | Comparación de estrategias de resumen, extracción de información clave y compresión semántica de contexto |

## Tipos de Proyectos

| Icono | Tipo | Significado |
| :--: | --- | --- |
| ✅ | **Autónomo** | Código completo en este repositorio, se ejecuta tras configurar la Clave API |
| 📖 | **Guía de Reproducción** | Documento detallado que depende de **repositorios externos** para realizar `git clone` |
| 🚧 | **Documento de Diseño** | Solo arquitectura/plan de implementación, el código ejecutable aún está en desarrollo |
