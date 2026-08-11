# Multimodalidad e Interacción en Tiempo Real

Los capítulos anteriores exploraron el diseño de Agentes en el mundo del texto (interactuando con sistemas digitales a través del contexto, herramientas y código). Sin embargo, los objetos de interacción de un Agente no son solo texto y API. Cuando un Agente necesita comprender las instrucciones habladas de un usuario, encontrar y hacer clic en el botón correcto en la pantalla, o controlar un brazo robótico para agarrar con precisión un objeto, entra en un terreno completamente nuevo: la **interacción multimodal en tiempo real** (pasando de la entrada y salida de texto puro a la **percepción multimodal y respuesta en tiempo real**), lo que constituye un paso crucial para que el Agente salga del "cuadro de diálogo". La llamada "multimodalidad" consiste en procesar simultáneamente múltiples formas de información (texto, voz, imágenes, video, acciones) y no solo texto.

Delimitemos primero las fronteras de este capítulo. La comprensión estática de imágenes y documentos (mirar una captura de pantalla, leer un gráfico, analizar un PDF) ya se ha integrado de forma natural en la práctica de los Agentes de los capítulos anteriores como herramientas de percepción: para los grandes modelos multimodales de hoy en día, este tipo de tareas de "una entrada, una comprensión" son relativamente maduras y no requieren un diseño de arquitectura especial. Este capítulo se centra en otro tipo de problemas: tres escenarios en los que **la naturaleza de tiempo real vuelve complejo el problema multimodal**: diálogo por voz, operación de GUI y control robótico. En estos escenarios, la entrada fluye de manera continua y la salida debe entregarse dentro de un presupuesto de tiempo estricto, lo que provoca un cambio cualitativo en el diseño de la arquitectura. En cuanto a la comprensión en tiempo real de flujos de visión continua (video), al momento de escribir este libro sigue siendo un problema abierto para los Agentes (la sección de Computer Use de este capítulo discutirá las limitaciones de las capturas fotograma a fotograma, y las preguntas de reflexión al final del capítulo volverán a este tema). También debemos trazar otra frontera: la **generación** multimodal (generación de imágenes, generación de video) en el marco de este libro es simplemente una llamada a una herramienta ordinaria (ya abordada en el Capítulo 5 sobre generación multimedia); el Agente la utiliza como una herramienta externa y no involucra los desafíos de interacción en tiempo real que se resuelven en este capítulo, por lo que no está dentro de la línea principal.

La interacción por voz, Computer Use y las operaciones robóticas parecen abarcar tres dominios completamente diferentes, pero al llevarlos a la práctica se descubre que los puntos de atasco son altamente similares: en todos ellos se debe procesar simultáneamente información de múltiples modalidades y todos son extremadamente sensibles a la latencia. Una pausa en la voz de más de dos segundos causa ansiedad en las personas, mientras que las fluctuaciones de milisegundos en el control robótico pueden causar colisiones. Estas dos restricciones impulsan colectivamente a los tres escenarios hacia la misma dirección arquitectónica: pasar de **pipelines seriales** (donde, como en una cadena de montaje de una fábrica, una etapa debe completarse antes de entregarla a la siguiente) a **modelos de extremo a extremo** (un modelo unificado pasa directamente de la entrada a la salida, eliminando las etapas intermedias de traspaso).

Este capítulo se desarrolla a través del siguiente hilo conductor:

1. En primer lugar, se establece un sistema de coordenadas utilizando los "Tres paradigmas de las arquitecturas de voz": cascada (pipeline VAD-ASR-LLM-TTS), omnimodal de extremo a extremo (Omni, un solo modelo pero donde aún se habla por turnos) y full-duplex (Moshi, GPT-Live, escuchando y hablando al mismo tiempo). Se desglosará la latencia y los compromisos de cada etapa a lo largo del eje de "cómo librarse de la suposición de turnos de VAD". En la sección de cascada también se explicará cómo sustituir VAD + ASR por percepción de voz en streaming.
2. A continuación, se examina cómo las arquitecturas de pensamiento concilian la contradicción entre la "respuesta en tiempo real" y el "pensamiento profundo": desde el paralelismo simple entre rápido y lento, pasando por la ruta de desacoplamiento donde un modelo de razonamiento en segundo plano actúa como "asesor" (delegación en GPT-Live, Pine AI, etc.), hasta la "charla mientras piensa" de Step-Audio R1 que "internaliza" el pensamiento dentro de un solo modelo.
3. Luego se discute la optimización de la capa de ejecución mediante una síntesis de voz más humana.
4. Finalmente, se amplía la perspectiva a Computer Use (hacer que la IA opere la pantalla de una computadora como un ser humano) y a la manipulación robótica, para observar cómo se manifiestan estos mismos problemas de latencia y multimodalidad en ambos escenarios.

Entre ellos, cabe destacar especialmente dos puntos de carácter más teórico y transferibles entre escenarios: las **arquitecturas de pensamiento** (cómo colaboran los dos sistemas de pensamiento, rápido y lento) y la **interfaz rápido-lento** derivada de ella (Latent Bridge, qué más se puede transmitir entre modelos rápidos y lentos además de texto). Aunque se introducen a partir del escenario de voz, no sirven únicamente para la voz: Computer Use y la robótica encontrarán más adelante la misma cuestión de "cuándo se debe consultar a un asesor lento", algo a lo que el lector debe prestar especial atención.

## Voz: la interfaz humano-máquina más natural

La voz no es solo convertir texto en sonido. Hablar es aproximadamente cuatro veces más rápido que escribir y deja libres las manos y la mirada, por lo que encaja naturalmente a un Agente en un bucle continuo que puede ser interrumpido en cualquier momento. La entrada de voz convierte el dictado en texto; un Agente de voz permite colaborar directamente con él. Ambos sostienen el whisper coding presentado en la introducción.

Esta sección cubre dos direcciones: el usuario habla con el Agente y el Agente habla con el mundo exterior en nombre del usuario. El modelo de voz determina qué puede responder; la arquitectura de interacción determina si escucha bien, responde a tiempo, cede el turno de forma natural y completa confirmaciones y llamadas a herramientas durante una llamada.

### Tiempo de interacción: de la cascada al dúplex completo

La introducción de GPT-Live de OpenAI resume tres paradigmas: cascada, basado en turnos y dúplex completo[^ch9-12]. Son intercambios distintos entre latencia, coste y observabilidad, no una sustitución lineal.

| Paradigma | Estructura | Ventaja | Limitación |
| --- | --- | --- | --- |
| Cascada | VAD → ASR → LLM → TTS | Módulos claros, intercambiables y depurables | Se acumula la latencia y se pierde información paralingüística |
| Omni de extremo a extremo | Un modelo escucha, piensa y habla | Menor latencia y preservación de tono, emoción y ambiente | Sigue dependiendo de turnos; entrenar y depurar cuesta más |
| Dúplex completo | Escucha, habla y decide continuamente | Habla solapada, interrupción natural y flujo continuo | Entrenamiento, control y evaluación más complejos |

El hilo común es escapar de la suposición de que hay que hablar por turnos y de la conjetura de VAD sobre quién tiene la palabra. Cascada y Omni aún dividen la interacción en turnos; el dúplex completo convierte esa decisión en una salida continua del modelo.

[^ch9-12]: OpenAI. *Introducing GPT-Live.* 2026-07-08. https://openai.com/index/introducing-gpt-live/ . La clasificación procede del resumen de las tres generaciones de ChatGPT Voice; «end-to-end omnimodal (Omni)» corresponde a «turn-based voice models».

**Cancelación en streaming:**

```python
while audio_is_arriving:
    partial = asr.push(audio_chunk)
    if endpoint_is_probable(partial):
        candidate = llm.start(partial)
        if later_audio_changes_meaning(partial):
            cancel(candidate)                 # speculative cancellation
        else:
            tts.enqueue_stable_segments(candidate)

on_final_transcript(text):
    commit_or_restart(text)
```

### Paradigma 1 · Pipeline en cascada

La mayoría de asistentes comerciales todavía usa un pipeline serial (Figura 9-1): VAD detecta el final, ASR convierte audio en texto, el LLM entiende y genera la respuesta, y TTS la pronuncia. La modularidad facilita optimizar cada componente, pero cada frontera añade espera.

![Figura 9-1: Pipeline serial de un Agente de voz](images/fig9-1.svg)

| Módulo | Función | Cuello de botella |
| --- | --- | --- |
| VAD | Decidir si terminó el habla | Umbral de silencio, espera y segmentación errónea |
| ASR | Audio a texto | Latencia y pérdida de contexto |
| LLM | Comprender, razonar y generar | Latencia del primer token y espera adicional con reasoning |
| TTS | Texto a voz | Síntesis del primer paquete y búfer de reproducción |

En una respuesta breve, las esperas de VAD, ASR, LLM y TTS se acumulan en serie (Figura 9-2). La cola de producción amplifica aún más la latencia en vacío (Figura 9-3).

![Figura 9-2: Cascada de latencia de una respuesta serial](images/fig9-2.svg)

![Figura 9-3: Curva de latencia de cola](images/fig9-3.svg)

