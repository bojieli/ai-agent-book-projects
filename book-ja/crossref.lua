-- crossref.lua — internal cross-reference links for the book.
--
-- Keeps the existing manual numbering (図N-M, 第N章) but turns every in-text
-- reference into a clickable internal link, and drops a \label anchor on each
-- figure and chapter. Uses raw LaTeX \label / \hyperref so it does not depend
-- on LaTeX counters (the displayed text is the manual number verbatim).
--
-- Topdown traversal: Image returns `false` to skip its own caption, so figure
-- captions are anchored but NOT self-linkified.

local chap = 0

local function fig_label(n, m) return 'fig:' .. n .. '-' .. m end
local function chap_label(n) return 'chap:' .. n end

-- Replace 図N-M / 第N章 occurrences inside a plain string with a list of
-- inlines (Str segments + RawInline hyperref links).
local function linkify(text)
  local out = {}
  local i = 1
  local len = #text
  while i <= len do
    -- earliest of the two patterns from position i
    local fs, fe, fn, fm = text:find('図(%d+)%-(%d+)', i)
    local cs, ce, cn = text:find('第(%d+)章', i)
    -- choose the nearest match
    local pick
    if fs and (not cs or fs <= cs) then pick = 'fig'
    elseif cs then pick = 'chap' end
    if not pick then
      table.insert(out, pandoc.Str(text:sub(i)))
      break
    end
    local ms = (pick == 'fig') and fs or cs
    local me = (pick == 'fig') and fe or ce
    if ms > i then table.insert(out, pandoc.Str(text:sub(i, ms - 1))) end
    if pick == 'fig' then
      table.insert(out, pandoc.RawInline('latex',
        '\\crossreflink{' .. fig_label(fn, fm) .. '}{図' .. fn .. '-' .. fm .. '}'))
    else
      table.insert(out, pandoc.RawInline('latex',
        '\\crossreflink{' .. chap_label(cn) .. '}{第' .. cn .. '章}'))
    end
    i = me + 1
  end
  return out
end

return {
  {
    traverse = 'topdown',

    Header = function(el)
      if el.level == 1 and not el.classes:includes('unnumbered') then
        chap = chap + 1
        el.content:insert(pandoc.RawInline('latex', '\\label{' .. chap_label(chap) .. '}'))
      end
      return el
    end,

    -- pandoc 3.x: a standalone image is a Figure block carrying the caption.
    Figure = function(el)
      local cap = pandoc.utils.stringify(el.caption.long)
      local n, m = cap:match('図%s*(%d+)%-(%d+)')
      if n and m then
        el.identifier = fig_label(n, m)  -- LaTeX writer emits \label{fig:N-M}
      end
      return el, false  -- do not descend into caption (no self-links)
    end,

    -- Fallback for any inline image that still carries its own caption.
    Image = function(el)
      local cap = pandoc.utils.stringify(el.caption)
      local n, m = cap:match('図%s*(%d+)%-(%d+)')
      if n and m and el.identifier == '' then
        el.identifier = fig_label(n, m)
      end
      return el, false
    end,

    Str = function(el)
      if el.text:find('図%d') or el.text:find('第%d+章') then
        return linkify(el.text)
      end
    end,
  }
}
