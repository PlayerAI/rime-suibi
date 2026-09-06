# 第三方来源与修改说明

随笔拼音原创代码及方案采用 GPL-3.0-only，许可证正文见 [LICENSE](LICENSE)。本文件记录 v0.2.0 使用的来源与转换，核查日期为 2026-09-06。依赖的输入法前端和引擎独立分发，保留各自许可证。

## 雾凇拼音

来自 [iDvel/rime-ice](https://github.com/iDvel/rime-ice)，作者 iDvel 及其贡献者，项目许可证 GNU GPL v3.0。固定提交为 `fbb516b2786e4d5444383706d13c31c2e4d10c08`。

- `cn_dicts/8105.dict.yaml` 保存为 `data/sources/rime_ice_chars.dict.yaml`，保留上游注释。其注释署名维基词典《通用规范汉字表》拼音索引与北京语言大学荀恩东团队的 25 亿字语料汉字字频表。
- `cn_dicts/base.dict.yaml` 经字集、读音过滤后生成 `cn_dicts/suibi_words.dict.yaml`。上游列明华宇野风系统词库、[清华 THUOCL](https://github.com/thunlp/THUOCL)、[现代汉语常用词表](https://gist.github.com/indiejoseph/eae09c673460aa0b56db)、[腾讯词向量](https://ai.tencent.com/ailab/nlp/zh/download.html)及 Huandeep 的整理贡献，另参考多部汉语词典。完整原始注释可从 [固定版本原文件](https://github.com/iDvel/rime-ice/blob/fbb516b2786e4d5444383706d13c31c2e4d10c08/cn_dicts/base.dict.yaml) 阅读。
- `double_pinyin.schema.yaml` 的自然码拼写代数保存为 `data/natural_double_pinyin.json`，供普通双拼与辅助读音映射共用。

随笔的修改包括：限定规范汉字范围、过滤字表外词语、生成独立方案与词库名称、生成 Lua 查询数据，以及新增笔顺前缀筛选。数据继承上游署名和来源，不主张其为随笔原创。

## 笔顺

`data/sources/strokes.tsv` 来源于教育部发布的 [《通用规范汉字笔顺规范》GF 0023—2020](https://www.moe.gov.cn/jyb_sjzl/ziliao/A19/202103/W020210318300204215237.pdf)。保存 8,105 个字的序号、汉字与五类数字笔顺；抽取结果在前期研究中与公开笔顺数据逐字比对，字序和笔顺一致。这里只保存结构化笔顺事实，未打包原 PDF 的版式、说明文字或图像，也不将该规范标称为 GPL 授权作品。

转换约定：1 → h（横/提），2 → s（竖/竖钩），3 → p（撇），4 → n（点/捺），5 → z（折）。固定输入文件与原 PDF 的 SHA-256 见 [sources.json](data/sources.json)。

## Rime API

`tools/rime_api.py` 的 ctypes 结构依据 RIME Developers 的 `rime_api.h` 公共接口。接口来源：[librime 1.17.0](https://github.com/rime/librime/blob/1.17.0/src/rime_api.h)；保留其 [BSD 许可证](LICENSES/librime-BSD.txt)。测试用动态库由工具单独下载，不进入方案安装包。

微软双拼映射 `data/microsoft_double_pinyin.json` 提取自同一固定提交的 `iDvel/rime-ice/double_pinyin_mspy.schema.yaml` 中 `speller/algebra`（GPL-3.0）；该文件注明键位映射源于 `rime/rime-double-pinyin`。随笔保留分号 ing 和兼容别名，生成自己的方案及反查映射。哈希见 `data/sources.json`。
