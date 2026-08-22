# Capítulo 9 · Auto-Evolución del Agente

> Crecimiento sin cambiar pesos: aprendizaje a partir de la experiencia, de usuario de herramientas a creador de herramientas

← [Volver al README principal](../docs/es/README.md) · 📖 [Leer texto del capítulo](../book-es/chapter9.es.md)

## Cómo leer los experimentos

El texto usa skeletons breves para explicar el flujo de control; el directorio de experimentos contiene adaptadores SDK completos, registros, pruebas y evidencias de aceptación. No hace falta leer cada archivo línea por línea.

- **Starter:** Empieza por el objetivo, el comando mínimo y la aceptación; comienza con [trajectory-verifier](trajectory-verifier/);
- **Builder:** Sigue el punto de entrada, el bucle central, el esquema de estado/mensajes, las herramientas y el verificador.
- **Maintainer:** Después revisa pruebas, manifiestos, fallos, rollback y adaptadores de proveedores.

En la primera pasada puedes omitir credenciales, presentación y compatibilidad de proveedores; vuelve al reproducir una cifra.

## Proyectos Complementarios

| Exp. | Proyecto | Tipo | Descripción |
| :--: | --- | :--: | --- |
| 8-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | Diagnóstico de trayectorias con evidencias basadas en resultados del entorno y reglas |
| 8-2 | [gaia-experience](gaia-experience/) | ✅ | Comparación de trayectorias exitosas y fallidas para generar documentación de experiencia |
| 8-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | Generación de parches mínimos de prompts a partir de trayectorias fallidas con control de versión |
| 8-4 | [browser-use-rpa](browser-use-rpa/) | ✅ | Compilación de trayectorias de navegador en flujos de trabajo con predicados de estado |
| 8-5 | [self-modifying-agent](self-modifying-agent/) | ✅ | Parches de código de reintento/disyuntor activados por fallos repetidos con regresión y despliegue |
| 8-6 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | Da a Hermes el libro y su propio código; elige una mejora, se modifica y convierte cada rechazo del Reviewer en otra ronda de aprendizaje hasta ser aceptado |
| 8-7 | [self-evolution-eval](self-evolution-eval/) | ✅ | Evaluación 8-7 de evolución a largo plazo en cuatro etapas: aprendizaje, transferencia, reglas y retención |
| 8-8 | [harness-safety-gate](harness-safety-gate/) | ✅ | Puerta de confirmación para operaciones de alto riesgo |
| 8-9 | [ai-style-skill](ai-style-skill/) | ✅ | Convierte comentarios de escritura en un Skill verificable; el capítulo conecta la Skill de comillas curvas con datos sintéticos auditados y posentrenamiento, y separa los fallos de tokenizer/Harness en la copia exacta |

## Casos Complementarios

| Exp. | Proyecto | Relación |
| :--: | --- | --- |
| 8-8 | [prompt-distillation](../chapter8/prompt-distillation/) | Proyecto cruzado de destilación de prompts y aprendizaje parametrizado (Capítulo 8) |
| — | [self-evolving-tools](self-evolving-tools/) | Descubrimiento, encapsulación y reutilización de herramientas estilo Alita |

## Tipos de Proyectos

| Icono | Tipo | Significado |
| :--: | --- | --- |
| ✅ | **Autónomo** | Código completo en este repositorio, se ejecuta tras configurar la Clave API |
| 📖 | **Guía de Reproducción** | Documento detallado que depende de **repositorios externos** para realizar `git clone` |
| 🚧 | **Documento de Diseño** | Solo arquitectura/plan de implementación, el código ejecutable aún está en desarrollo |
