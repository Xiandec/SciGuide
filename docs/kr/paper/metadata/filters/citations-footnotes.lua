function Cite(el)
  local targets = {}

  for _, citation in ipairs(el.citations) do
    table.insert(targets, "<" .. citation.id .. ">")
  end

  if #targets == 0 then
    return nil
  end

  local raw = "#footnote[#cite(" .. table.concat(targets, ", ")
    .. ', form: "full")]'

  return pandoc.RawInline("typst", raw)
end