> **Experimento 9-1 ★: Construir un Agente de voz tradicional**
>
> Conecta micrófono, Silero VAD, Whisper local, LLM en streaming y Fish S1 TTS por WebSocket. La evidencia real de un turno demuestra que la cadena funciona de extremo a extremo, pero no es un benchmark de concurrencia ni de carga de producción. Código y aceptación: [chapter9/live-audio](../chapter9/live-audio/).

> **Proyecto adicional: un Agente de voz WebRTC que «llama al usuario»**
>
> PSTN no es imprescindible. WebRTC en el navegador reproduce el ciclo de abrir una sesión, pedir datos faltantes, repetirlos para confirmar y guardar resultados estructurados. Para llamar a una organización externa se sustituye el mismo contrato por un proveedor PSTN/SIP conforme. El proyecto conserva los identificadores históricos exp9-2, pero ya no ocupa un número del manuscrito. Véanse [chapter9/phone-agent](../chapter9/phone-agent/) y sus evidencias.

#### De lo serial a la percepción en streaming

ASR puede emitir una transcripción provisional mientras se habla, el LLM puede enviar la primera frase pronunciable a TTS y TTS puede devolver bloques de audio. Eso no hace que las tres etapas sean completamente paralelas: la generación anticipada exige cancelar, invalidar, reiniciar o revertir cuando cambia la transcripción.

El frente VAD + ASR acumula latencia por esperar silencio, pierde dudas, emoción, apoyos y ambiente, y rompe el contexto de nombres o correos. Un modelo realmente streaming necesita codificador causal o por bloques y decodificación incremental; Whisper no es causal porque su codificador espera el segmento completo. Un modelo auditivo basado en LLM puede emitir texto y eventos semánticos, pero simular prefijos no garantiza el rendimiento de un modelo causal. Los marcadores speak_start/end, interrupt, emotion, laugh, sigh y noise conservan señales que no caben en texto.

[^ch9-11]: Sobre incorporar el juicio de turno al reconocedor y el problema de etiquetas con información futura, véase Li, Bojie and Noah Shi. *The Trade-off Was in the Labels: Causal Supervision for Turn-Aware Streaming ASR.* 2026 (pendiente de publicación).

> **Experimento 9-2 ★: Simular percepción de voz en streaming con Qwen2-Audio**
>
> Qwen2-Audio no es un modelo streaming: se usan prefijos de audio crecientes y se compara con 600 ms de VAD + Whisper. El canonical run pasó los controles, pero solo reprodujo 2/6 conductas; tardó 8,4–11,3 s, omitió silence en pause y confundió cough/laughter en noise. Es una prueba de mecanismos y fallos, no evidencia de percepción streaming de 100–200 ms. Registro: [chapter9/streaming-speech](../chapter9/streaming-speech/).

### Paradigma 2 · Modelos omnimodales de extremo a extremo (Omni)

La cascada pierde emoción, entonación y sonido ambiente en la interfaz textual. Omni escucha, genera y habla con un único modelo, pero cuesta más entrenarlo, depurarlo y sustituir componentes. Su ventaja principal es la latencia y la información no textual, no una precisión necesariamente mayor. La autocascada puede corregir un error de percepción cuando el texto basta; si la respuesta depende de velocidad, emoción o ambiente, el cuello de botella textual destruye la evidencia[^ch9-13]. Omni todavía supone turnos y puede confundir una pausa en una secuencia de números con el final.

[^ch9-13]: Medición completa de cuándo se invierte la ventaja de precisión entre cascada y extremo a extremo: Li, Bojie and Noah Shi. *The Cascade Gap: When and Why Self-Cascades Help Multimodal Agents.* 2026 (pendiente de publicación).

![Figura 9-4: Comparación de modelos de voz omnimodales](images/fig9-4.svg)

Las API de voz en tiempo real ocupan una posición intermedia: procesan audio de forma nativa, pero conservan VAD, interrupciones y llamadas asíncronas a herramientas. Lo importante es comparar los fallos por tarea, no una tabla de posiciones.

> **Experimento 9-3 ★★: Ejecutar MiniCPM-o 4.5 localmente, extremo a extremo frente a autocascada**
>
> Fija una revisión local, desactiva thinking mode y compara responder directamente al audio con transcribir primero y responder después. Mide la conservación de información acústica, no la capacidad posterior de «pensar mientras habla».
>
> | Tarea | Extremo a extremo | Autocascada | Observación |
> | --- | ---: | ---: | --- |
> | Aritmética semántica (2) | 1/2 | 2/2 | La autocascada corrigió un error de transcripción |
> | Velocidad paralingüística (2) | 2/2 | 1/2 | El texto borró la diferencia rápido/lento |
> | Total | 3/4 | 3/4 | Mismo total, fallos complementarios |
>
> La muestra es pequeña; no establece qué ruta es generalmente más precisa o rápida. Evidencia completa: [chapter9/end-to-end-speech](../chapter9/end-to-end-speech/).

Step-Audio 2 procesa audio crudo y produce texto y voz; Step-Audio R1 incorpora el razonamiento en el modelo de audio.

### Paradigma 3 · Modelos interactivos de dúplex completo

Omni separa «habla el usuario» y «habla el modelo», pero la interpretación simultánea exige solapamiento. Un modelo de dúplex completo escucha y habla continuamente y decide seguir, pausar, interrumpir o llamar a una herramienta. Moshi de Kyutai fue un ejemplo temprano; Thinking Machines Lab llama a esta ruta Interaction Model[^ch9-14] y la integra en el modelo en lugar de montarla alrededor de VAD. GPT-Live la lleva a escala de producción y delega el trabajo complejo a un modelo de fondo mientras mantiene la conversación.

[^ch9-14]: Thinking Machines Lab, “Interaction Models: A Scalable Approach to Human-AI Collaboration,” 2026-05. https://thinkingmachines.ai/blog/interaction-models/

La trayectoria es: la cascada adivina turnos con umbrales de silencio, el streaming eleva el juicio al nivel semántico y el dúplex completo convierte el cambio de turno en una decisión continua.

### Tiempo cognitivo: interacción en tiempo real y pensamiento profundo

El modelo de primer plano responde mientras el usuario sigue conectado; el modelo de fondo puede pensar más tiempo. Son tres intercambios, no una progresión lineal:

| Diseño | Primer plano | Fondo | Riesgo |
| --- | --- | --- | --- |
| Respuesta rápida, corrección lenta | Respuesta inmediata | Replantear y completar | Contradicción |
| Interacción rápida, consejo lento | Mantener el hilo y elegir palabras | Consejo o resultados de herramientas | Interfaz limitada |
| Pensamiento y expresión unidos | Pensar mientras habla | Compartir el estado | Alto coste de entrenamiento |

La primera solución duplica el trabajo y puede contradecirse; la segunda comunica consejos de forma indirecta y no ve el razonamiento intermedio; la tercera integra ambos procesos. Step-Audio R1 usa MGRD para anclar el razonamiento en rasgos acústicos y una arquitectura MPS de dos cerebros para producir pensamiento y voz en paralelo. El modelo unificado es más natural, pero requiere reentrenar pensamiento y expresión juntos; el desacoplado permite cambiar el cerebro de fondo (Figuras 9-5 y 9-6).

### Síntesis de voz más humana

Un TTS demasiado fluido y sin pausas delata que es una máquina. El LLM puede emitir THINKING, EMO:happy y SPEED:0.8x junto con el texto, y TTS puede convertirlos en pausas, prosodia, velocidad, risas y suspiros. En Fish Audio S1, la configuración con varias referencias obtuvo la mejor puntuación en tres escuchas ciegas equilibradas (4,67/5 en parecido a un agente humano), pero el grupo sin marcadores superó al de referencia única y no se reprodujo todo el orden previsto.

> **Experimento 9-4 ★★: TTS controlado por tokens con Fish Audio**
>
> Compara biblioteca sin marcadores, una referencia y varias referencias; la capa de ejecución selecciona emoción, velocidad y estilo. La biblioteca de 24 referencias, los medios A/B/C y la aceptación están en [chapter9/controllable-tts](../chapter9/controllable-tts/).

## Computer Use: Agentes de automatización de GUI

Al llegar a este punto, el lector habrá notado que el espacio dedicado a la voz en este capítulo es notablemente superior al de los dos escenarios posteriores, lo cual es intencionado. En la línea evolutiva de la multimodalidad en tiempo real, la voz es el escenario que se ha desarrollado de manera más completa y que más merece tomarse como sistema de referencia: partiendo del problema de "la alta latencia del pipeline serial", pasando por soluciones como extremo a extremo, full-duplex y pensar mientras se habla, hasta llegar a la situación consolidada de hoy, todo el recorrido de problema → solución → situación final se ha completado. Por ello lo explicamos en profundidad, de modo que los dos escenarios siguientes, Computer Use y robótica, puedan examinarse en comparación con este marco de referencia: para ver en qué punto de esta línea evolutiva se encuentra cada uno y dónde se han atascado.

