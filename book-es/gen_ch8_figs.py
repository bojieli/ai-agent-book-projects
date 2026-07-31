#!/usr/bin/env python3
"""Chapter 8 figures — Agent's self-evolution."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svg_lib import SVG, FS_SMALL, FS_TINY, FS_BODY

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')


def _pipeline(stages, fname, W=880, feedback=None):
    """Horizontal stage pipeline with an optional dashed feedback loop."""
    n = len(stages)
    bw = min(190, (W - 40 - (n - 1) * 22) // n)
    bh, gap = 84, 22
    H = 234 if feedback else 174
    s = SVG(W, H)
    x0 = (W - (n * bw + (n - 1) * gap)) / 2
    y = 48
    pos = []
    for i, (lab, sub) in enumerate(stages):
        x = x0 + i * (bw + gap)
        s.box(x, y, bw, bh, lab, sublabel=sub, bold=True, fill='light')
        pos.append(x)
        if i > 0:
            s.arrow(pos[i - 1] + bw + 2, y + bh / 2, x - 2, y + bh / 2)
    if feedback:
        lx = pos[-1] + bw / 2
        fx = pos[0] + bw / 2
        ry = y + bh + 34
        s.line(lx, y + bh, lx, ry, dash=True)
        s.line(lx, ry, fx, ry, dash=True)
        s.arrow(fx, ry, fx, y + bh + 2, dash=True)
        s.text((lx + fx) / 2, ry + 18, feedback, size=FS_SMALL, fill='text_light')
    s.save(os.path.join(OUT, fname + '.svg'))


def fig8_1():  # Externalized learning loop
    _pipeline([("Completar tarea", "Generar experiencia bruta"),
               ("Refinar experiencia", "Resumir, comprimir, estructurar"),
               ("Almacenar en sist. externo", "Base de conoc./herram. recuperables"),
               ("Recuperar y reutilizar", "Llamar en la siguiente tarea")],
              'fig8-1', feedback="La experiencia se acumula de forma permanente y se reutiliza entre sesiones")


def fig8_2():  # GAIA experience learning system
    _pipeline([("Traza exitosa", "Proceso de finalización de tarea"),
               ("Resumen de estrategia", "Destilar en síntesis de conocimiento"),
               ("Base de síntesis de conoc.", "Crear índice semántico"),
               ("Inyección en recuperación", "El Agente lo usa al tomar decisiones")],
              'fig8-2', feedback="Reutilizar experiencia pasada para tareas similares")


def fig8_3():  # Hierarchical tool matching (server level -> tool level)
    W, H = 620, 354
    s = SVG(W, H)
    cx = W / 2
    s.box(cx - 150, 46, 300, 52, "Consulta del usuario", sublabel='"Depurar este archivo"', bold=True, fill='light')
    s.arrow(cx, 100, cx, 120)
    s.box(cx - 220, 122, 440, 62, "Capa 1: Búsqueda semántica a nivel de servidor",
          sublabel="Cientos de servidores MCP → recuperar los mejores K servidores", bold=True, fill='light')
    s.arrow(cx, 186, cx, 208)
    s.box(cx - 220, 210, 440, 62, "Capa 2: Búsqueda semántica a nivel de herramienta",
          sublabel="Coincidir solo entre herramientas de los mejores K servidores → mejores N herramientas", bold=True, fill='light')
    s.arrow(cx, 274, cx, 296)
    s.box(cx - 150, 298, 300, 46, "Herramienta seleccionada",
          sublabel="Reduce drásticamente el espacio de candidatos y reduce el costo de selección", bold=True, fill='light')
    s.save(os.path.join(OUT, 'fig8-3.svg'))


def fig8_4():  # KV Cache Optimization for Dynamic Tool Loading (Naive vs Optimized)
    W, H = 860, 244
    s = SVG(W, H)
    s.text(220, 46, "Ingenuo: todas las herramientas en el prompt del sistema", size=FS_SMALL, bold=True, fill='darker')
    s.rect(30, 62, 380, 70, fill='#f0d8d8')
    s.text(220, 84, "Prompt del sistema + todas las def. de herramientas", size=FS_SMALL, bold=True)
    s.text(220, 108, "Cualquier cambio en herramientas → invalida toda la caché KV", size=FS_TINY, fill='text_light')
    s.rect(30, 140, 380, 46, fill='light')
    s.text(220, 163, "Recomputado en cada ronda, alto costo", size=FS_SMALL)

    s.text(640, 46, "Optimizado: def. de herramientas cargadas bajo demanda", size=FS_SMALL, bold=True, fill='darker')
    s.rect(450, 62, 380, 40, fill='#d8e8d8')
    s.text(640, 82, "Prompt del sistema estable (prefijo de acierto de caché)", size=FS_SMALL, bold=True)
    s.rect(450, 106, 380, 40, fill='light')
    s.text(640, 126, "Def. de herramientas agregadas bajo demanda (parte variable)", size=FS_SMALL)
    s.rect(450, 150, 380, 40, fill='light')
    s.text(640, 170, "Traza de conversación", size=FS_SMALL)
    s.text(640, 206, "El prefijo estable no cambia → la caché KV se reutiliza continuamente", size=FS_TINY, fill='text_light')
    s.line(430, 54, 430, 220, dash=True)
    s.save(os.path.join(OUT, 'fig8-4.svg'))


def fig8_5():  # Agent Self-Evolution Pipeline
    _pipeline([("① Identificación de necesidad", "Herramientas actuales insuficientes"),
               ("② Búsqueda de herramientas", "Búsqueda en el mundo abierto"),
               ("③ Encapsulación de código", "Generar y encapsular"),
               ("④ Registro de herramientas", "Agregar a librería, reutilizar")],
              'fig8-5', feedback="Las nuevas herramientas registradas se reutilizan en tareas posteriores, expandiendo continuamente sus capacidades")


def fig8_6():  # Voyager Continuous Learning Architecture
    _pipeline([("Generador de plan de estudio", "Proponer nuevas tareas progresivas"),
               ("Mecanismo de prompt iterativo", "Generar código de habilidad y depurar"),
               ("Librería de habilidades", "Almacenar habilidades reutilizables")],
              'fig8-6', W=760, feedback="La acumulación de habilidades desbloquea tareas más difíciles (exploración en mundo abierto)")


def fig8_7():  # Experiment 8-5 Self-Evolution Pipeline
    _pipeline([("① Buscar", "Encontrar herramienta en la web abierta"),
               ("② Evaluar", "Determinar idoneidad"),
               ("③ Probar", "Verificar usabilidad"),
               ("④ Empaquetar", "Envolver en herramienta estándar"),
               ("⑤ Reutilizar", "Agregar a la librería de herramientas")],
              'fig8-7', W=940, feedback="Las nuevas herramientas se acumulan para ser reutilizadas en tareas posteriores")


if __name__ == '__main__':
    for fn in (fig8_1, fig8_2, fig8_3, fig8_4, fig8_5, fig8_6, fig8_7):
        fn()
        print('saved', fn.__name__)
