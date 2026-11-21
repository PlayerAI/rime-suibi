# 第三方来源与修改说明

随笔拼音原创代码及方案采用 GPL-3.0-only，许可证正文见 [LICENSE](LICENSE)。本文件记录 v0.4.0 使用的来源与转换，核查日期为 2026-11-21。依赖的输入法前端和引擎独立分发，保留各自许可证。

## 万象拼音

自 v0.4.0 起，随笔的字音、字频和词库来自 [amzxyz/rime-wanxiang](https://github.com/amzxyz/rime-wanxiang)（万象拼音，作者 amzxyz 及其贡献者），数据许可证为 [Creative Commons Attribution 4.0 International（CC BY 4.0）](https://creativecommons.org/licenses/by/4.0/)，许可证正文见 [LICENSES/rime-wanxiang-CC-BY-4.0.txt](LICENSES/rime-wanxiang-CC-BY-4.0.txt)。固定提交为 `0a137fa979277228ac7580f28b941d604a4be16d`。万象词库的数据中心为 [amzxyz/rime-wanxiang-data](https://github.com/amzxyz/rime-wanxiang-data)。

- `dicts/zi.dict.yaml` 原样保存为 `data/sources/wanxiang_zi.dict.yaml`，生成 `cn_dicts/suibi_chars.dict.yaml` 及 `lua/suibi/data.lua` 中的读音与字频。
- `dicts/jichu.dict.yaml`（基础词库）与 `dicts/duoyin.dict.yaml`（多音词库）在构建时按固定 URL 下载并校验哈希，合并生成 `cn_dicts/suibi_words.dict.yaml`。未使用万象的错音、地名、名人等其他词库，也未使用其方案、Lua 脚本或语法模型。

随笔对万象数据的修改：去除声调并将 ü 写作 v；按万象自身拼写代数将独立的 n、ng、m 读音写作 en、eng、me；限定《通用规范汉字表》8105 字，过滤含表外字或无法映射读音的词条；合并去声调后重复的词条（取较高词频）；缺失词频按 0 处理，带非数字后缀的词频取前导数字。数据署名归原作者，随笔不主张其为原创。依据 CC BY 4.0，改编后的数据随本项目以 GPL-3.0-only 分发；固定输入的哈希见 [sources.json](data/sources.json)。

## 雾凇拼音

来自 [iDvel/rime-ice](https://github.com/iDvel/rime-ice)，作者 iDvel 及其贡献者，项目许可证 GNU GPL v3.0。固定提交为 `fbb516b2786e4d5444383706d13c31c2e4d10c08`。

- v0.2.0—v0.3.0 曾使用 `cn_dicts/8105.dict.yaml`（字音与字频）和 `cn_dicts/base.dict.yaml`（词库），v0.4.0 起改用万象数据，不再包含这两份文件。历史版本的 `base.dict.yaml` 上游列明华宇野风系统词库、[清华 THUOCL](https://github.com/thunlp/THUOCL)、[现代汉语常用词表](https://gist.github.com/indiejoseph/eae09c673460aa0b56db)、[腾讯词向量](https://ai.tencent.com/ailab/nlp/zh/download.html)及 Huandeep 的整理贡献，另参考多部汉语词典。完整原始注释可从 [固定版本原文件](https://github.com/iDvel/rime-ice/blob/fbb516b2786e4d5444383706d13c31c2e4d10c08/cn_dicts/base.dict.yaml) 阅读。
- 当前仍使用：`double_pinyin.schema.yaml` 的自然码拼写代数保存为 `data/natural_double_pinyin.json`，供普通双拼与辅助读音映射共用。

v0.3.0 及以前对雾凇数据的修改包括：限定规范汉字范围、过滤字表外词语、生成独立方案与词库名称、生成 Lua 查询数据，以及新增笔顺前缀筛选。数据继承上游署名和来源，不主张其为随笔原创。

## 笔顺

`data/sources/strokes.tsv` 来源于教育部发布的 [《通用规范汉字笔顺规范》GF 0023—2020](https://www.moe.gov.cn/jyb_sjzl/ziliao/A19/202103/W020210318300204215237.pdf)。保存 8,105 个字的序号、汉字与五类数字笔顺；抽取结果在前期研究中与公开笔顺数据逐字比对，字序和笔顺一致。这里只保存结构化笔顺事实，未打包原 PDF 的版式、说明文字或图像，也不将该规范标称为 GPL 授权作品。

转换约定：1 → h（横/提），2 → s（竖/竖钩），3 → p（撇），4 → n（点/捺），5 → z（折）。固定输入文件与原 PDF 的 SHA-256 见 [sources.json](data/sources.json)。

## Rime API

`tools/rime_api.py` 的 ctypes 结构依据 RIME Developers 的 `rime_api.h` 公共接口。接口来源：[librime 1.17.0](https://github.com/rime/librime/blob/1.17.0/src/rime_api.h)；保留其 [BSD 许可证](LICENSES/librime-BSD.txt)。测试用动态库由工具单独下载，不进入方案安装包。

微软双拼映射 `data/microsoft_double_pinyin.json` 提取自同一固定提交的 `iDvel/rime-ice/double_pinyin_mspy.schema.yaml` 中 `speller/algebra`（GPL-3.0）；该文件注明键位映射源于 `rime/rime-double-pinyin`。随笔保留分号 ing 和兼容别名，生成自己的方案及反查映射。哈希见 `data/sources.json`。