Aunque estos tres escenarios parecen diferentes, enfrentan los mismos desafíos centrales: percepción en tiempo real, toma de decisiones con baja latencia e interacción continua. A continuación veremos cómo reaparecen estos temas técnicos en la interacción visual (Computer Use) y la interacción física (robótica); comenzando por ampliar la perspectiva de la modalidad auditiva a la visual: ¿qué ocurre si el Agente no solo puede comprender la voz, sino también "entender" la pantalla y operar interfaces gráficas de usuario?

Computer Use (también llamado Agente de automatización de GUI) permite a la IA utilizar software como los humanos, observando la pantalla y operando el ratón y el teclado; por ejemplo, abrir el navegador para buscar información, rellenar datos en una hoja de cálculo o ajustar la configuración del sistema. Su núcleo es un bucle de **Percepción-Pensamiento-Acción** (Figura 9-6):

1. El Agente toma una captura de la pantalla actual.
2. El modelo multimodal recibe la captura y la instrucción de la tarea, emitiendo un fragmento de pensamiento y una acción específica.
3. La capa de ejecución ejecuta dicha acción en el entorno real (mover el ratón, hacer clic, ingresar texto, etc.).
4. Espera la respuesta de la interfaz y vuelve a tomar una captura de pantalla, entrando en la siguiente ronda del bucle.

**Bucle de seguridad de Computer Use:**

```python
observation = capture_screenshot_and_accessibility_tree()
proposal = model.decide(task, observation)
action = validate_schema_and_coordinates(proposal)

if action.is_irreversible and not user_or_policy_approval(action):
    stop("approval required")
else:
    execute_in_sandbox_or_scoped_session(action)
    new_observation = capture_after_settle()
    if not verify_goal_progress(new_observation, action):
        rollback_if_possible_or_replan()
```

![Figura 9-6: Bucle Percibir-Pensar-Actuar de Agentes Computer Use](images/fig9-7.svg)

Existen tres dimensiones de diseño clave en este bucle: el **espacio de acciones** (qué operaciones puede ejecutar el Agente), el **grounding visual** (cómo encontrar el elemento objetivo en la captura de pantalla) y la **arquitectura del modelo** (cómo generar la acción correcta a partir de la captura de pantalla).

### Diseño del espacio de acciones

Anthropic define tres categorías de herramientas que constituyen la capacidad de interacción completa (Figura 9-7):

![Figura 9-7: Espacio de acciones de Computer Use](images/fig9-8.svg)

**Herramientas de operación de GUI** (`computer tool`): Las operaciones de ratón incluyen movimiento (`mouse_move`), clic con botón izquierdo/derecho/central, doble clic/triple clic, arrastre (`left_click_drag`), así como presionar/soltar con mayor precisión (`left_mouse_down/up`). El desplazamiento (`scroll`) admite cuatro direcciones y se puede combinar con teclas modificadoras. Las operaciones de teclado incluyen escritura carácter por carácter (`type`, simulando la escritura real con un intervalo de 12 ms entre caracteres), combinaciones de teclas (`key`, como Ctrl+C) y pulsación prolongada (`hold_key`). Acciones de percepción: captura de pantalla (`screenshot`), obtención de la posición del cursor (`cursor_position`) y espera (`wait`).

**Herramientas de ejecución de comandos** (`bash tool`): Proporciona una sesión de terminal bash persistente con un tiempo de espera de 120 segundos, detectando si la ejecución del comando ha finalizado mediante cadenas centinela y manteniendo el estado del entorno entre múltiples llamadas (por ejemplo, si se hace `cd` a un directorio, la siguiente llamada permanecerá en ese directorio).

**Herramientas de edición de archivos** (`str_replace_editor`): Logra una edición segura mediante coincidencia de cadenas, admitiendo operaciones de visualización, creación, reemplazo, inserción y deshacer, siendo más preciso que sobrescribir el archivo completo y reduciendo la probabilidad de modificar involuntariamente otros contenidos.

> **Experimento 9-5 ★: Ejecutar Computer Use (ruta de referencia de Anthropic o ruta de modelo abierto)**
>
> La ruta A utiliza la demo de Anthropic Computer Use. Su contenedor empaqueta un entorno de escritorio Ubuntu completo, con navegador, terminal y otras herramientas habituales. El frontend recibe la tarea; el backend envía las instrucciones y capturas de pantalla a Claude y luego ejecuta las acciones de ratón, teclado, terminal o edición que devuelve el modelo. Esta ruta sirve para comprender el protocolo nativo de la herramienta `computer`; no exige que todos los lectores tengan acceso a la API de Anthropic.
>
> La ruta B utiliza el proyecto complementario del libro [`chapter9/computer-use-open-model`](../chapter9/computer-use-open-model/). Por defecto controla browser-use con el modelo de pesos abiertos Qwen3-VL 32B Instruct, ya sea mediante la API alojada de OpenRouter o apuntando `OPEN_MODEL_BASE_URL` a un vLLM/SGLang autoalojado u otro endpoint compatible. El endpoint debe aceptar capturas de pantalla y admitir JSON Schema nativo; si solo admite JSON ordinario, se puede activar explícitamente el modo de compatibilidad schema-in-prompt.
>
> Ambas rutas emplean la misma tarea de solo lectura y el mismo contrato de aceptación: un máximo de 25 pasos, una sola acción por paso, y conservación de la identidad del modelo/endpoint, las respuestas originales del proveedor, las capturas de cada paso, la secuencia de acciones, la respuesta final y el motivo de detención. Los modelos distintos deben informarse como brazos experimentales separados: no se puede presentar el resultado de un modelo abierto como una reproducción de Claude ni considerar que «el contenedor arrancó correctamente» equivale a completar la tarea. El intervalo entre acciones y la calidad de la planificación son resultados medidos; no se presupone que sean de 2–5 segundos ni que superen necesariamente a otros modelos.

### Grounding visual (Visual Grounding)

En cada ronda del bucle, el modelo necesita localizar con precisión el elemento objetivo en la captura de pantalla: "¿Dónde está la casilla de búsqueda?", "¿Cuáles son las coordenadas del botón de envío?". Este es el problema de grounding visual (Visual Grounding). Actualmente existen **dos enfoques principales**: el primero convierte la localización en una **pregunta de opción múltiple** (etiquetando previamente los elementos de la interfaz con números para que el modelo solo tenga que elegir uno); el segundo es la **predicción directa de coordenadas** (permitiendo que el modelo "mire" directamente la captura de pantalla e informe las coordenadas como haría un humano). El enfoque de opción múltiple tiene dos formas de implementación: **anotación puramente visual** (el Set-of-Mark original, utilizando modelos de segmentación para recortar regiones candidatas sobre los píxeles) e **indexación de elementos estructurados** (DOM/Accessibility Tree, leyendo directamente la estructura interna de la interfaz). La ventaja común del enfoque de opción múltiple es que transforma la tarea abierta de "encontrar el botón en la captura de pantalla y predecir las coordenadas" en una tarea cerrada de "elegir uno entre los elementos ya etiquetados" (al igual que en un examen las preguntas de opción múltiple son más fáciles de responder correctamente que las de rellenar espacios), donde el modelo solo necesita decir "hacer clic en [123]" en lugar de "hacer clic en el botón azul situado aproximadamente a 200 píxeles a la derecha de la esquina superior izquierda de la pantalla".

**Set-of-Mark: Método de anotación visual.**

El Set-of-Mark (SoM) original fue propuesto por Microsoft Research en 2023, inicialmente para liberar la capacidad de localización visual de GPT-4V. Es un método **puramente visual**: utiliza modelos de segmentación de imágenes (SAM, SEEM, etc.) para recortar automáticamente regiones candidatas en la captura de pantalla, superponiendo marcas numéricas en cada región; el modelo ve una imagen con números y solo necesita informar el número, que el sistema convierte en las coordenadas centrales de la región correspondiente. Todo el proceso no requiere DOM ni ninguna estructura interna de la interfaz, por lo que el software de escritorio nativo y las interfaces de juegos son igualmente aplicables, siempre que el modelo de segmentación pueda recortar las regiones candidatas.

**Indexación de elementos estructurados: Implementación estructurada de la idea SoM en la Web.**

Cuando la propia interfaz puede proporcionar información estructurada, las anotaciones se pueden realizar con mayor precisión. Las páginas web modernas ya definen la estructura completa de los elementos (árbol DOM) y los roles semánticos (cuál es un botón, cuál es una casilla de entrada) antes de renderizar, y las interfaces de accesibilidad (Accessibility Tree) proporcionan información similar para muchas aplicaciones de escritorio. En lugar de dejar que el modelo de segmentación adivine entre los píxeles "qué región es un botón", es mejor preguntar directamente a la propia interfaz "¿qué elementos interactivos tienes?". Las soluciones de Web Agent representadas por el proyecto `browser-use` funcionan precisamente de esta manera: enumeran y numeran los elementos interactivos desde el DOM, lo que puede considerarse una implementación estructurada de la idea SoM en la Web (Figura 9-8). El flujo consta de cuatro pasos:

1. Obtener la representación estructurada de la página web (árbol DOM) y la información de accesibilidad a través de la interfaz de depuración del navegador (CDP, Chrome DevTools Protocol).
2. Detectar automáticamente qué elementos son interactivos (botones, casillas de entrada, enlaces, etc.).
3. Etiquetar un ID único para cada elemento interactivo y dibujar cuadros delimitadores en la captura de pantalla.
4. Generar simultáneamente una lista de texto que describa el elemento correspondiente a cada ID.

