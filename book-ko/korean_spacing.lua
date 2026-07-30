-- korean_spacing.lua — preserve source-defined Korean mixed-script spacing.
--
-- ElegantBook enables xeCJK through lang=cn. Its automatic CJK/Latin glue is
-- disabled in preamble.tex because Korean particles attach directly to Latin
-- terms (for example, "GPT-5.6으로"). Some xeCJK paths then discard a source
-- space in the opposite direction ("이미 AI"). Protect only those explicit
-- Pandoc spaces instead of adding spacing at every script boundary.

local function first_codepoint(text)
  for _, codepoint in utf8.codes(text) do
    return codepoint
  end
end

local function last_codepoint(text)
  local last
  for _, codepoint in utf8.codes(text) do
    last = codepoint
  end
  return last
end

local function is_cjk(codepoint)
  if not codepoint then return false end
  return
    (codepoint >= 0x1100 and codepoint <= 0x11FF) or
    (codepoint >= 0x2E80 and codepoint <= 0x2FFF) or
    (codepoint >= 0x3040 and codepoint <= 0x30FF) or
    (codepoint >= 0x3130 and codepoint <= 0x318F) or
    (codepoint >= 0x31A0 and codepoint <= 0x31BF) or
    (codepoint >= 0x3400 and codepoint <= 0x4DBF) or
    (codepoint >= 0x4E00 and codepoint <= 0x9FFF) or
    (codepoint >= 0xA960 and codepoint <= 0xA97F) or
    (codepoint >= 0xAC00 and codepoint <= 0xD7FF) or
    (codepoint >= 0xF900 and codepoint <= 0xFAFF) or
    (codepoint >= 0x20000 and codepoint <= 0x323AF)
end

local function boundary_text(inline)
  local text = pandoc.utils.stringify(inline)
  if text ~= '' then return text end
  if inline.t == 'RawInline' and inline.format:match('latex') then
    return inline.text
  end
  return ''
end

local function ends_in_cjk(inline)
  local text = boundary_text(inline)
  if is_cjk(last_codepoint(text)) then return true end

  -- Earlier PDF filters can wrap a Korean reference in raw LaTeX, leaving
  -- braces after the visible text. Treat any CJK character in that wrapper as
  -- a CJK boundary; an occasional extra protected source space is harmless.
  if inline.t == 'RawInline' then
    for _, codepoint in utf8.codes(text) do
      if is_cjk(codepoint) then return true end
    end
  end
  return false
end

local function starts_in_cjk(inline)
  return is_cjk(first_codepoint(boundary_text(inline)))
end

local function preserve(inlines, heading)
  local out = pandoc.Inlines{}
  for index, inline in ipairs(inlines) do
    local is_source_space = inline.t == 'Space' or inline.t == 'SoftBreak'
    local mixed_boundary =
      is_source_space and index > 1 and index < #inlines and
      ends_in_cjk(inlines[index - 1]) and
      not starts_in_cjk(inlines[index + 1])

    if mixed_boundary then
      if heading then
        -- Keep PDF bookmarks textual; raw LaTeX is omitted from their fallback.
        out:insert(pandoc.Str(utf8.char(0x00A0)))
      else
        -- The zero-width kern prevents grouped links/emphasis from swallowing
        -- the following explicit word space while preserving line breaking.
        out:insert(pandoc.RawInline('latex', '\\kern0pt\\ '))
      end
    else
      out:insert(inline)
    end
  end
  return out
end

return {
  {
    traverse = 'topdown',

    Header = function(header)
      header.content = preserve(header.content, true)
      return header, false
    end,

    Inlines = function(inlines)
      return preserve(inlines, false)
    end,
  }
}
