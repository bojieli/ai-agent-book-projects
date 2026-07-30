-- crossref.lua — internal cross-reference links for the book.
--
-- Keeps the existing manual numbering (그림 N-M, 제N장) but turns every in-text
-- reference into a clickable internal link, and drops a \label anchor on each
-- figure and chapter. Uses raw LaTeX \label / \hyperref so it does not depend
-- on LaTeX counters (the displayed text is the manual number verbatim).
--
-- Korean figure references usually span three inline elements:
-- Str("그림") Space Str("2-6"). When they follow an opening delimiter without
-- whitespace, Pandoc keeps that delimiter and "그림" in the preceding Str
-- (for example Str("문장(그림")). Match both forms at the Inlines level while
-- keeping compact N장 / 제N장 references handled inside a single Str token.
--
-- Topdown traversal: Image/Figure return `false` to skip their own captions,
-- so figure captions are anchored but NOT self-linkified.

local chap = 0

local function fig_label(n, m) return 'fig:' .. n .. '-' .. m end
local function chap_label(n) return 'chap:' .. n end

local function valid_chapter(n)
  local value = tonumber(n)
  return value and value >= 1 and value <= 10
end

-- Find the next N장 or 제N장 reference. A bare chapter number immediately
-- preceded by "~" or "-" is the end of a range such as 2~5장, so leave the
-- whole range as plain text instead of linking only its final number.
local function find_chapter(text, start)
  local pos = start
  while pos <= #text do
    local es, ee, en = text:find('제%s*(%d+)%s*장', pos)
    local bs, be, bn
    local bare_pos = pos
    while bare_pos <= #text do
      bs, be, bn = text:find('(%d+)%s*장', bare_pos)
      if not bs then break end
      local previous = bs > 1 and text:sub(bs - 1, bs - 1) or ''
      if previous ~= '~' and previous ~= '-' then break end
      bare_pos = be + 1
    end

    local cs, ce, cn
    if es and (not bs or es <= bs) then
      cs, ce, cn = es, ee, en
    else
      cs, ce, cn = bs, be, bn
    end

    if not cs then return nil end
    if valid_chapter(cn) then
      return cs, ce, cn, text:sub(cs, ce)
    end
    pos = ce + 1
  end
end

-- Replace compact N장 / 제N장 occurrences inside a plain string.
local function linkify(text)
  local out = {}
  local i = 1
  local len = #text
  while i <= len do
    local cs, ce, cn, displayed = find_chapter(text, i)
    if not cs then
      table.insert(out, pandoc.Str(text:sub(i)))
      break
    end
    if cs > i then table.insert(out, pandoc.Str(text:sub(i, cs - 1))) end
    table.insert(out, pandoc.RawInline('latex',
      '\\crossreflink{' .. chap_label(cn) .. '}{' .. displayed .. '}'))
    i = ce + 1
  end
  return out
end

local function ok_figure_suffix(s)
  if s == '' then return true end
  local b = s:byte(1)
  -- A following digit or hyphen means the number token was only partially
  -- matched. Punctuation and Korean particles are safe suffixes.
  return not ((b >= 48 and b <= 57) or b == 45)
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
      local n, m = cap:match('그림%s*(%d+)%-(%d+)')
      if n and m then
        el.identifier = fig_label(n, m)  -- LaTeX writer emits \label{fig:N-M}
      end
      return el, false  -- do not descend into caption (no self-links)
    end,

    -- Fallback for any inline image that still carries its own caption.
    Image = function(el)
      local cap = pandoc.utils.stringify(el.caption)
      local n, m = cap:match('그림%s*(%d+)%-(%d+)')
      if n and m and el.identifier == '' then
        el.identifier = fig_label(n, m)
      end
      return el, false
    end,

    Inlines = function(inlines)
      local out = pandoc.Inlines{}
      local i = 1
      local changed = false
      while i <= #inlines do
        local el = inlines[i]
        local linked = false
        local figure_prefix = el.t == 'Str' and el.text:match('^(.*)그림$')
        if figure_prefix and i + 2 <= #inlines
            and inlines[i + 1].t == 'Space'
            and inlines[i + 2].t == 'Str' then
          local a, b, suffix = inlines[i + 2].text:match('^(%d+)%-(%d+)(.*)$')
          if a and ok_figure_suffix(suffix) then
            if figure_prefix ~= '' then out:insert(pandoc.Str(figure_prefix)) end
            out:insert(pandoc.RawInline('latex',
              '\\crossreflink{' .. fig_label(a, b) .. '}{그림 ' .. a .. '-' .. b .. '}'))
            if suffix ~= '' then out:insert(pandoc.Str(suffix)) end
            linked = true
          end
        end
        if linked then
          i = i + 3
          changed = true
        else
          out:insert(el)
          i = i + 1
        end
      end
      if changed then return out end
    end,

    Str = function(el)
      if el.text:find('%d+%s*장') then
        return linkify(el.text)
      end
    end,
  }
}
