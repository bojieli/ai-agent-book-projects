-- Keep links to companion experiment directories usable outside the checkout.
-- In the Markdown sources, ../chapterN/... is correct relative to book-*/.
-- Those directories are not bundled into EPUB files, so make the links point
-- at the corresponding directory on GitHub before Pandoc packages the book.

function Link(link)
  local chapter, remainder = link.target:match("^%.%./(chapter%d+)(.*)$")
  if chapter and (remainder == "" or remainder:match("^[/#?]")) then
    local project_path = chapter .. remainder
    local path, suffix = project_path:match("^([^?#]*)(.*)$")
    local clean_path = path:gsub("/+$", "")
    local is_file = clean_path:match("%.%w+$") ~= nil
    local type_path = is_file and "blob" or "tree"
    link.target = "https://github.com/bojieli/ai-agent-book/" .. type_path .. "/main/" .. clean_path .. suffix
    return link
  end
end
