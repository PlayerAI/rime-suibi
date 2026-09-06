-- SPDX-License-Identifier: GPL-3.0-only
local core = require("suibi.core")

return function(translation, env)
  local auxiliary = env.engine.context.input:find("`", 1, true) ~= nil
  for candidate in translation:iter() do
    if (not auxiliary or candidate.type == "suibi_aux")
      and core.is_simplified(candidate.text) then
      yield(candidate)
    end
  end
end