```text
Screenshot: [en la imagen los elementos clave están etiquetados con ID como [1], [2], [3], [4]]

Elements:
[1] <input type="text" placeholder="Search" aria-label="Search" />
[2] <button id="submit-btn" aria-label="Submit form" />
[3] <input type="text" placeholder="Enter your name" value="" />
[4] <a href="/docs" aria-label="Documentation" />
```

El modelo solo necesita emitir un número de ID, y el sistema ejecuta automáticamente el clic utilizando las coordenadas centrales de dicho elemento. Este tipo de solución no ahorra tokens (porque toda la información de anotación debe enviarse al modelo), pero la localización es precisa y estable, evitando además las omisiones y falsas detecciones que los modelos de segmentación podrían introducir.

![Figura 9-8: Set-of-Mark vs indexación de elementos estructurados (implementación browser-use)](images/fig9-9.svg)

**Predicción directa de coordenadas.**

La tercera ruta no realiza ninguna anotación y permite que el modelo emita las coordenadas directamente. Representada por **SeeClick** y el computer use de Claude: se entrena un modelo visual con datos emparejados de capturas de pantalla de GUI y posiciones de elementos a gran escala, permitiéndole aprender a mapear descripciones en lenguaje natural (como "hacer clic en el botón de envío") directamente a coordenadas precisas en la captura de pantalla, al igual que un usuario humano que confía puramente en la "vista" para encontrar la posición donde hacer clic.

En la solución de predicción de coordenadas, la comprensión de las coordenadas por parte del modelo depende en gran medida de la resolución utilizada durante el entrenamiento (Figura 9-9). El entrenamiento de Claude utiliza XGA (1024x768), WXGA (1280x800) y FWXGA (1366x768); si la resolución de la captura de pantalla de entrada no coincide, las coordenadas predichas por el modelo se desviarán sistemáticamente, como si se midiera una distancia en un mapa pequeño y se aplicara directamente a un mapa grande. Por lo tanto, es necesario implementar un mecanismo de escalado bidireccional de coordenadas en la capa de herramientas, debiendo **seleccionar la resolución objetivo según la relación de aspecto de ancho y alto**, evitando que un estiramiento no proporcional deforme la imagen e introduzca desvíos en el juicio de coordenadas. Por ejemplo, si la resolución real de la pantalla es de 2560×1440 (16:9), se debe seleccionar entre las tres opciones admitidas por Claude aquella cuya relación de aspecto sea más cercana a 16:9: FWXGA (1366×768) es la más adecuada. Al tomar la captura de pantalla, la pantalla se escala proporcionalmente a 1366×768 para enviarla al modelo; tras emitir el modelo las coordenadas de clic (683, 384), se mapean de forma inversa a las coordenadas reales (683×2560/1366, 384×1440/768) ≈ (1280, 720). Por el contrario, si se fuerza el estiramiento de 16:9 a 1024×768 (4:3), la imagen se aplastará horizontalmente y las coordenadas predichas por el modelo sufrirán una desviación sistemática.

![Figura 9-9: Coincidencia de resolución y escalado bidireccional de coordenadas](images/fig9-10.svg)

La lógica de elección entre las tres rutas se puede resumir de la siguiente manera: **cuando la información estructurada esté disponible, se priorizará el uso del índice DOM/Accessibility Tree**, ya que la localización es la más precisa y estable; **cuando no esté disponible** (software de escritorio nativo como Photoshop, interfaces renderizadas en Canvas/WebGL, juegos), **se puede utilizar tanto la anotación visual (ruta SoM original) como la predicción de coordenadas**. La anotación visual convierte la localización en una pregunta de opción múltiple, siendo más amigable para modelos generales no entrenados específicamente; la predicción de coordenadas omite el paso de anotación y es más directa para modelos entrenados en localización de GUI. La precisión de ambas en elementos pequeños e interfaces densas aún presenta brechas.

> **Experimento 9-6 ★: Uso de browser-use para implementar operaciones automatizadas en el navegador**
>
> Se combina Playwright, un framework de automatización de navegadores, con un modelo multimodal para implementar operaciones de navegador dirigidas mediante lenguaje natural. Se activa la visualización SoM y se guarda antes de cada decisión una captura con cuadros delimitadores anotados. La interfaz del modelo no se limita a OpenAI ni Anthropic: el libro ofrece una configuración de API para el modelo abierto Qwen3-VL y conserva un base URL genérico compatible con OpenAI para otros servicios alojados o para inferencia autoalojada.
>
> Tarea de prueba «Abrir Google y consultar el tiempo en San Francisco»: tras iniciar el sistema, una captura muestra la página de búsqueda de Google con los elementos interactivos numerados. El modelo selecciona el cuadro de búsqueda, escribe "San Francisco weather today", envía la búsqueda y extrae la temperatura y las condiciones de la página de resultados. Durante la aceptación se verifican de forma independiente la respuesta y la trayectoria, y se registran fielmente el número real de pasos y el tiempo transcurrido. «5 pasos y unos 20 segundos» solo puede ser una observación de una ejecución concreta, no un resultado fijo sin comprobante de ejecución.
>
> La ejecución oficial preservada del modelo abierto utilizó `qwen/qwen3-vl-32b-instruct` en OpenRouter. Al encontrar un CAPTCHA en la búsqueda de Google en el paso 4, el modelo no afirmó haber terminado: cambió a weather.com y, en el paso 16, leyó en la página Today de San Francisco 64°F, Sunny, sensación térmica de 62°F, máxima de 74°F y mínima de 55°F. Las 16 respuestas de API informaron del modelo Qwen3-VL solicitado, y las 15 capturas válidas de los pasos junto con la trayectoria de acciones de solo lectura superaron una aceptación determinista independiente. Este resultado demuestra que la ruta de API del modelo abierto funciona; no significa que se haya reproducido el brazo que usa la herramienta `computer` nativa de Anthropic.

### Agentes de Computer Use capaces de ver animaciones y escuchar audio

Hasta ahora, la percepción de Computer Use se ha basado en una suposición implícita: **la pantalla está estática** (tomar una captura, pensar un paso, hacer clic, y luego tomar la siguiente captura). Sin embargo, en la realidad las pantallas reproducen videos, muestran notificaciones fugaces y reproducen las voces de las personas en las reuniones. Un Agente que solo abre los ojos una vez cada 3-5 segundos y carece por completo de oídos es incapaz de ver o escuchar "lo que sucede entre dos fotogramas". Ver grabaciones de pantalla, seguir reuniones, escuchar avisos de voz o responder a cuadros de diálogo que parpadean rápidamente: toda esta categoría de operaciones cotidianas en computadoras es casi una zona prohibida para los Agentes de Computer Use de hoy en día.

Lo que realmente debe rediseñarse aquí no es la "interfaz de acción", sino la **"interfaz de observación"** [^ch9-9]. La idea central es desacoplar la **observación** (continua, adaptativa, multimodal) de la **acción** (discreta), convirtiéndola en una capa de middleware de percepción que se inserta entre el entorno y cualquier modelo de Computer Use existente sin necesidad de reentrenamiento (pudiendo denominarse Interfaz de Observación Agente-Computadora, AOI). Consta de tres componentes que "abren la compuerta según la demanda": en primer lugar, la **captura de fotogramas clave entre fotogramas** (utilizando primero una puerta de píxeles extremadamente económica para omitir imágenes casi sin cambios, y luego un modelo pequeño para juzgar si la imagen ha sufrido cambios significativos, tomando capturas solo ante cambios, con costo casi nulo en imágenes estáticas); en segundo lugar, la **transcripción de voz controlada por puerta de volumen** (llamando al reconocimiento de voz solo cuando hay sonido, permitiendo al Agente "desarrollar oídos" por primera vez); y en tercer lugar, lo más crítico, **narrar la imagen en texto persistente** (haciendo que el modelo describa los fotogramas capturados en una frase como "la notificación recién mostrada dice que la fecha de lanzamiento cambió al 28 de abril", y **aunque la imagen original se limpie posteriormente del contexto, esta frase de texto permanece en la memoria**, llevando la información dinámica hacia adelante en forma de texto).

Un hallazgo contraintuitivo es que lo que realmente funciona no es "qué fotogramas seleccionar", sino **"narrar los fotogramas como texto que se pueda conservar a largo plazo"**: el texto es precisamente la modalidad que mejor manejan los LLM Agent. En ocho modelos que van desde 7B hasta la escala de vanguardia, este middleware aportó una mejora de +17 a +48 puntos porcentuales sin necesidad de reentrenamiento alguno, siendo la brecha en las tareas de voz la más drástica: con esta capa de percepción añadida, el Agente pudo realizar tareas de voz que originalmente "escuchaba pero no podía ejecutar". Sin embargo, tampoco se trata de una configuración fija universal: en algunos modelos más recientes, añadir demasiados tokens de imagen desplaza al razonamiento y perjudica el rendimiento, por lo que estos componentes deben **seleccionarse modelo por modelo**, en lugar de activarlos todos de golpe. Esto sigue la misma lógica que la elección entre Set-of-Mark y predicción de coordenadas explicada anteriormente: no existe una bala de plata en las soluciones de percepción, y es necesario configurarlas según las características específicas del modelo.

