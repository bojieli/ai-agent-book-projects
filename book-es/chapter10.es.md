# Capítulo 10: Colaboración Multi-Agente (Multi-Agent Systems)

OpenAI propuso en su momento una escala de cinco niveles de capacidades de IA: Nivel 1, Conversadores; Nivel 2, Razonadores; Nivel 3, Agentes; Nivel 4, Innovadores; y Nivel 5, Organizaciones. La colaboración multi-agente se presenta a menudo como un camino hacia el Nivel 5. La premisa fundamental es que **la inteligencia de un grupo puede superar la de cualquier individuo**. Como señala Google DeepMind en *From AGI to ASI*, las colectividades multi-agente a gran escala son una vía clave hacia la superinteligencia (ASI).

## Marco de Clasificación para la Colaboración Multi-Agente

### Dimensión 1: Contexto Compartido vs. No Compartido

![Figura 10-1: Contexto Compartido vs. Contexto No Compartido](images/fig10-1.svg)

- **Contexto Compartido**: Un Agente posterior recibe el historial de conversación completo y la trayectoria del Agente anterior. No hay pérdida de información, pero el contexto se expande rápidamente.
- **Contexto No Compartido**: Cada Agente mantiene un contexto e historial independientes. La comunicación se realiza mediante mecanismos explícitos: parámetros de herramientas, sistema de archivos compartido o un bus de mensajes (paradigmas de memoria compartida o paso de mensajes).

Tabla 10-1 Criterios de Selección entre Contexto Compartido y No Compartido

| Criterio de Selección | Contexto Compartido | Contexto No Compartido |
|---------------|-----------------------------------|--------------------------------------------|
| Número de subtareas | Pocas (2-3 roles) | Muchas (procesamiento paralelo) |
| Ventana de contexto | Puede acomodar la información de todos | Una sola ventana es insuficiente |
| Paralelismo | Principalmente serial | Escalable masivamente en paralelo |
| Aislamiento de información | No necesario | Necesario (seguridad/privacidad) |
| Presupuesto de costo | Trayectoria única relevada por etapas | Múltiples Agentes independientes (mayor costo) |

### Dimensión 2: Topología de Colaboración

1. **Patrón de Colaboración entre Pares (Peer Collaboration)**: 2-3 Agentes interactúan como iguales en un bucle iterativo (ej. Proponente-Revisor).
2. **Patrón de Manager (Orquestación)**: Un Agente Manager central planifica y programa tareas mientras sub-agentes especializados ejecutan subtareas.
3. **Patrón Descentralizado (Choreography / Handoff)**: Sin controlador central en tiempo de ejecución; los Agentes se transfieren tareas directamente (ej. red de handoffs).

## ¿Cuándo es un Sistema Multi-Agente Realmente Mejor que un Agente Único?

El criterio central es: **¿La colaboración introduce nueva información que un Agente único no podría obtener al generar su respuesta?**

Tabla 10-2 Comparación de Ganancia de Información en Modos de Colaboración Multi-Agente

| Modo de Colaboración | ¿Introduce Nueva Información? | Efecto |
|---------------------------------------|---------------------|-----------------------------------|
| Auto-revisión del mismo modelo | No | Ineficaz o perjudicial |
| Debate entre diferentes Agentes sobre el mismo texto | No | Comparable a Agente único con igual cómputo |
| Revisor usa resultados de ejecución de código | Sí (retroalimentación de ejecución) | Mejora significativa |
| Revisor usa capturas de pantalla renderizadas | Sí (retroalimentación visual) | Mejora significativa |
| Revisor usa herramientas externas para verificar hechos | Sí (retroalimentación de herramientas) | Mejora significativa |

La consideración del presupuesto de pasos (Budget-Aware) y el costo computacional son fundamentales antes de optar por una arquitectura multi-agente.

## Colaboración Multi-Agente con Contexto Compartido

### Cambio de Rol Multietapa (Multi-Stage Role Switching)

![Figura 10-2: Cambio de rol basado en etapas](images/fig10-2.svg)

> **Experimento 10-1 ★★: Determinar Prompts del Sistema Basados en la Etapa de Ejecución (Analista de Requisitos → Ingeniero → Revisor)**

### Cambio de Rol Trans-Dominio (Cross-Domain Role Switching)

> **Experimento 10-2 ★★: Cambio Multirrol mediante transfer_to_agent**

## Colaboración Multi-Agente Sin Contexto Compartido

Tabla 10-3 Correspondencia entre Sistemas Multi-Agente y Sistemas Operativos

