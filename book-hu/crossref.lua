-- crossref.lua — internal cross-reference links for the Hungarian edition.
--
-- Hungarian references put the number before the noun ("2-6. ábra",
-- "2. fejezet"). This filter anchors chapter and figure targets and turns
-- those textual references into clickable LaTeX links. It also recognizes
-- the legacy English "Figure 2-6" caption form so older source revisions
-- still build with working targets.

local chapter = 0

local function figure_label(n, m)
  return "fig:" .. n .. "-" .. m
end

local function chapter_label(n)
  return "chap:" .. n
end

local function figure_number(text)
  local n, m = text:match("(%d+)%-(%d+)%.%s*Ábra")
  if not n then
    n, m = text:match("(%d+)%-(%d+)%.%s*ábra")
  end
  if not n then
    n, m = text:match("[Ff]igure%s*(%d+)%-(%d+)")
  end
  return n, m
end

local function split_keyword(text, keyword)
  local suffix = text:match("^" .. keyword .. "(.*)$")
  if suffix == nil then return nil end
  return suffix
end

return {
  {
    traverse = "topdown",

    Header = function(el)
      if el.level == 1 and not el.classes:includes("unnumbered") then
        chapter = chapter + 1
        el.content:insert(
          pandoc.RawInline("latex", "\\label{" .. chapter_label(chapter) .. "}")
        )
      end
      return el
    end,

    Figure = function(el)
      local n, m = figure_number(pandoc.utils.stringify(el.caption.long))
      if n and m then
        el.identifier = figure_label(n, m)
      end
      return el, false
    end,

    Image = function(el)
      local n, m = figure_number(pandoc.utils.stringify(el.caption))
      if n and m and el.identifier == "" then
        el.identifier = figure_label(n, m)
      end
      return el, false
    end,

    Inlines = function(inlines)
      local output = pandoc.Inlines{}
      local i = 1
      local changed = false

      while i <= #inlines do
        local number = inlines[i]
        local space = inlines[i + 1]
        local word = inlines[i + 2]
        local linked = false

        if number and number.t == "Str"
            and space and space.t == "Space"
            and word and word.t == "Str" then
          local n, m, number_suffix =
            number.text:match("^(%d+)%-(%d+)%.(.*)$")
          local word_suffix = split_keyword(word.text, "Ábra")
          if word_suffix == nil then
            word_suffix = split_keyword(word.text, "ábra")
          end

          if n and m and number_suffix == "" and word_suffix ~= nil then
            output:insert(pandoc.RawInline(
              "latex",
              "\\crossreflink{" .. figure_label(n, m) .. "}{" ..
                n .. "-" .. m .. ". ábra}"
            ))
            if word_suffix ~= "" then
              output:insert(pandoc.Str(word_suffix))
            end
            linked = true
          else
            n, number_suffix = number.text:match("^(%d+)%.(.*)$")
            word_suffix = split_keyword(word.text, "[Ff]ejezet")
            if n and number_suffix == "" and word_suffix ~= nil then
              output:insert(pandoc.RawInline(
                "latex",
                "\\crossreflink{" .. chapter_label(n) .. "}{" ..
                  n .. ". fejezet}"
              ))
              if word_suffix ~= "" then
                output:insert(pandoc.Str(word_suffix))
              end
              linked = true
            end
          end
        end

        if linked then
          i = i + 3
          changed = true
        else
          output:insert(inlines[i])
          i = i + 1
        end
      end

      if changed then return output end
    end,
  }
}