[^ch9-9]: Los detalles de los fotogramas clave controlados por puerta, la transcripción a pedido y la narración de fotogramas en texto persistente, así como la mecánica completa y las ablaciones por modelo, se encuentran en Li, Bojie y Noah Shi. *Agent-Computer Observation Interfaces Enable Dynamic Computer Use.* arXiv:2606.29472, 2026.

### Modelos del mundo para Computer Use

La interfaz de observación responde a «¿qué ocurrió entre dos capturas?» haciendo que los cambios dinámicos lleguen antes y queden en memoria. No elimina el coste de planificación: el Agente puede seguir repitiendo «captura, piensa, clic» y reconsiderar tras cada acción. OSWorld-Human muestra que una precisión de nivel humano puede requerir muchos más pasos y esperas.

Las personas operan el escritorio de forma predictiva: anticipan el efecto y, si el estado coincide con la predicción, continúan sin replantear. Solo una discrepancia devuelve el sistema a observación y planificación. Es ejecución especulativa; **un modelo del mundo resuelve la otra mitad del problema** al predecir el siguiente estado, continuar cuando coincide y replantear o detenerse cuando no.

### Dispositivos móviles: Las barreras del ecosistema superan a los desafíos técnicos

Computer Use también se está expandiendo hacia los dispositivos móviles. Existen diferencias técnicas reales entre los dispositivos móviles y los de escritorio: el espacio de acciones ya no suele ser "coordenadas del ratón + teclado", sino que se conecta a las API de servicios de accesibilidad del sistema (como AccessibilityService en Android) para leer los elementos de la interfaz y emitir clics e ingreso de texto; el modo de interacción pasa de un puntero de ratón a gestos táctiles, y la semántica de las coordenadas cambia en consecuencia (si un mismo $(x, y)$ corresponde a un toque simple, una pulsación larga o el punto inicial de un gesto de deslizamiento requiere tipos de gestos adicionales para delimitarse). Los benchmarks para móviles como AndroidWorld presentados en el Capítulo 6 evalúan precisamente la capacidad del Agente para completar tareas reales en App sobre este espacio de acciones.

Sin embargo, lo que suele atascar a los dispositivos móviles no son estas diferencias técnicas, sino las barreras del ecosistema. Algunos fabricantes de teléfonos móviles intentaron integrar asistentes de IA en teléfonos de consumo para operar automáticamente aplicaciones cotidianas como WeChat, Taobao y Alipay, pero rápidamente encontraron restricciones por parte de las plataformas.

Esto revela un desafío único al que se enfrenta Computer Use: las **barreras del ecosistema**. La razón fundamental detrás de los bloqueos es el conflicto de modelos de negocio. La lógica de monetización central de las aplicaciones de internet tradicionales es el **tráfico y la atención**: los usuarios ven anuncios al revisar flujos de información, siguen la guía de los algoritmos de recomendación al buscar productos y generan compras impulsivas al navegar por las páginas. Sin embargo, cuando el Agente opera en lugar del usuario, esta cadena de monetización se elude por completo: la IA no presta atención a los anuncios ni realiza compras impulsivas, dirigiéndose directamente al objetivo para completar la tarea e irse. Para las plataformas que monetizan mediante anuncios y tráfico, cada operación del Agente erosiona la base de su modelo de negocio.

Esto significa que Computer Use no solo se enfrenta a enfrentamientos a nivel técnico como los CAPTCHA (códigos de verificación), sino a un **conflicto de intereses estructural**. Esta contradicción es difícil de conciliar a corto plazo, lo que hace que la implantación de Computer Use en escenarios de consumo enfrente desafíos más complejos que los puramente técnicos.

### Tiempo real: El desafío central aún sin resolver

**OSWorld** (cuya metodología de evaluación se detalló en el Capítulo 6) es un benchmark de evaluación de Computer Use ampliamente utilizado que prueba la capacidad del Agente para completar tareas entre aplicaciones en entornos reales de Ubuntu/Windows/macOS. La tasa de éxito de los primeros modelos generales en este benchmark era de solo un 20% aproximadamente; los modelos dedicados posteriores y los modelos generales más potentes han continuado elevando la precisión, acercándose gradualmente al nivel humano al momento de escribir este libro. Sin embargo, la precisión dista mucho de ser el final: el verdadero cuello de botella ha pasado de "¿puede hacerlo bien?" a "¿puede hacerlo rápido?".

El estudio de eficiencia de **OSWorld-Human** reveló una realidad cruda: incluso si la tarea tiene éxito al final, los pasos de operación necesarios para que el Agente complete la misma tarea siguen siendo notablemente superiores a los de los humanos, y la latencia de inferencia de cada paso continúa creciendo a medida que avanza la tarea (cuanto más largo es el contexto, más lenta es la decisión del modelo, siendo el tiempo consumido en los pasos finales a menudo muy superior al de las etapas iniciales). Un ajuste de formato de documento que un humano completaría en decenas de segundos puede llevarle al Agente varios minutos de titubeo. **Que la precisión alcance el nivel humano no equivale a practicidad: la eficiencia es el verdadero cuello de botella.**

La causa raíz del problema de eficiencia es similar a la del escenario de voz: en el bucle serial de "captura-pensamiento-clic", incluso si cada etapa se optimiza al límite, la latencia acumulada paso a paso sigue siendo inaceptable. Un problema más profundo es que el Computer Use actual carece por completo de la capacidad de "pensar por adelantado". Si el Agente pudiera predecir el siguiente paso que debe realizar mientras ejecuta la acción actual (por ejemplo, pensar dónde hacer clic a continuación mientras espera que se cargue la página), se podrían superponer los tiempos de pensamiento y ejecución, reduciendo drásticamente la latencia total (esta es la misma exigencia que el "pensar mientras se habla" en el escenario de voz anterior y el Agente asíncrono de "pensamiento continuo" del Capítulo 4, solo que aquí se convierte en "pensar mientras se opera").

A diferencia del campo de la voz, la naturaleza de tiempo real propia de Computer Use (acelerar el propio bucle de "captura-pensamiento-clic") no cuenta actualmente con una solución sistemática, manteniéndose en el bucle discreto de capturas fotograma a fotograma. Sin embargo, una vía para eludirlo ya se ha completado, utilizando precisamente el desacoplamiento rápido-lento que reaparece a lo largo de este capítulo: dado que acelerar al lento Agente de operación de computadora es difícil, **no se debe hacer esperar al usuario por él**. Se dividen la "charla" y la "operación de la computadora" en dos modelos concurrentes, rápido y lento [^ch9-10]: un modelo pequeño (rápido) se encarga del diálogo por voz en tiempo real, mientras que un VLM de vanguardia (lento) opera paso a paso en el navegador, comunicándose ambos a través de un "contrato de texto puro" muy simple: cada vez que el Agente lento realiza una operación, adjunta un resumen de estado actualizado en desplazamiento ("Rellenando el formulario, aún se necesita su fecha de nacimiento"), el Agente rápido responde en tiempo real al usuario basándose en esto y le transmite la nueva información dada verbalmente por el usuario al Agente lento, y **hasta que el resumen de estado confirme la finalización, el Agente rápido no tiene permitido decir 'está listo'**. Este es precisamente el escenario de "hablar por teléfono mientras se deja que la computadora opere sola". En los experimentos, este desacoplamiento hizo que la respuesta de voz fuera aproximadamente 15 veces más rápida que en el caso de "un solo modelo hablando mientras opera" (latencia mediana de 0.58 s vs 8.64 s), sin reducir la tasa de éxito de la tarea; en cuanto se retiró ese canal de texto entre rápido y lento, la tasa de éxito colapsó instantáneamente a 0, ya que la información clave dada verbalmente por el usuario no podía transmitirse al navegador. Esta es la misma idea que el Latent Bridge anterior y el "pensar mientras se habla" en el escenario de voz: cuando un componente es lento por naturaleza, se permite que otro componente rápido llene la espera del usuario (solo que ese "contrato de texto puro" es en esencia el Agent Status Bar del que se ha hablado desde el Capítulo 2). La aceleración del propio bucle de Computer Use seguirá siendo quizás una dirección de investigación importante a futuro, pero "ocultar lo 'lento' mediante el desacoplamiento rápido-lento" se ha convertido en una respuesta utilizable.

[^ch9-10]: El diseño completo del desacoplamiento rápido-lento entre voz y operación y el "contrato de texto puro" se encuentra en Li, Bojie y Noah Shi. *Talking While Acting: Real-Time Voice for Slow Computer-Use Agents.* 2026 (pendiente de publicación).

## Operación robótica: Del control en tiempo real al entrenamiento y la generalización