| Sistema Operativo | Sistema Multi-Agente |
|----------|----------------|
| Programa (ejecutable) | Prefijo estático (prompt de sistema + herramientas) |
| Memoria de proceso | Trayectoria |
| CPU | LLM |
| Kernel | Runtime del Agente |
| Llamada al sistema | Llamada a herramienta |
| fork / kill / ps | spawn_subagent / cancel_subagent / list_agents |
| Memoria compartida / Paso de mensajes | Sistema de archivos compartido / Bus de mensajes |

### El Sistema de Archivos desde la Perspectiva del Agente

Un Sistema de Archivos Virtual con cuatro áreas montadas:
1. **Workspace Específico del Agente (Scratchpad)**: Privado y temporal.
2. **Workspace Compartido Multi-Agente**: Área de colaboración visible para Agentes y usuario (ej. `/workspace/shared`).
3. **Recursos Externos Montados**: Fuentes de terceros (ej. `/mnt/gdrive`).
4. **Recursos de Sistema Integrados**: Paquetes de solo lectura (ej. `/skills`).

![Figura 10-3: Estructura de montaje del Sistema de Archivos Virtual del Agente](images/fig10-3.svg)

Tabla 10-4 Cuatro tipos de áreas del Sistema de Archivos Virtual del Agente

| Área | Visibilidad | Ciclo de Vida | Lectura/Escritura | Control de Concurrencia |
|--------------|-----------------|------------------------|---------------------|-------------------|
| Workspace Específico del Agente | Solo el Agente propietario | Destruido con la instancia | Lectura/Escritura | No necesario |
| Workspace Compartido Multi-Agente | Todos los Agentes y usuario | Persiste durante la tarea | Lectura/Escritura | Requerido (Lock optimista/Worktree) |
| Recursos Externos Montados | Según autorización externa | Determinado por fuente externa | Mayormente solo lectura | Manejado por fuente externa |
| Recursos de Sistema Integrados | Todos los Agentes | Estable entre sesiones | Solo lectura | No necesario |

### Comunicación y Control entre Agentes

1. **Paso de Mensajes**: Envoltorio JSON estructurado transmitido punto a punto o vía bus de mensajes (Redis Pub/Sub, RabbitMQ).
2. **Consulta de Estado**: Obtención de estado vía mensajes o mediante persistencia de trayectoria (archivos JSONL / WAL) y detección de bloqueos.
3. **Terminación de Ejecución**: Terminación gradual (SIGTERM) vs forzada (SIGKILL); cancelación en cascada.
4. **Gestión de Recursos y Programación**: Presupuestos de tokens, dinero y concurrencia.

### Topologías de Colaboración Sin Contexto Compartido

#### 1. Patrón de Colaboración entre Pares (Proposer-Reviewer)

![Figura 10-4: Bucle Proponente-Revisor](images/fig10-4.svg)

Ingeniería de Bucles (Loop Engineering): El cuello de botella del bucle es el verificador, no el modelo.

#### 2. Patrón de Manager (Coordinación Centralizada)

![Figura 10-5: Coordinación Secuencial del Manager](images/fig10-5.svg)

El planificador (Planner) es el cuello de botella del sistema; el modelo más fuerte debe asignarse al Manager.

> **Experimento 10-3 ★★: Agente de Traducción de Libros (Manager, Glosario, Traducción, Revisión)**
>
> ![Figura 10-6: Arquitectura del Agente de Traducción de Libros](images/fig10-6.svg)

![Figura 10-7: Coordinación Paralela del Manager](images/fig10-7.svg)

> **Experimento 10-4 ★★★: Agente Hablando por Teléfono Mientras Usa la Computadora**
>
> **Experimento 10-5 ★★★: Agentes de Teléfono y Computadora Orquestados Autónomamente**
>
> ![Figura 10-8: Arquitectura de Agente Dual Teléfono y Computadora](images/fig10-8.svg)
>
> **Experimento 10-6 ★★★: Agente Recolectando Información de Múltiples Sitios Web Simultáneamente (Terminación en Cascada)**
>
> ![Figura 10-9: Arquitectura de Web Scraping En Paralelo](images/fig10-9.svg)

#### 3. Patrón Descentralizado (Handoff entre Pares)

![Figura 10-10: Patrón de Cadena de Handoff](images/fig10-10.svg)

El paquete de handoff sin contexto compartido incluye: descripción de la tarea, hechos y restricciones confirmadas, y referencias a artefactos estructurados (rutas de archivos).

![Figura 10-11: Red de Colaboración Multi-Agente de MetaGPT](images/fig10-11.svg)

