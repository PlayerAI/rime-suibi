-- SPDX-License-Identifier: GPL-3.0-only
-- Deterministic stroke lookup and complete-syllable validation. No Rime API dependency.
local data = require("suibi.data")
local M = {}
local strokes_by_char = {}
for _, row in ipairs(data.reverse) do strokes_by_char[row[1]] = row[2] end

function M.readings(sound, mode)
  if mode == "double_pinyin" or mode == "mspy" then return data[mode][sound] end
  local normalized = sound:gsub("^([nl])ue$", "%1ve")
  normalized = normalized:gsub("^([jqxy])v$", "%1u")
  if data.pinyin[normalized] then return { normalized } end
end

-- Advance by one complete syllable; apostrophes must fall on a boundary.
local function advance(sound, pos, mode)
  local result = {}
  local double = mode == "double_pinyin" or mode == "mspy"
  for length = double and 2 or 1, double and 2 or 6 do
    local last = pos + length - 1
    if last <= #sound then
      local readings = M.readings(sound:sub(pos, last), mode)
      if readings then
        local next_pos = last + 1
        if sound:sub(next_pos, next_pos) == "'" then
          next_pos = next_pos + 1
          if next_pos > #sound then next_pos = nil end
        end
        if next_pos then result[next_pos] = true end
      end
    end
  end
  return result
end

function M.valid_sound(sound, mode)
  if M.readings(sound, mode) then return true end
  if not sound:match("^[a-z;'][a-z;']+$") then return false end
  local counts = { [1] = 0 }
  for pos = 1, #sound do
    if counts[pos] then
      for next_pos in pairs(advance(sound, pos, mode)) do
        counts[next_pos] = math.max(counts[next_pos] or 0, counts[pos] + 1)
      end
    end
  end
  return (counts[#sound + 1] or 0) >= 2
end

function M.first_strokes(text)
  local cp = utf8.codepoint(text)
  return cp and strokes_by_char[utf8.char(cp)]
end

-- Native preedit supplies the actual syllable boundaries, including word-only
-- pronunciations absent from the single-character table. Every syllable must be
-- fully typed; completions have more characters than typed syllables.
function M.matches_word(text, sound, mode, preedit)
  local count, pos = 0, 1
  for code in (preedit or ""):gmatch("[^ ']+") do
    if not M.readings(code, mode) or sound:sub(pos, pos + #code - 1) ~= code then
      return false
    end
    count, pos = count + 1, pos + #code
    if sound:sub(pos, pos) == "'" then
      pos = pos + 1
      if pos > #sound then return false end
    end
  end
  return count >= 2 and count == utf8.len(text) and pos == #sound + 1
end

function M.parse(input, mode)
  local reverse = input:match("^`([hspnz]*)$")
  if reverse then return "", reverse end
  local sound, strokes = input:match("^([a-z;']+)`([hspnz]*)$")
  if not sound or not M.valid_sound(sound, mode) then return nil end
  return sound, strokes
end

function M.lookup(sound, strokes, mode)
  if not strokes:match("^[hspnz]*$") then return {} end
  local result, seen = {}, {}
  if sound == "" then
    if strokes == "" then return result end
    for _, row in ipairs(data.reverse) do
      if row[2]:sub(1, #strokes) == strokes then
        result[#result + 1] = { text = row[1], stroke = row[2], weight = row[3], pinyin = row[4] }
      end
    end
    table.sort(result, function(a, b)
      if a.weight ~= b.weight then return a.weight > b.weight end
      return a.text < b.text
    end)
    return result
  end
  for _, py in ipairs(M.readings(sound, mode) or {}) do
    for _, row in ipairs(data.pinyin[py]) do
      if row[2]:sub(1, #strokes) == strokes then
        local old = seen[row[1]]
        if not old then
          old = { text = row[1], stroke = row[2], weight = row[3], pinyin = py }
          seen[row[1]] = old
          result[#result + 1] = old
        elseif row[3] > old.weight then
          old.weight, old.pinyin = row[3], py
        end
      end
    end
  end
  table.sort(result, function(a, b)
    if a.weight ~= b.weight then return a.weight > b.weight end
    return a.text < b.text
  end)
  return result
end

local function is_han(cp)
  return (cp >= 0x3400 and cp <= 0x4DBF)
    or (cp >= 0x4E00 and cp <= 0x9FFF)
    or (cp >= 0xF900 and cp <= 0xFAFF)
    or (cp >= 0x20000 and cp <= 0x3347F)
end

function M.is_simplified(text)
  for _, cp in utf8.codes(text) do
    if is_han(cp) and not data.allowed[utf8.char(cp)] then return false end
  end
  return true
end

return M
