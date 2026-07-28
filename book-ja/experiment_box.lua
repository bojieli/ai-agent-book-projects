-- Pandoc Lua filter: wrap special sections in tcolorbox environments.
--
-- 1. "実験 X.Y" headings → experimentbox (description only, until next heading)
-- 2. "演習問題" headings → questionbox (until end of chapter or next same/higher heading)

function Pandoc(doc)
  local new_blocks = {}
  local in_box = false
  local box_type = ""
  local box_level = 0

  local function open_box(name)
    table.insert(new_blocks, pandoc.RawBlock("latex", "\\begin{" .. name .. "}"))
    in_box = true
    box_type = name
  end

  local function close_box()
    table.insert(new_blocks, pandoc.RawBlock("latex", "\\end{" .. box_type .. "}"))
    in_box = false
    box_type = ""
  end

  for _, block in ipairs(doc.blocks) do
    if block.t == "Header" then
      local text = pandoc.utils.stringify(block)

      if text:match("^実験%s?%d") then
        if in_box then close_box() end
        box_level = block.level
        block.classes:insert("unnumbered")
        open_box("experimentbox")
        table.insert(new_blocks, block)

      elseif text:match("^演習問題") then
        if in_box then close_box() end
        box_level = block.level
        block.classes:insert("unnumbered")
        open_box("questionbox")
        table.insert(new_blocks, block)

      elseif in_box then
        if box_type == "experimentbox" then
          close_box()
        elseif block.level <= box_level then
          close_box()
        end
        table.insert(new_blocks, block)

      else
        table.insert(new_blocks, block)
      end

    else
      table.insert(new_blocks, block)
    end
  end

  if in_box then close_box() end

  doc.blocks = new_blocks
  return doc
end
