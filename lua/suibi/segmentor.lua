-- SPDX-License-Identifier: GPL-3.0-only
local core = require("suibi.core")
local M = {}

function M.init(env)
  env.mode = env.engine.schema.config:get_string("suibi/mode") or "pinyin"
end

function M.func(segmentation, env)
  local start = segmentation:get_current_start_position()
  if start ~= 0 then return true end
  if not core.parse(segmentation.input, env.mode) then return true end
  local segment = Segment(0, #segmentation.input)
  segment.tags = Set({ "suibi_aux" })
  segmentation:add_segment(segment)
  return false
end

return M
