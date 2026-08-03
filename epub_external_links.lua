-- Keep links to companion experiment directories usable outside the checkout.
-- In the Markdown sources, ../chapterN/... is correct relative to book-*/.
-- Those directories are not bundled into EPUB files, so make the links point
-- at the corresponding directory on GitHub before Pandoc packages the book.

function Link(link)
  local project_path = link.target:match("^%.%./(chapter%d+.*)$")
  if project_path then
    local clean_path = project_path:gsub("/+$", "")
    local is_file = clean_path:match("%.%w+$") ~= nil
    local type_path = is_file and "blob" or "tree"
    link.target = "https://github.com/bojieli/ai-agent-book/" .. type_path .. "/main/" .. clean_path
    return link
  end
end