> **Los cinco experimentos de esta sección usan una única tarea: poner la taza roja en la bandeja, poner el papel amarillo en el cubo de residuos y volver a observar para verificar el estado del escritorio. El brazo real y el simulador se informan por separado, pero comparten la semántica de acciones y las condiciones de éxito.**
>
Los Agentes de voz enfrentan la latencia en la modalidad auditiva, Computer Use enfrenta la latencia en la modalidad visual, y cuando el Agente necesita controlar robots en el mundo físico, los desafíos de latencia y multimodalidad se amplifican aún más: las consecuencias de las acciones son irreversibles, y una sola colisión puede dañar los objetos o al propio robot. Esta sección examina primero cómo los robots reducen el problema del control en tiempo real mediante arquitecturas de dos capas y Action Chunking, para pasar luego a su escollo más duro en la actualidad: el entrenamiento y la generalización (cómo se obtienen los datos y cómo migra el modelo entre tareas y plataformas).

### El hardware no es el cuello de botella, los algoritmos sí lo son

Los robots aún no se han aplicado ampliamente en escenarios abiertos generales. ¿El cuello de botella está en el hardware o en los algoritmos? El proyecto XLeRobot ofrece una contraprueba contundente: un robot de dos brazos sobre ruedas con un costo inferior a 1,000 dólares puede completar con fluidez una gran cantidad de tareas domésticas cuando los humanos lo teleoperan a través de visores VR. Tareas domésticas más complejas que requieren manos diestras también pueden ser completadas con fluidez por los robots de Unitree bajo teleoperación humana. La latencia de la teleoperación es de aproximadamente 100-200 ms, cercana a las exigencias de respuesta de la interacción física. La resolución de los sensores, la precisión de los actuadores y la frecuencia de control (el número de veces por segundo que el robot actualiza las instrucciones de acción; cuanto menor es la frecuencia, menos fluido es el movimiento y más probable es que aparezcan vibraciones o desvíos de la trayectoria objetivo) en las plataformas de bajo costo actuales ya son suficientes para respaldar tareas prácticas.

Es necesario delimitar las fronteras de esta afirmación: lo que la contraprueba de la teleoperación demuestra realmente es que "el hardware actual de bajo costo sumado a la inteligencia humana es suficiente para completar **este tipo de tareas de manipulación doméstica basadas principalmente en retroalimentación visual**". Esto no significa que el hardware cumpla en todas las dimensiones: la falta de sensores táctiles y la confiabilidad y costo de las manos diestras siguen siendo deficiencias de hardware reconocidas hasta el día de hoy; una vez que la tarea depende en gran medida del control preciso de fuerzas y la retroalimentación táctil, el hardware puede ser un cuello de botella. Por lo tanto, lo que se indica a continuación sobre "el hardware no es el cuello de botella" se limita al alcance de las tareas discutidas en esta sección.

En lo que respecta a este tipo de tareas, la verdadera brecha se encuentra en la capa algorítmica, la cual se desarrolla en las dos subsecciones siguientes.

> **Experimento 9-7 ★: Teleoperar XLeRobot para ordenar el escritorio**
>
> **Objetivo:** En un XLeRobot real, un operador remoto ejecuta la misma tarea y verifica de nuevo el escritorio.
>
> **Principio:** Un brazo de unos cientos de dólares puede completar esta tarea de varios pasos bajo teleoperación humana; aquí el cuerpo del hardware no es el cuello de botella, sino la percepción, la planificación, el control cerrado y la recuperación.
>
### Arquitectura de dos capas: Separación de planificación y control

Para que un robot complete tareas domésticas complejas, debe tomar decisiones en dos escalas temporales diferentes. La primera capa es la **planificación de largo alcance** (long-horizon planning), más lenta: desglosa instrucciones de alto nivel como "limpiar la escritorio" en secuencias de subobjetivos (limpiar el mostrador, cargar el lavavajillas, limpiar las superficies), requiriendo comprender la semántica del entorno, razonar sobre las dependencias de la tarea y planificar esquemas de acción multipaso (al igual que un humano piensa "qué hacer primero y qué hacer después" antes de ponerse a trabajar). La segunda capa es el **control VLA** (Vision-Language-Action, modelo de Visión-Lenguaje-Acción), más rápido: ejecuta cada operación específica ("caminar hacia el fregadero", "tomar el trapo", "limpiar la superficie"), emitiendo continuamente señales de control basadas en la imagen actual que ve y las instrucciones de lenguaje, para que los movimientos del robot sean fluidos y continuos.

Esta arquitectura de dos capas separa eficazmente la complejidad: la planificación de largo alcance se encarga de "qué hacer" y el control VLA se encarga de "cómo hacerlo". Esta arquitectura de dos capas de "toma de decisiones lenta de alto nivel + ejecución rápida de nivel inferior" es altamente similar en estructura al "pensamiento rápido/lento" en el escenario de voz anterior: ambas desacoplan el pensamiento complejo y la respuesta en tiempo real en diferentes módulos. Cabe recordar que la "planificación / control" aquí se corresponde con el desacoplamiento de la dimensión "pensamiento profundo lento / respuesta en tiempo real rápida" en el pensamiento rápido/lento, y no con el desacoplamiento de "pensamiento / expresión" de MPS Solución 3 (este último divide "pensar" y "hablar", mientras que el primero divide "planificación global" y "ejecución en tiempo real", cortando dimensiones diferentes).

Sin embargo, la naturaleza de tiempo real no desaparece mágicamente, sino que se desplaza hacia abajo a la capa de control VLA, amortiguándose mediante la **fragmentación de acciones** (Action Chunking, véase la sección posterior "Control VLA"): el modelo genera en una sola inferencia una secuencia corta de acciones futuras, y el hilo de control la reproduce a alta frecuencia, diluyendo la latencia de una sola inferencia a lo largo del tiempo de ejecución de todo el bloque de acciones. Sin embargo, aquí hay un compromiso ineludible: la fragmentación intercambia reactividad por suavidad. Cuanto más largo es el bloque, más se diluye la latencia de cada inferencia y más continuo es el movimiento, pero el modelo "no ve" nuevas imágenes durante ese tiempo, volviéndose más lento ante cambios repentinos (si se mueve un objeto o alguien extiende la mano para bloquear). Este compromiso entre tiempo real y suavidad es la parte que la arquitectura de dos capas no elimina, sino que simplemente desplaza.

Aquí también es necesario explicar un giro en la línea principal de este capítulo: en el escenario robótico, la contradicción en tiempo real ya se ha mitigar parcialmente mediante el desacoplamiento de dos capas y la fragmentación de acciones, desplazándose la contradicción principal actual hacia el **entrenamiento y la generalización** (cómo obtener suficientes datos de demostración y cómo hacer que el modelo generalice entre tareas y plataformas). Las subsecciones siguientes se desarrollan en torno a esta nueva contradicción, siendo también la extensión al mundo físico de los entornos de simulación del Capítulo 6 y del aprendizaje por refuerzo del Capítulo 7.

Y esta nueva contradicción recae principalmente sobre la capa de control VLA. Se puede considerar VLA como "VLM + salida de acciones": el **VLM** (Vision-Language Model, modelo de visión-lenguaje: un gran modelo que comprende imágenes y texto simultáneamente) se encarga de "entender" y "pensar con claridad", y el VLA además debe "manos a la obra" sobre esta base, residiendo el verdadero desafío precisamente en esta capa de "manos a la obra". Actualmente, la capa de control VLA se entrena principalmente mediante aprendizaje por imitación (clonación de comportamiento): aprendiendo directamente de un gran número de demostraciones humanas "qué hacer al ver qué" (OpenVLA, RT-2, π₀, etc. pertenecen a esta categoría); el aprendizaje por refuerzo ha sido un medio complementario sobre esto en los últimos años. Aunque los VLA entrenados con aprendizaje por refuerzo pueden funcionar muy bien en tareas individuales, a menudo carecen de capacidad de generalización: incluso si SimpleVLA-RL en el Capítulo 7 reportó resultados elevados en tareas individuales en LIBERO, se entrenó con RL por separado para cada tarea, en lugar de ser un modelo unificado que generalice con cero muestras a todas las tareas. Este patrón de "entrenar una vez por cada tarea" significa que cada vez que se encuentra una nueva tarea, se deben volver a recopilar datos y reentrenar.

Las dos secciones siguientes discuten en profundidad las soluciones técnicas específicas para la planificación de largo alcance y el control VLA.

### Planificación de largo alcance: De VLM a modelos de pensamiento embrollado dedicados

Los VLM generales ya poseen una capacidad notable de pensamiento embrollado. **Gemini Robotics-ER 1.5** de Google DeepMind se optimizó específicamente para el pensamiento embrollado (Embodied Reasoning, es decir, comprender la posición, movimiento y relaciones causales de los objetos en el mundo físico), alcanzando un promedio de 62.8% en 15 benchmarks académicos (Point-Bench, RefSpatial, RoboSpatial, BLINK, etc.), superando a GPT-4o (60.6%) y Gemini 2.5 Pro (59.3%). Sus ventajas centrales incluyen: comprensión espacial avanzada y localización de objetos, razonamiento temporal (predecir causalidades de acciones como "qué pasará si empujo este vaso") y orquestación de tareas (descomponer instrucciones de alto nivel en pequeños pasos), admitiendo de forma nativa mecanismos de pensamiento (thinking) y llamadas a herramientas [^ch9-2].

[^ch9-2]: Google DeepMind, “Gemini Robotics-ER 1.5”. https://deepmind.google/models/gemini-robotics/gemini-robotics-er/

