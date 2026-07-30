# Capítulo 7 · Posentrenamiento de Modelos

> Tres etapas (Pre-entrenamiento/SFT/RL): cuándo elegir SFT vs. RL, internalización de llamadas a herramientas, eficiencia de muestra

← [Volver al README principal](../docs/es/README.md) · 📖 [Leer texto del capítulo](../book-es/chapter7.es.md)

## Proyectos Complementarios

| Exp. | Proyecto | Tipo | Descripción |
| :--: | --- | :--: | --- |
| 7-3, 7-4 | [MiniMind-pretrain](MiniMind-pretrain/) | 📖 | Pre-entrenamiento desde cero de LLM/VLM pequeños para comprender el proceso completo |
| 7-5 | [continued-pretraining](continued-pretraining/) | ✅ | Pre-entrenamiento continuo sobre datos de dominio específico para mejorar el rendimiento |
| 7-6 | [sesame](sesame/) | ✅ | SFT de voz Sesame CSM: ajuste LoRA de modelo TTS 1B con etiquetas paralingüísticas |
| 7-6 | [orpheus](orpheus/) | ✅ | SFT de voz Orpheus 3B: ajuste LoRA de modelo TTS para clonación de voz consistente |
| 7-7 | [MultilingualReasoning](MultilingualReasoning/) | ✅ | Entrenamiento de capacidad de razonamiento en entornos multilingües |
| 7-9 | [cot-distillation](cot-distillation/) | ✅ | Destilación de trayectorias CoT desde modelos avanzados vía OpenRouter y filtrado por reglas |
| 7-10 | [AdaptThink](AdaptThink/) | 📖 | Selección adaptativa entre Thinking/NoThinking según la dificultad del problema |
| 7-11 | `SFTvsRL/` | 📖 | Comparación sistemática entre ajuste fino supervisado y aprendizaje por refuerzo |
| 7-12 | [SpatialReasoning](SpatialReasoning/) | 📖 | Entrenamiento de capacidades de razonamiento espacial (posiciones, direcciones, distancias) |
| 7-13 | [SimpleVLA-RL](SimpleVLA-RL/) | 📖 | Aprendizaje por refuerzo visión-lenguaje-acción para ejecución de acciones físicas |
| 7-14 | [RLVP](RLVP/) | 📖 | Investigación de posentrenamiento con recompensa de resultados y penalización de trayectorias |
| 7-15 | [retool](retool/) | 📖 | Mejora del razonamiento matemático mediante diálogo multirronda y sandbox de código en dos etapas |
| 7-16 | `AWorld/` · [AWorld-train](AWorld-train/) | 📖 | Entrenamiento de Agentes encarnados basados en el marco AWorld en entornos virtuales |
| — | `verl/` | 📖 | Marco eficiente de RLHF para LLMs con soporte para PPO/GRPO/DAPO |
| — | [Intuitor](Intuitor/) | ✅ | Entrenamiento de razonamiento intuitivo rápido sin depender de cadenas de pensamiento detalladas |
| — | `tinker-cookbook/` | 📖 | Colección de trucos prácticos y mejores prácticas para entrenamiento de modelos |

## Tipos de Proyectos

| Icono | Tipo | Significado |
| :--: | --- | --- |
| ✅ | **Autónomo** | Código completo en este repositorio, se ejecuta tras configurar la Clave API |
| 📖 | **Guía de Reproducción** | Documento detallado que depende de **repositorios externos** para realizar `git clone` |
| 🚧 | **Documento de Diseño** | Solo arquitectura/plan de implementación, el código ejecutable aún está en desarrollo |
