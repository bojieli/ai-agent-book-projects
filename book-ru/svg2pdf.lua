-- svg2pdf.lua — в путях картинок меняет расширение .svg → .pdf.
--
-- На Windows в pandoc-сборке нет rsvg-convert, поэтому SVG предварительно
-- конвертируются в PDF (Inkscape, см. build_pdf.sh / convert_svg.sh), а этот
-- фильтр перенаправляет ссылки на готовые .pdf рядом с исходными .svg.
function Image(el)
  el.src = el.src:gsub('%.svg$', '.pdf')
  return el
end