> **Experimento 9-8 ★: Medir en simulación el límite de control ideal de la misma tarea**
>
> **Objetivo:** Ejecutar la misma tarea con un controlador ideal que no comete errores de percepción ni de elección.
>
> **Principio:** Esta referencia mide el límite cuando las decisiones son correctas; no demuestra que el brazo real haya ejecutado la tarea.
>

> **Experimento 9-9 ★★: Control autónomo de un XLeRobot real con Gemini Robotics-ER 1.5**
>
> **Objetivo:** Sustituir al operador por un Agente que observa y llama a habilidades acotadas de recoger, colocar y verificar, manteniendo la misma tarea y criterio de éxito.
>
> **Principio:** La diferencia está en percepción, planificación, temporización, control cerrado y recuperación, no en una nueva limitación mecánica.
>

### Control VLA: De datos de demostración a la generalización entre distintos cuerpos

En la capa de ejecución de la arquitectura de dos capas, tres modelos representativos (RT-2, OpenVLA y π₀) se enfocan en el control VLA, es decir, emitir las acciones del robot en tiempo real basándose en las imágenes de las cámaras y las instrucciones de lenguaje (Figura 9-10). Pertenecen a dos rutas en cuanto a la representación de las acciones: tokens de acción discretos y generación de trayectorias continuas.

![Figura 9-10: Arquitectura VLA (Vision-Language-Action)](images/fig9-11.svg)

**RT-2 y OpenVLA: Ruta de tokens de acción discretos.**

**RT-2** fue el pionero de esta ruta: realiza un ajuste fino directo sobre grandes modelos de visión-lenguaje, discretizando las acciones continuas del robot en tokens que se emiten de forma autorregresiva uno a uno como si fuera generación de texto, aprovechando la capacidad de generalización del modelo preentrenado para mejorar la transferencia zero-shot a nuevos objetos e instrucciones. **OpenVLA** sigue el esquema de representación de acciones de RT-2, unificando el modelo de lenguaje y el codificador visual en una sola arquitectura, recibiendo imágenes e instrucciones de texto para emitir tokens de acción. El entrenamiento consta de dos etapas: primero se realiza un preentrenamiento en el dataset multiplataforma a gran escala Open X-Embodiment (que abarca demostraciones de manipulación real en más de 20 plataformas robóticas) para aprender conocimientos generales de manipulación (los patrones de acción como "agarrar" y "colocar" son comunes entre diferentes robots), y luego se realiza un ajuste fino con pocos datos para plataformas específicas. Puesto que la representación de acciones es idéntica en esencia, la verdadera diferencia entre ambos reside en la apertura y las elecciones de ingeniería: RT-2 y sus datos de entrenamiento son internos de Google, mientras que OpenVLA es completamente de código abierto (modelo backbone de código abierto Llama 2 más codificador visual combinado con datasets públicos), lo que permite a toda la comunidad reproducir y mejorar sobre su base por primera vez.

**Action Chunking: Tecnología de compensación de frecuencia universal en el campo VLA.**

Debido a la latencia de inferencia de los LLM, la frecuencia de control de VLA es muy inferior a las exigencias del control robótico tradicional (el control robótico tradicional exige frecuencias de 50-1000 Hz, mientras que la inferencia única de VLA solo alcanza unos 1-10 Hz, con una brecha de hasta dos órdenes de magnitud). El OpenVLA original es un ejemplo típico de este problema: solo emite una acción por inferencia (predicción autorregresiva de un solo paso a unos 6 Hz), siendo los tirones en el movimiento su principal deficiencia criticada. La **fragmentación de acciones** (Action Chunking) es una tecnología universal nacida para compensar esta brecha: propuesta inicialmente por ACT (Zhao et al., 2023) y adoptada posteriormente por π₀, OpenVLA-OFT, etc. El modelo no emite una sola acción por inferencia, sino que genera de un tirón una secuencia de acciones futuras para un período corto (en la configuración típica de π₀, genera un bloque de unos 0.5-1 segundos de acciones a la vez, equivalente a 25-50 acciones a 50 Hz de frecuencia de control), ejecutándolas secuencialmente el hilo de control a alta frecuencia mientras el modelo genera el siguiente lote asíncronamente en segundo plano. Siempre que el tiempo de inferencia del modelo sea menor que el tiempo de ejecución de este lote de acciones, el robot mantendrá un movimiento continuo y fluido, como el almacenamiento en búfer de video, cargando el contenido posterior por adelantado para que la reproducción no sufra tirones.

**π₀: Ruta de generación de trayectorias continuas.**

La verdadera diferenciación en la representación de acciones no está entre RT-2 y OpenVLA, sino entre los **tokens discretos y la generación de trayectorias continuas**. **π₀** representa esta última ruta: ya no predice tokens de acción discretos uno por uno, sino que utiliza flow matching (coincidencia de flujo, un método de generación continua de la misma familia que los modelos de difusión) partiendo del ruido aleatorio para "desruidificar" iterativamente en múltiples pasos, generando directamente una trayectoria de acciones suave y continua. Esta representación se combina de forma natural con Action Chunking, funcionando mejor en tareas que exigen alta precisión y fluidez de movimiento como las manipulaciones diestras. Para hacer una analogía: la ruta de tokens discretos es como elegir paso a paso en un menú "5 grados a la izquierda" y "3 centímetros adelante", mientras que la ruta de trayectorias continuas es como un pintor que traza primero la curva completa y la corrige pincelada a pincelada hasta darle forma.

**Preempción de bloques de acción:**

```python
chunk = vla(current_observation, skill)
for action in chunk:
    low_level.execute(action)
    if safety_event() or observation_changed_significantly():
        low_level.stop()
        discard_remaining(chunk)
        reobserve_and_replan()
        break
```

### Transferencia Sim2Real: La brecha entre simulación y realidad

En la sección de entornos de simulación del Capítulo 6 se explicaron los orígenes de la brecha entre simulación y realidad (sim-to-real gap) y el principio de la aleatorización de dominio (domain randomization) para hacerle frente, por lo que no se repetirá aquí; en una frase: dado que la simulación no puede restaurar completamente las características físicas, visuales y de hardware reales, se alteran aleatoriamente estos parámetros en un amplio rango durante el entrenamiento, forzando a la política a aprender un conjunto de representaciones generales estables ante diversos cambios (Figura 9-11). A continuación solo examinaremos cómo se aterriza este principio en brazos robóticos reales.

![Figura 9-11: Brecha Sim2Real y Aleatorización de Dominio](images/fig9-12.svg)

Existen numerosos casos de éxito en esta ruta: la manipulación diestra de manos mecánicas de OpenAI (el proyecto Dactyl logró la reorientación de cubos dentro de la mano, y su trabajo posterior logró resolver el cubo de Rubik con una mano mediante aleatorización automática de dominio ADR) y ANYmal de ETH Zurich (caminata robusta de robots cuadrúpedos sobre nieve, grava y otros terrenos complejos en exteriores) pertenecen a esta categoría.

Lo que realmente debe aportar este capítulo son los dos pasos de ingeniería ineludibles al aterrizar la aleatorización de dominio en máquinas reales. El primero es la **calibración del rango de aleatorización**: el rango no se puede fijar al azar; si es demasiado estrecho no cubrirá los cambios reales, y si es demasiado amplio aumentará la dificultad de entrenamiento, aprendiendo políticas subóptimas que "pueden lidiar con todo pero no son expertas en nada". En la práctica, se suele **medir y calibrar la distribución** de parámetros clave a partir de datos del entorno real (como la distribución real del coeficiente de fricción y la latencia de respuesta de los motores), muestreando dentro de ese rango; si la política entrenada en simulación cae notablemente en la máquina real, se amplía gradualmente el rango de aleatorización hasta que la brecha sim-to-real converja a un nivel aceptable. El segundo es el **alineamiento visual**: calibrar con precisión la pose de la cámara en simulación y en la realidad (alineamiento de entorno), y reemplazar aleatoriamente fondos fotografiados en el entorno real dentro del renderizado de simulación (reemplazo de fondo greenscreen), haciendo que la imagen de simulación se asemeje lo más posible a lo que ve la máquina real (estos dos pasos se demostrarán concretamente en el Experimento 9-9).

> **Experimento 9-10 ★★: Comparar tres bucles autónomos en simulación**
>
> **Objetivo:** Comparar ejecución abierta, comprobación paso a paso y estrategia predictiva con la misma tarea y herramientas.
>
> **Principio:** La comprobación permite recuperar fallos locales; el modelo del mundo continúa cuando predicción y realidad coinciden y replantea cuando divergen. El estado final se confirma con observación nueva.
>

> **Experimento 9-11 ★★★: Prueba RGB entre entornos para la misma tarea**
>
> **Objetivo:** Variar fondo, apariencia, iluminación y ruido visual y probar la adaptación de la política simulada.
>
> **Principio:** La diversidad visual puede mejorar la robustez, pero no sustituye la calibración real ni el bucle de seguridad.
>

+## Actualización 2026: planificación en streaming y modelos del mundo

