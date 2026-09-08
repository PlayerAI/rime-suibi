# 实现结构

本文记录 v0.3.0 的实际实现（新增词语首字辅助），核查日期 2026-09-08。

## 边界

随笔是 Rime 方案与 librime-lua 模块，不修改前端或 librime。小狼毫和 Fcitx5-Rime 负责系统输入、候选窗口与部署。三套方案共享 `suibi` 用户词典，使用各自的拼写 prism；不依赖用户已安装的雾凇方案。

普通拼音由 Lua translator 委托唯一的原生 `script_translator` 实例，支持组词、整句和用户词频。Lua filter 只限制汉字字集，不重排普通候选。单字和词语辅助均为完整全拼或自然码/微软双拼编码，后接反引号与零个或多个笔画字母；词语按首字笔顺过滤。

`core.valid_sound` 按完整音节验证编码，支持音节边界上的单引号。全拼本身是一个合法音节时优先单字模式，“西安”需用 `xi'an`。不接受简拼、未完成音节或已经分段选定前缀的输入。

## 运行路径

1. `lua/suibi/processor.lua` 处理进入辅助、五类笔画、退格与确认，避免无匹配时将辅助编码直接提交。
2. `segmentor.lua` 将完整辅助输入标记为单个段，普通分词保持原样。
3. `translator.lua` 的单字路径调用 `core.lua`，以读音与笔顺前缀的交集生成单字候选，按上游静态字频降序、同频按字排序，多音字去重且不截断。词语路径用去掉辅码的编码查询同一原生 translator，要求候选覆盖完整编码、预编辑音节全部完整且音节数与字数一致，再按首字笔顺前缀过滤；不截断或重排原生候选。原生组句产生的完整候选也遵循相同规则。
4. `filter.lua` 在辅助状态只保留辅助候选；普通状态拒绝字表外汉字候选。非汉字标点不受字集限制。

单字辅助与反查不接入用户词典学习。词语路径用 `ShadowCandidate` 保留原始 Phrase，只延长外层候选的输入覆盖范围以吞掉反引号和笔画；原始音节跨度和读音编码不变。Enter 走 Context 确认与提交，Space 和数字选词走 Rime 原有流程，因此按原拼音学习。方案不再额外挂载第二个 `script_translator`，避免重复学习。`core.lua` 不依赖 Rime API，便于测试。

完整性校验使用原生候选的预编辑音节边界，不根据单字表反推词语读音，因而支持“般若”“六安”等词语特有读音。官方笔顺仍来自共享的 8105 字数据；未新增平行词库或重新排列词语频率。

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
