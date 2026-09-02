# Agentes de IA em Profundidade: Princípios de Design e Prática de Engenharia

[![PDF](https://img.shields.io/badge/PDF-Download-success.svg)](#livro-eletrônico) [![Leitura online](https://img.shields.io/badge/🌐_Leitura_online-bojieli.github.io-success?style=flat-square)](https://bojieli.github.io/ai-agent-book/index.ptbr/) [![Stars](https://img.shields.io/github/stars/bojieli/ai-agent-book?style=social)](https://github.com/bojieli/ai-agent-book) [![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE) [![Languages](https://img.shields.io/badge/Traduções-15%20idiomas-informational.svg)](#livro-eletrônico)

[中文](README.md) · [English](docs/en/README.md) · [Español](docs/es/README.md) · [Bahasa Indonesia](docs/id/README.md) · [العربية](docs/ar/README.md) · [繁體中文（台灣）](docs/zh-TW/README.md) · [Русский](docs/ru/README.md) · [Tiếng Việt](docs/vi/README.md) · [தமிழ்](docs/ta/README.md) · [日本語](docs/ja/README.md) · [Türkçe](docs/tr/README.md) · [한국어](docs/ko/README.md) · [Magyar](docs/hu/README.md) · [עברית](README.he.md) · **Português (Brasil)** ← atual

> 📥 **[Download do PDF / EPUB](#livro-eletrônico)** (recomendado) — as edições em PDF e EPUB oferecem a melhor experiência de leitura. Também é possível [ler online](https://bojieli.github.io/ai-agent-book/index.ptbr/) com navegação completa, alternância entre idiomas e busca em texto integral.

**Agente = LLM + Contexto + Ferramentas** — o livro é construído em torno desta fórmula e apresenta, em dez capítulos, os princípios e a prática de engenharia de agentes de IA.

> 📢 **Mudanças da versão 2.0 em relação à 1.4:** a versão 2.0 unifica a parte "Interação Assíncrona" do antigo capítulo 4 com o conteúdo sobre "Agentes Multimodais" do antigo capítulo 9, reorganizando-os como o novo capítulo 6, "Interação: Expansão dos Espaços de Observação e Ação". Os antigos capítulos 6 ("Avaliação de Agentes"), 7 ("Pós-treinamento de Modelos") e 8 ("Evolução Contínua de Agentes") foram deslocados em um capítulo cada, passando a ser, respectivamente, os capítulos 7, 8 e 9.
>
> Se você tem um PDF antigo, recomendamos [baixar a versão mais recente do PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ptbr.pdf). A nova edição também inclui diversas correções e ajustes de conteúdo; confie apenas na versão mais recente.

A tradução completa para português do Brasil foi produzida por [Leonardo F. Nascimento](https://github.com/leofn) (LABHD-UFBA) com assistência de IA (GPT-5.6 Sol), revisão estrutural automatizada e glossário técnico. A tradução do texto das figuras (SVG) foi contribuída por [Líbna Raffaely](https://github.com/LibnaRaffaely).

## Livro eletrônico

- **Português (Brasil)** — tradução comunitária de [Leonardo F. Nascimento](https://github.com/leofn): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ptbr.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ptbr.epub)
- **Original em chinês**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.epub)

## Sumário

| Capítulo | Tópico | Leitura |
| :--: | --- | :--: |
| — | Introdução | [Ler](book-ptbr/introduction.ptbr.md) |
| 1 | Primeiros passos com agentes de IA | [Ler](book-ptbr/chapter1.ptbr.md) |
| 2 | Engenharia de contexto | [Ler](book-ptbr/chapter2.ptbr.md) |
| 3 | Memória do usuário e base de conhecimento | [Ler](book-ptbr/chapter3.ptbr.md) |
| 4 | Ferramentas | [Ler](book-ptbr/chapter4.ptbr.md) |
| 5 | Agente de código e geração de código | [Ler](book-ptbr/chapter5.ptbr.md) |
| 6 | Interação: expansão dos espaços de observação e ação | [Ler](book-ptbr/chapter6.ptbr.md) |
| 7 | Avaliação de agentes | [Ler](book-ptbr/chapter7.ptbr.md) |
| 8 | Pós-treinamento de modelos | [Ler](book-ptbr/chapter8.ptbr.md) |
| 9 | Evolução contínua de agentes | [Ler](book-ptbr/chapter9.ptbr.md) |
| 10 | Colaboração multiagente | [Ler](book-ptbr/chapter10.ptbr.md) |
| — | Posfácio | [Ler](book-ptbr/afterword.ptbr.md) |
| — | Respostas das questões de reflexão | [Ler](book-ptbr/reference-answers.ptbr.md) |

A documentação dos experimentos que acompanham o livro ainda não foi traduzida para português do Brasil. O código dos experimentos e as instruções em inglês ou chinês estão disponíveis nas pastas `chapter1/` a `chapter10/`.

## Build local

Para gerar o PDF são necessários Pandoc, XeLaTeX, ElegantBook, librsvg e as fontes incluídas no TeX Live:

```bash
cd book-ptbr
bash build_pdf.sh
```

Após gerar o PDF, é possível gerar e validar o EPUB a partir da raiz do repositório:

```bash
./build_epub.sh ptbr
```

O código-fonte da edição em português do Brasil está na pasta [`book-ptbr/`](book-ptbr/). O conteúdo é atualizado continuamente e pode diferir da edição chinesa original.