- **MetaGPT**: Basado en SOPs de desarrollo de software con pool de mensajes compartido y suscripción por rol.
- **AutoGen Group Chat**: Historial de conversación compartido con programación centralizada.
- **OpenAI Swarm / Agents SDK**: Red de handoffs punto a punto.

#### 4. Colaboración Trans-Organizacional: Protocolo A2A

El protocolo **A2A** (Agent2Agent) estandariza la interoperabilidad entre Agentes de distintas organizaciones mediante Tarjetas de Agente (Agent Cards), gestión del ciclo de vida de tareas y colaboración opaca.

## Modos de Falla de la Colaboración Multi-Agente

Taxonomía de fallas MAST (14 modos de falla). Distinción entre fallas de colapso (crash faults) y fallas bizantinas (Byzantine faults).

### Modo de Falla 1: Conflictos de Concurrencia en Sistemas de Archivos Compartidos

Conflictos simples (escrituras simultáneas) y conflictos semánticos.
Solución: **Mecanismo de Bloqueo Optimista (Optimistic Locking)** utilizando números de versión o marcas de tiempo, y aislamiento por árbol de trabajo (Git worktrees).

### Modo de Falla 2: Amplificación en Cascada de Errores

Un error inicial se propaga y refuerza a lo largo de la cadena.
Solución: Verificación cruzada (Cross-validation) e inclusión de chequeos deterministas. Prevención del bucle desbocado (Runaway loop).

## Sociedad de Agentes

![Figura 10-12: Arquitectura de AI Town](images/fig10-12.svg)

- **Stanford AI Town (Smallville)**: 25 Agentes con flujo de memoria (Memory Stream), reflexión (Reflection) y planificación. Emergencia de comportamientos sociales colectivos sin control central.
- **Agentopia**: Simulación de vida de 10 años con 100 Agentes y métrica Life Reward basada en la pirámide de Maslow.
- **Moltbook**: Red social para 1.5 millones de Agentes con emergencia de protocolos y culturas digitales.
- **Vending-Bench Arena**: Competencia económica entre Agentes operando máquinas expendedoras.
- **Pinchwork y RentAHuman**: Mercados de tareas entre Agentes y contratación de humanos.
- **Juego Estratégico en Werewolf**: Agentes jugando al Hombre Lobo bajo asimetría de información.

> **Experimento 10-8 ★★★: Sistema de Agente Hombre Lobo por Voz**
>
> ![Figura 10-13: Sistema de Agente Hombre Lobo por Voz](images/fig10-13.svg)

## Resumen del Capítulo

La colaboración multi-agente abarca arquitecturas con y sin contexto compartido, diversas topologías y patrones de sincronización inspirados en sistemas operativos. El verdadero valor surge cuando la colaboración aporta nueva información no disponible para un Agente único.

## Preguntas de Reflexión

1. ★★ En colaboración con contexto compartido, ¿cómo detectar y eliminar la interferencia de encuadre (framing bias) entre roles?
2. ★★ En el patrón Manager, ¿cómo garantizar que el Manager produzca una descomposición de tareas adecuada?
3. ★★ ¿Qué "patologías organizacionales" humanas son más probables en una sociedad de Agentes y cómo prevenirlas?
4. ★★★ Diseñe un mecanismo de terminación en cascada eficiente para el patrón Manager ("uno tiene éxito, todos se detienen").
5. ★★★ ¿Cómo diseñar una gobernanza de sistema de archivos robusta ante conflictos semánticos entre archivos y contaminación de nombres?
6. ★★★ En mercados de colaboración de Agentes (Pinchwork, RentAHuman), ¿cómo medir automáticamente la calidad del trabajo entregado y arbitrar disputas?
7. ★★ Si los Agentes contratan humanos para tareas físicas, ¿qué papel jugarán los humanos en la economía de Agentes?
8. ★★ Si los LLMs son generalistas, ¿dónde reside la verdadera ventaja de utilizar múltiples Agentes en lugar de uno solo?
9. ★★★ ¿Cómo equilibrar la eficiencia y la diversidad en un sistema multi-agente para evitar el colapso en un solo objetivo?
10. ★★★ Diseñe un mecanismo "consciente del presupuesto" (budget-aware) que adapte la estrategia de trabajo según el número de pasos asignado (30 vs 300 pasos).
11. ★★ ¿Por qué el remedio para las tres formas de terminación prematura (falso hecho, abandono prematuro, éxito falso) converge en la verificación?
12. ★★ En la correspondencia entre sistemas multi-agente y sistemas operativos (Tabla 10-3), ¿a qué corresponden la memoria virtual, los permisos de archivos y la detección de deadlocks en el mundo de los Agentes?
