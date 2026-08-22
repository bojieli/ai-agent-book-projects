# Capítulo 8 · Posentrenamiento de Modelos

> Cuatro partes—pre-entrenamiento, Mid-training, SFT y RL: currículo y datos de contexto largo, protocolos con SFT, entornos y recompensas de RL, y eficiencia de muestra de una a varias rondas.

← [Volver al README principal](../docs/es/README.md) · 📖 [Leer texto del capítulo](../book-es/chapter8.es.md)

Los límites de implementación, código externo y evidencia directa de cada experimento se detallan en el [registro de aceptación](EXPERIMENT_LEDGER.md).

## Cómo leer los experimentos

El texto usa skeletons breves para explicar el flujo de control; el directorio de experimentos contiene adaptadores SDK completos, registros, pruebas y evidencias de aceptación. No hace falta leer cada archivo línea por línea.

- **Starter:** Empieza por el objetivo, el comando mínimo y la aceptación; comienza con [cot-distillation](cot-distillation/);
- **Builder:** Sigue el punto de entrada, el bucle central, el esquema de estado/mensajes, las herramientas y el verificador.
- **Maintainer:** Después revisa pruebas, manifiestos, fallos, rollback y adaptadores de proveedores.

En la primera pasada puedes omitir credenciales, presentación y compatibilidad de proveedores; vuelve al reproducir una cifra.

## Proyectos Complementarios

| Exp. | Proyecto | Tipo | Descripción |
| :--: | --- | :--: | --- |
| 8-1, 8-2 | [learning-from-experience](../chapter1/learning-from-experience/) | ✅ | En el mismo entorno determinista de búsqueda del tesoro se completaron 10.000 partidas de Q-learning, 100 evaluaciones voraces y una primera ejecución oficial con Moonshot `kimi-k3`; la [evidencia de ambos brazos](../chapter1/learning-from-experience/validation/20260730_011704/evidence.json) conserva 17/17 respuestas originales de la API sin *fallback* |
| 8-3 | [MiniMind-pretrain](MiniMind-pretrain/) · `MiniMind-pretrain/minimind/` | 📖 | Documentación complementaria y código externo `bojieli/minimind` fijado a `8bdc5d9…`; el *checkout* no está presente y el entrenamiento no se ejecutó |
| 8-4 | [MiniMind-pretrain](MiniMind-pretrain/) · `MiniMind-pretrain/minimind-v/` | 📖 | Documentación complementaria y código externo `bojieli/minimind-v` fijado a `ead791c…`; el *checkout* no está presente y el entrenamiento no se ejecutó |
| 8-5 | [continued-pretraining](continued-pretraining/) | ✅ | Preentrenamiento continuo sobre datos de un dominio específico para mejorar su rendimiento |
| 8-6 | [sesame](sesame/) · [orpheus](orpheus/) | 🚧 | Dos vías reales de SFT de voz: modelado con etiquetas paralingüísticas y coherencia de timbre entre frases; se requiere el adaptador entrenado, audio y evidencia comparativa para completarlas |
| 8-7 | [MultilingualReasoning](MultilingualReasoning/) | 🚧 | Implementación de SFT de razonamiento multilingüe; se necesita un checkpoint entrenado y comparaciones antes/después en benchmarks entre idiomas |
| 8-8 | [prompt-distillation](../chapter8/prompt-distillation/) | ✅ | Implementación transversal de generación de prompts/respuestas del profesor, entrenamiento del alumno y comparación calidad-costo; generar ejemplos o prompts no basta para considerarla completa |
| 8-9 | [cot-distillation](cot-distillation/) | 🚧 | Conserva y filtra por reglas CoT reales de Kimi K3; incluye SFT del alumno sin mocks, comparación de tres brazos sobre los mismos problemas, significación pareada y validación de reflexión/retroceso, pero la máquina actual carece de un checkpoint CUDA |
| 8-10 | [documentación de AdaptThink](AdaptThink/) · `AdaptThink-original/` | 📖 | Código de entrenamiento externo de `bojieli/AdaptThink` para que el modelo elija Thinking/NoThinking según la dificultad |
| 8-11 | `SFTvsRL/` | 📖 | GeneralPoints-L/VL de `bojieli/SFTvsRL`: comparación memoria-generalización ID/OOD entre SFT y PPO con el mismo presupuesto |
| 8-12 | [documentación de SpatialReasoning](SpatialReasoning/) · `SFTvsRL/` | 📖 | Entrenamiento V-IRL-L/VL y evaluación OOD entre ciudades/reglas en el mismo *checkout* de `bojieli/SFTvsRL`; no es un repositorio SpatialReasoning independiente |
| 8-13 | [documentación de SimpleVLA-RL](SimpleVLA-RL/) · `SimpleVLA-RL/SimpleVLA-RL/` | 📖 | Repositorio `PRIME-RL/SimpleVLA-RL` y `verl/` integrado fijados; OpenVLA-OFT, LIBERO/RoboTwin, checkpoints, Flash Attention, CUDA/controlador y recursos del simulador aún no forman un bloqueo de dependencias completamente validado |
| 8-14 | [documentación de retool](retool/) · `verl/` · `SandboxFusion/` | 📖 | La receta ReTool procede de `bojieli/verl` y la ejecución de código en tiempo real depende de `bojieli/SandboxFusion`; no existe un repositorio de código independiente llamado `retool` |
| 8-15 | [documentación de AWorld-train](AWorld-train/) · `AWorld/` | 📖 | Sandbox MCP y entrada de entrenamiento de GAIA en `bojieli/AWorld`, con `bojieli/verl` como backend de entrenamiento |
| 8-16 | [documentación de RLVP](RLVP/) · `RLVP/rlvp/` | 📖 | El código completo de entrenamiento/evaluación procede de `19PINE-AI/rlvp` fijado a `1ad30bc…`; el *checkout* no está presente y el entrenamiento no se ejecutó |
| 8-17 | [premature-completion-dpo](premature-completion-dpo/) | ✅ | Reparación DPO de bad cases de finalización prematura en GPU |
| 8-18 | [curly-quote-sft](curly-quote-sft/) | ✅ | SFT auditado de comillas curvas chinas sensible al ámbito: 1.024/256/256 casos de entrenamiento/reserva/borde, 10 géneros y 9 lenguajes; Qwen3-8B alcanza 96,9%/97,7% exacto y 100% de preservación protegida en GPU |
| 8-19 | [exact-copy-sft](exact-copy-sft/) | ✅ | SFT auditado de copia byte-exacta: 1.024/256/256 casos; Qwen3-8B alcanza 78,9% en reserva y 80,1% en borde, con auditoría de tokenizadores Qwen3/Qwen2.5/Mistral |
| — | `verl/` | 📖 | Marco eficiente de RLHF para LLM compatible con PPO, GRPO, DAPO y otros algoritmos |
| — | [Intuitor](Intuitor/) | ✅ | Entrena razonamiento intuitivo para obtener decisiones plausibles con rapidez sin depender de una cadena de pensamiento detallada |
| — | `tinker-cookbook/` | 📖 | Colección de técnicas prácticas y mejores prácticas para entrenar modelos |

## Tipos de Proyectos

| Icono | Tipo | Significado |
| :--: | --- | --- |
| ✅ | **Autónomo** | Código completo en este repositorio, se ejecuta tras configurar la Clave API |
| 📖 | **Guía de Reproducción** | Documento detallado que depende de **repositorios externos** para realizar `git clone` |
| 🚧 | **En curso** | Existe una implementación, pero el entrenamiento o la evidencia de aceptación requerida por el texto aún no está completa |
