local function longest_fence(text)
  local fence = "```"
  while string.find(text, fence, 1, true) do
    fence = fence .. "`"
  end
  return fence
end

local MAX_LISTING_LINES = 30

local function split_lines(text)
  local lines = {}
  local start = 1

  while true do
    local newline = string.find(text, "\n", start, true)
    if not newline then
      table.insert(lines, string.sub(text, start))
      break
    end

    table.insert(lines, string.sub(text, start, newline - 1))
    start = newline + 1
  end

  return lines
end

local function join_lines(lines, first_index, last_index)
  local chunk = {}
  for index = first_index, last_index do
    table.insert(chunk, lines[index])
  end
  return table.concat(chunk, "\n")
end

local function build_listing(text, language, caption, identifier)
  local fence = longest_fence(text)
  local label = ""

  if identifier and identifier ~= "" then
    label = " <" .. identifier .. ">"
  end

  if language ~= "" then
    return table.concat({
      "#figure(",
      fence .. language,
      text,
      fence .. ",",
      "  caption: [" .. caption .. "],",
      "  kind: raw,",
      ")" .. label,
    }, "\n")
  end

  return table.concat({
    "#figure(",
    fence,
    text,
    fence .. ",",
    "  caption: [" .. caption .. "],",
    "  kind: raw,",
    ")" .. label,
  }, "\n")
end

function CodeBlock(el)
  local caption = el.attributes.caption
  if not caption or caption == "" then
    return nil
  end

  local language = el.classes[1] or ""
  local lines = split_lines(el.text)

  if #lines <= MAX_LISTING_LINES then
    return pandoc.RawBlock(
      "typst",
      build_listing(el.text, language, caption, el.identifier)
    )
  end

  local blocks = {}
  local part_count = math.ceil(#lines / MAX_LISTING_LINES)

  for part_index = 1, part_count do
    local first_line = ((part_index - 1) * MAX_LISTING_LINES) + 1
    local last_line = math.min(part_index * MAX_LISTING_LINES, #lines)
    local part_caption = caption
      .. " (часть "
      .. tostring(part_index)
      .. " из "
      .. tostring(part_count)
      .. ")"
    local part_identifier = ""

    if part_index == 1 then
      part_identifier = el.identifier
    end

    table.insert(
      blocks,
      build_listing(
        join_lines(lines, first_line, last_line),
        language,
        part_caption,
        part_identifier
      )
    )
  end

  return pandoc.RawBlock("typst", table.concat(blocks, "\n\n"))
end
