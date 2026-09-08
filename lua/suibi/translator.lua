-- SPDX-License-Identifier: GPL-3.0-only
local core = require("suibi.core")
local M = {}

function M.init(env)
  env.mode = env.engine.schema.config:get_string("suibi/mode") or "pinyin"
  -- One native translator serves ordinary and assisted input, so commits are
  -- learned once through its original Phrase candidates.
  env.native = Component.Translator(env.engine, "translator", "script_translator")
end

function M.func(input, segment, env)
  if not segment:has_tag("suibi_aux") then
    local translation = env.native:query(input, segment)
    if translation then
      for candidate in translation:iter() do yield(candidate) end
    end
    return
  end
  local sound, strokes = core.parse(input, env.mode)
  if not sound then return end
  if sound ~= "" and not core.readings(sound, env.mode) then
    local plain = Segment(segment.start, segment.start + #sound)
    plain.tags = Set({ "abc" })
    local translation = env.native:query(sound, plain)
    if not translation then return end
    for candidate in translation:iter() do
      local first = core.first_strokes(candidate.text)
      if candidate.start == plain.start and candidate._end == plain._end
        and first and first:sub(1, #strokes) == strokes
        and core.matches_word(candidate.text, sound, env.mode, candidate.preedit) then
        candidate.preedit = candidate.preedit .. "`" .. strokes
        local result = ShadowCandidate(candidate, "suibi_word", candidate.text,
          " 首字 · " .. first)
        -- Cover the suffix without changing the genuine Phrase's syllable spans.
        result._end = segment._end
        yield(result)
      end
    end
    return
  end
  for _, row in ipairs(core.lookup(sound, strokes, env.mode)) do
    local comment = " (" .. row.pinyin .. ") · " .. row.stroke
    local candidate = Candidate("suibi_aux", segment.start, segment._end, row.text, comment)
    candidate.quality = math.log(row.weight + 1)
    yield(candidate)
  end
end

return M