La sección de robótica no debe terminar en «un VLM escribe un plan y un VLA lo ejecuta». Consideremos **«ordenar el escritorio»**. El planificador de horizonte largo construye primero una lista del estado: una taza medio llena, papeles, tres libros, un portátil abierto, una papelera y una caja organizadora. Después emite comandos con precondiciones y comprobaciones:

1. «Ve al escritorio y detente a 30 cm del borde».
2. «Pon los dos papeles en la papelera y verifica que no quede ninguno».
3. «Mantén la taza vertical y colócala en la bandeja; reduce la velocidad si el líquido se mueve».
4. «Cierra el portátil y muévelo a la esquina posterior izquierda; no tires del cable».
5. «Apila los libros por tamaño y guarda los bolígrafos en la caja».
6. «Solo cuando se hayan retirado los objetos frágiles y eléctricos, limpia la superficie».
7. «Retrocede, observa de nuevo y verifica el estado final».

Esto es un grafo de dependencias, no un párrafo de prosa. Si el usuario dice «guarda primero el portátil», cambia la prioridad. Si se vuelca la taza, el robot se detiene en un punto seguro, registra cup.orientation=fallen y laptop.at_risk=true, invalida el sufijo obsoleto y vuelve a planificar: proteger el portátil, contener el líquido, observar de nuevo y reanudar solo las tareas no afectadas. Las acciones ya verificadas no se repiten; los eventos urgentes cancelan el bloque actual y las actualizaciones normales esperan al siguiente punto seguro.

### Ejecución en streaming

La planificación y la ejecución pueden solaparse. Cuando existe un prefijo seguro, el planificador envía un comando completo al ejecutor mientras continúa planificando el sufijo. El comando debe ser completo y auditable:

```text
{"type":"command.commit","seq":12,"command_id":"desk-02","command":"put paper in bin","preconditions":["paper.visible","bin.reachable"],"success":"paper_count=0","cancel_at":"before_grasp"}
```

El ejecutor devuelve started, succeeded, cancelled o failed. El planificador actualiza las dependencias y aplica backpressure si la cola está llena o quedó obsoleta. El streaming reduce el tiempo hasta la primera acción segura; no permite ejecutar JSON parcial ni pensamientos no verificados.

### Por qué los VLA actuales generalizan mal

OpenVLA no se entrenó literalmente modificando solo el projector: el trabajo original también estudia fine-tuning completo, visión congelada, última capa y LoRA. La crítica estructural sigue siendo válida: un corpus enorme de texto e imágenes se conecta con un conjunto mucho menor de datos robóticos mediante una vía de adaptación estrecha; las adaptaciones baratas suelen concentrar la conducta nueva en el projector, módulos LoRA o la cabeza de acciones. El cloning de comportamiento aprende «observación + instrucción → bloque de acciones», no consecuencias físicas contrafactuales. Las acciones dependen del cuerpo del robot y los bloques obsoletos limitan la transferencia.

### Modelos del mundo

Un modelo del mundo aprende una transición accionable: estado + acción candidata → estado futuro predicho → seleccionar y verificar una acción. Es más amplio que V-JEPA: incluye modelos predictivos latentes (V-JEPA 2), modelos generativos interactivos (Genie 3 y Cosmos), World-Action Models (GeniWorld y Robust-WAM), acciones latentes aprendidas de vídeo sin etiquetas (LAWM-3D) y RL basado en modelos (Dreamer y MuZero). Su función es aprender de observaciones a escala, probar acciones contrafactuales antes de ejecutarlas, separar dinámicas compartidas del control específico del robot y replanificar cuando la predicción difiere de la realidad.

Los preprints de 2026 estudian priors dinámicos compartidos (DyPES-VLA), acciones visuales para manipulación cerrada fuera de distribución (GeniWorld), acciones latentes 3D desde vídeo humano (LAWM-3D), alineación semántica del futuro (Robust-WAM) y despliegue asíncrono en tiempo real. Son resultados prometedores, no una solución definitiva a la generalización.

## Resumen del capítulo

Aunque los tres escenarios parecen muy diferentes en la superficie, los dos obstáculos de la latencia y la multimodalidad siempre están presentes. La voz ha recorrido un camino evolutivo desde pipelines seriales hacia extremo a extremo y full-duplex, y desde el pensamiento rápido/lento separado hacia "pensar mientras se habla"; Computer Use ha alcanzado una precisión cercana a la humana en benchmarks como OSWorld, pero la brecha de eficiencia manifestada en una cantidad notablemente mayor de pasos de operación y en el crecimiento continuo del tiempo consumido por paso aún no cuenta con una solución sistemática; en el caso de los robots en tareas de manipulación basadas principalmente en retroalimentación visual, el cuello de botella ha pasado del hardware a la capacidad de generalización multitarea de la capa de control VLA (siendo el tacto y las manos diestras deficiencias de hardware aún no conquistadas). El siguiente capítulo ampliará la perspectiva a la colaboración entre múltiples Agentes, lo que constituye un desafío en otra dimensión.

## Preguntas de reflexión

1. ★★ El modelo de extremo a extremo de los Agentes de voz combina ASR-LLM-TTS en un solo modelo, lo que reduce la latencia pero pierde modularidad. Si el modelo de extremo a extremo comete un error en alguna etapa (como el reconocimiento de voz), la depuración y reparación es mucho más difícil que en un pipeline serial. ¿Cómo diseñarías el sistema de observabilidad (observability) para un Agente de voz de extremo a extremo?
2. ★ Step-Audio R1 logra "pensar mientras se habla" mediante la arquitectura de doble cerebro MPS. Sin embargo, los seres humanos a menudo dicen palabras sin pensar profundamente, se autorcorrigen o utilizan muletillas al "pensar mientras hablan". ¿Debería el "pensar mientras se habla" de un Agente imitar estas características humanas?
3. ★★ SoM (Set-of-Mark) y sus variantes estructuradas (índice de elementos DOM) convierten el grounding visual de Computer Use de una predicción de coordenadas abierta a una selección de ID cerrada, pero ambos requieren detectar y etiquetar previamente los elementos de la interfaz, ya sea mediante modelos de segmentación o mediante el DOM. Si la interfaz contiene controles no estándar o elementos dinámicos, la anotación puede ser incompleta o inexacta. En este caso, ¿se debería recurrir a la predicción de coordenadas?
4. ★★ Plataformas robóticas del orden de mil dólares como XLeRobot hacen que la recopilación de datos de teleoperación sea económica. Sin embargo, la calidad de los datos de teleoperación depende en gran medida de la habilidad del operador. ¿Cómo afectará el entrenamiento del modelo VLA los datos proporcionados por un operador no experimentado? ¿Cómo filtrar automáticamente datos de baja calidad durante la etapa de recopilación?
5. ★★★ Este capítulo abarca tres formas de interacción: voz, Computer Use y robótica. La tendencia común de estas tres formas es evolucionar de pipelines seriales hacia modelos de extremo a extremo. Si esta tendencia continúa, ¿cómo será la capa de interacción de los Agentes dentro de cinco años?
6. ★★★ El Computer Use actual funciona en un bucle discreto de "captura de pantalla → acción → captura de pantalla", donde cada observación es un fotograma estático. Sin embargo, la percepción humana de la pantalla es continua: podemos ver animaciones, observar el progreso de carga y comprender contenidos de video. Esto significa que el Computer Use de hoy es incapaz de manejar tareas que requieren comprensión visual temporal. ¿Cómo se debería rediseñar la capa de percepción para admitir la comprensión de flujos visuales continuos?
7. ★★ El índice de elementos DOM/Accessibility Tree produce efectos notables en aplicaciones Web estándar, pero cada vez más interfaces de software (renderizado en Canvas/WebGL, controles autodibujados multiplataforma) no proporcionan información estructurada accesible, teniendo que depender únicamente de la anotación visual o la predicción de coordenadas. ¿Crees que Computer Use debería apostar por una ruta puramente visual, o mantener simultáneamente dos vías, estructurada y visual? ¿Cuáles son los costos y beneficios de mantener ambas vías?
8. ★★ Los modelos VLA adoptan la fragmentación de acciones (action chunking); como se menciona en el texto principal, la configuración típica de π₀ es generar de una vez entre 25 y 50 acciones futuras a una frecuencia de 50 Hz, ocultando la latencia de inferencia en el tiempo de ejecución. Sin embargo, si el entorno cambia repentinamente durante la ejecución (por ejemplo, si se retira un objeto), la secuencia de acciones pregenerada quedará invalidada. ¿Cómo equilibrar la ventaja de eficiencia de la fragmentación de acciones con la velocidad de respuesta ante cambios en el entorno?
9. ★★★ Los tres escenarios de este capítulo (voz, Computer Use y robótica) enfrentan el problema de latencia en el bucle "Percepción-Pensamiento-Acción", evolucionando todos hacia la paralelización del pensamiento rápido y lento. En el escenario de voz, esto se manifiesta como "corregir tras hablar mal"; en el escenario de Computer Use, se manifiesta como "hacer clic primero y mirar después"; en el escenario robótico, se manifiesta como "dar un paso y observar". ¿Cómo garantizar que estas acciones basadas en el pensamiento rápido no causen consecuencias irreversibles?
