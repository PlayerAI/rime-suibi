-- SPDX-License-Identifier: GPL-3.0-only
local core = require("suibi.core")
local M = {}
local accepted, noop = 1, 2

function M.init(env)
  env.mode = env.engine.schema.config:get_string("suibi/mode") or "pinyin"
end

function M.func(key, env)
  local ctx = env.engine.context
  if ctx:get_option("ascii_mode") then return noop end
  local shift_key = key.keycode == 0xffe1 or key.keycode == 0xffe2
  -- Prevent ascii_composer's commit_code from leaking sound`stroke syntax.
  if shift_key and ctx.input:find("`", 1, true) then return accepted end
  if key:release() then return noop end
  if key:ctrl() or key:alt() or key:super() then return noop end
  local input, code = ctx.input, key.keycode
  local delimiter = input:find("`", 1, true)

  if not delimiter then
    if code ~= 96 then return noop end
    -- A leading backtick starts stroke-only reverse lookup.
    if input == "" then
      ctx:push_input("`")
      return accepted
    end
    -- Auxiliary mode is explicit and only starts at a complete single syllable.
    if ctx.caret_pos == #input and core.readings(input, env.mode) then
      ctx:push_input("`")
    end
    return accepted
  end

  if code == 0xff1b then -- Escape
    ctx:clear()
    return accepted
  elseif code == 0xff08 then -- BackSpace
    -- Editing remains at the end while in auxiliary mode.
    ctx.caret_pos = #input
    ctx:pop_input(1)
    return accepted
  elseif code == 0xff51 or code == 0xff50 then -- Left/Home: do not edit the sound through an active suffix
    return accepted
  elseif code == 0xff53 or code == 0xff57 then -- Right/End
    ctx.caret_pos = #input
    return accepted
  elseif code == 96 then
    if input == "`" then
      ctx:clear()
      env.engine:commit_text("`")
    end
    return accepted
  elseif code == 0xff0d or code == 0xff8d then -- Return / keypad Enter
    local candidate = ctx:get_selected_candidate()
    if candidate and candidate.type == "suibi_aux" then
      env.engine:commit_text(candidate.text)
      ctx:clear()
    end
    return accepted
  end

  if (code >= 97 and code <= 122) or (code >= 65 and code <= 90) then
    local ch = string.char(code):lower()
    if ch:match("^[hspnz]$") then
      ctx.caret_pos = #input
      ctx:push_input(ch)
    end
    return accepted
  end
  -- With no match, Space/digits/punctuation must never commit the raw suffix.
  if not ctx:has_menu() and code >= 32 and code <= 126 then return accepted end
  return noop
end

return M
