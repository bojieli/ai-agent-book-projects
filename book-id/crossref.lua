-- crossref.lua — internal cross-reference links for the book (English edition).
--
-- Keeps the existing manual numbering (Figure N-M, Chapter N) but turns every
-- in-text reference into a clickable internal link, and drops a \label anchor
-- on each figure and chapter. Uses raw LaTeX \label / \hyperref so it does not
-- depend on LaTeX counters (the displayed text is the manual number verbatim).
--
-- Unlike the Chinese edition (where 图N-M is a single Str token), English
-- references span two inline elements: Str("Figure") Space Str("2-6").
-- So matching happens at the Inlines level, pairing the keyword token with the
-- following number token.
--
-- Topdown traversal: Image/Figure return `false` to skip their own captions,
-- so figure captions are anchored but NOT self-linkified.

local chap = 0

local function fig_label(n, m) return 'fig:' .. n .. '-' .. m end
local function chap_label(n) return 'chap:' .. n end

-- Byte-level ASCII alphanumeric test (Lua's %w is locale-dependent and may
-- misclassify UTF-8 continuation bytes of curly quotes / em dashes).
local function is_ascii_alnum(b)
  return (b >= 48 and b <= 57) or (b >= 65 and b <= 90) or (b >= 97 and b <= 122)
end

-- Str suffixes we allow after the number: anything not starting with a letter,
-- digit, or hyphen (punctuation, em dashes, "'s", closing quotes/parens…).
local function ok_suffix(s)
  if s == '' then return true end
  local b = s:byte(1)
  return not (is_ascii_alnum(b) or b == 45)  -- 45 = '-'
end

-- Split "…Figure" / "…Chapter" tokens: the keyword may carry glued leading
-- punctuation, ASCII or multi-byte (e.g. "(Figure", "basics—Chapter").
-- Returns the prefix, or nil if the token does not end with the keyword or
-- the prefix ends in a letter/digit (e.g. "subChapter").
local function split_kw(text, kw)
  local pre = text:match('^(.-)' .. kw .. '$')
  if not pre then return nil end
  if pre ~= '' and is_ascii_alnum(pre:byte(#pre)) then return nil end
  return pre
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
      local n, m = cap:match('Figure%s*(%d+)%-(%d+)')
      if n and m then
        el.identifier = fig_label(n, m)  -- LaTeX writer emits \label{fig:N-M}
      end
      return el, false  -- do not descend into caption (no self-links)
    end,

    -- Fallback for any inline image that still carries its own caption.
    Image = function(el)
      local cap = pandoc.utils.stringify(el.caption)
      local n, m = cap:match('Figure%s*(%d+)%-(%d+)')
      if n and m and el.identifier == '' then
        el.identifier = fig_label(n, m)
      end
      return el, false
    end,

    Inlines = function(inlines)
      local out = pandoc.Inlines{}
      local i = 1
      local n = #inlines
      local changed = false
      while i <= n do
        local el = inlines[i]
        local linked = false
        if el.t == 'Str' and i + 2 <= n
            and inlines[i + 1].t == 'Space' and inlines[i + 2].t == 'Str' then
          local kind = 'Figure'
          local pre = split_kw(el.text, 'Figure')
          if not pre then
            kind = 'Chapter'
            pre = split_kw(el.text, 'Chapter')
          end
          if pre then
            local numtext = inlines[i + 2].text
            if kind == 'Figure' then
              local a, b, suffix = numtext:match('^(%d+)%-(%d+)(.*)$')
              if a and ok_suffix(suffix) then
                if pre ~= '' then out:insert(pandoc.Str(pre)) end
                out:insert(pandoc.RawInline('latex',
                  '\\crossreflink{' .. fig_label(a, b) .. '}{Figure ' .. a .. '-' .. b .. '}'))
                if suffix ~= '' then out:insert(pandoc.Str(suffix)) end
                linked = true
              end
            else
              local a, suffix = numtext:match('^(%d+)(.*)$')
              if a and ok_suffix(suffix) then
                if pre ~= '' then out:insert(pandoc.Str(pre)) end
                out:insert(pandoc.RawInline('latex',
                  '\\crossreflink{' .. chap_label(a) .. '}{Chapter ' .. a .. '}'))
                if suffix ~= '' then out:insert(pandoc.Str(suffix)) end
                linked = true
              end
            end
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
  }
}
