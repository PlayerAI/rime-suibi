-- SPDX-License-Identifier: GPL-3.0-only
local core = require("suibi.core")
local M = {}

function M.init(env)
  env.mode = env.engine.schema.config:get_string("suibi/mode") or "pinyin"
end

function M.func(input, segment, env)
  if not segment:has_tag("suibi_aux") then return end
  local sound, strokes = core.parse(input, env.mode)
  if not sound then return end
  for _, row in ipairs(core.lookup(sound, strokes, env.mode)) do
    local comment = " (" .. row.pinyin .. ") · " .. row.stroke
    local candidate = Candidate("suibi_aux", segment.start, segment._end, row.text, comment)
    candidate.quality = math.log(row.weight + 1)
    yield(candidate)
  end
end

return M
