-- SPDX-License-Identifier: GPL-3.0-only
-- Shared, deterministic single-character lookup. No Rime API dependency.
local data = require("suibi.data")
local M = {}

function M.readings(sound, mode)
  if mode == "double_pinyin" or mode == "mspy" then return data[mode][sound] end
  local normalized = sound:gsub("^([nl])ue$", "%1ve")
  normalized = normalized:gsub("^([jqxy])v$", "%1u")
  if data.pinyin[normalized] then return { normalized } end
end

function M.parse(input, mode)
  local reverse = input:match("^`([hspnz]*)$")
  if reverse then return "", reverse end
  local sound, strokes = input:match("^([a-z;]+)`([hspnz]*)$")
  if not sound or not M.readings(sound, mode) then return nil end
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
