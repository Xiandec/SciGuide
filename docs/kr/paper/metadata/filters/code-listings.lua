local function longest_fence(text)
  local fence = "```"
  while string.find(text, fence, 1, true) do
    fence = fence .. "`"
  end
  return fence
end

function CodeBlock(el)
  local caption = el.attributes.caption
  if not caption or caption == "" then
    return nil
  end

  local language = el.classes[1] or ""
  local fence = longest_fence(el.text)
  local label = ""

  if el.identifier ~= "" then
    label = " <" .. el.identifier .. ">"
  end

  local raw_block
  if language ~= "" then
    raw_block = table.concat({
      "#figure(",
      fence .. language,
      el.text,
      fence .. ",",
      "  caption: [" .. caption .. "],",
      "  kind: raw,",
      ")" .. label,
    }, "\n")
  else
    raw_block = table.concat({
      "#figure(",
      fence,
      el.text,
      fence .. ",",
      "  caption: [" .. caption .. "],",
      "  kind: raw,",
      ")" .. label,
    }, "\n")
  end

  return pandoc.RawBlock("typst", raw_block)
end
