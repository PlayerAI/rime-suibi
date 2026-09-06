# 实现结构

本文记录 v0.2.0 的实际实现，核查日期 2026-09-06。

## 边界

随笔是 Rime 方案与 librime-lua 模块，不修改前端或 librime。小狼毫和 Fcitx5-Rime 负责系统输入、候选窗口与部署。三套方案共享 `suibi` 用户词典，使用各自的拼写 prism；不依赖用户已安装的雾凇方案。

普通拼音走 Rime `script_translator`，支持组词、整句和用户词频。Lua filter 只限制汉字字集，不重排普通候选。辅助模式必须是单个完整全拼音节或两键自然码/微软双拼，后接反引号与零个或多个笔画字母；不支持在词语或句子末尾附加辅码。

## 运行路径

1. `lua/suibi/processor.lua` 处理进入辅助、五类笔画、退格与确认，避免无匹配时将辅助编码直接提交。
2. `segmentor.lua` 将完整辅助输入标记为单个段，普通分词保持原样。
3. `translator.lua` 调用 `core.lua`，以读音与笔顺前缀的交集生成单字候选，按上游静态字频降序、同频按字排序，多音字去重且不截断。
4. `filter.lua` 在辅助状态只保留辅助候选；普通状态拒绝字表外汉字候选。非汉字标点不受字集限制。

辅助路径不接入用户词典学习。`core.lua` 不依赖 Rime API，便于穷举测试。

## 生成源

| 可编辑来源 | 生成产物 |
| --- | --- |
| `tools/build.py` 中的方案构造 | 三个 `suibi_*.schema.yaml`、`suibi.dict.yaml` |
| `data/sources/strokes.tsv`、`rime_ice_chars.dict.yaml` | `cn_dicts/suibi_chars.dict.yaml`、`lua/suibi/data.lua` |
| `data/natural_double_pinyin.json`、`data/microsoft_double_pinyin.json` | 双拼方案代数、Lua 双拼读音映射 |
| 固定版本雾凇 `base.dict.yaml` | `cn_dicts/suibi_words.dict.yaml` |
| 上述所有输入 | `data/build_stats.json` |

原始大词库缓存于 `.cache/upstream/`，按 `data/sources.json` 的固定 URL 获取并验证哈希。所有生成产物随仓库保存，终端用户安装不需要 Python 构建流程。单方案安装脚本复制 10 个运行文件（三方案共 12 个）；备份、用户词库、编译缓存不属于版本源码。

反查模式为反引号加笔顺前缀，不依赖读音。生成的 `data.reverse` 覆盖全部 8105 字，包含字频和所有已收录无声调拼音；缺读音时仍可查字。反引号后无笔画时不生成候选，双反引号输出字面符号。独立包的 `package.json` 限定默认安装方案；共用数据使不同方案可同时安装。
