-- crossref.lua — внутренние кросс-ссылки (адаптация оригинала под русский).
--
-- Оригинал линковал китайские «图N-M» и «第N章». В русском переводе:
--   • подписи к рисункам — «Рис. N-M», ссылки в тексте — «рис. N-M» → линкуем;
--   • ссылки на главы записаны словами («в седьмой главе») и надёжно не матчатся
--     байтовыми Lua-паттернами, поэтому НЕ линкуются (текст читается как есть).
--
-- Примечание: Lua-паттерны работают по байтам. Кириллические литералы «Рис»/«рис»
-- ниже — это UTF-8 байты; матчатся как обычные подстроки. Классы вида [Рр] по байтам
-- НЕ работают для многобайтовых символов, поэтому два регистра обрабатываем отдельно.

local function fig_label(n, m) return 'fig:' .. n .. '-' .. m end

-- Найти самое раннее вхождение «Рис. N-M» или «рис. N-M» начиная с позиции i.
local function next_fig(text, i)
  local s1, e1, n1, m1 = text:find('Рис%.?%s*(%d+)%-(%d+)', i)
  local s2, e2, n2, m2 = text:find('рис%.?%s*(%d+)%-(%d+)', i)
  if s1 and (not s2 or s1 <= s2) then return s1, e1, n1, m1, 'Рис' end
  if s2 then return s2, e2, n2, m2, 'рис' end
  return nil
end

local function linkify(text)
  local out = {}
  local i, len = 1, #text
  while i <= len do
    local s, e, n, m, word = next_fig(text, i)
    if not s then
      table.insert(out, pandoc.Str(text:sub(i)))
      break
    end
    if s > i then table.insert(out, pandoc.Str(text:sub(i, s - 1))) end
    table.insert(out, pandoc.RawInline('latex',
      '\\crossreflink{' .. fig_label(n, m) .. '}{' .. word .. '. ' .. n .. '-' .. m .. '}'))
    i = e + 1
  end
  return out
end

return {
  {
    traverse = 'topdown',

    -- pandoc 3.x: отдельная картинка — это блок Figure с подписью.
    Figure = function(el)
      local cap = pandoc.utils.stringify(el.caption.long)
      local n, m = cap:match('[Рр]ис%.?%s*(%d+)%-(%d+)')
      if n and m then el.identifier = fig_label(n, m) end
      return el, false  -- в подпись не спускаемся (без само-ссылок)
    end,

    Image = function(el)
      local cap = pandoc.utils.stringify(el.caption)
      local n, m = cap:match('[Рр]ис%.?%s*(%d+)%-(%d+)')
      if n and m and el.identifier == '' then el.identifier = fig_label(n, m) end
      return el, false
    end,

    Str = function(el)
      if el.text:find('ис%.?%s*%d+%-%d+') then
        return linkify(el.text)
      end
    end,
  }
}
