# 随笔拼音 · Suibi

**拼音为主，重码补笔。**

随笔拼音是基于 Rime 的简体中文输入方案，提供全拼、自然码双拼和微软双拼。在找不到目标单字时，按反引号，再按笔顺补几笔，缩小候选范围。

| 输入方式 | 示例 | 含义 |
| --- | --- | --- |
| 随笔全拼 | `zhongguo` | 正常输入“中国” |
| 随笔双拼（自然码） | `vsgo` | 自然码双拼输入“中国” |
| 随笔微软双拼 | `vsgo` / `y;` | 输入“中国” / ying 音节 |
| 全拼辅助 | `` zhong`phh `` | 读作 zhong，前三笔为撇横横的单字 |
| 双拼辅助 | `` vs`phh `` | 自然码、微软双拼均可用 |
| 纯笔画反查 | `` `szhs `` | 找到“中”，候选旁显示 `(zhong)` |

笔画键：`h` 横/提、`s` 竖/竖钩、`p` 撇、`n` 点/捺、`z` 折。

## 当前功能

- 全拼、自然码双拼、微软双拼共用简体词库及笔画数据。
- 正常输入词语和句子，单个完整音节可按需追加笔画辅助。
- 辅助候选必须同时满足读音、简体字集和笔顺前缀条件；允许继续输入超过三笔。
- Windows 使用小狼毫，CachyOS 与 Debian 使用 Fcitx5-Rime。
- 不知道读音时，直接按反引号，再按笔顺输入五类笔画，候选旁显示完整拼音。

## 安装与试用

当前版本 **v0.2.0**。选择自己熟悉的方案下载：

| 方案 | 独立安装包 | 方案标识 |
| --- | --- | --- |
| 随笔全拼 | [下载 ZIP](https://github.com/PlayerAI/rime-suibi/raw/refs/heads/main/dist/rime-suibi-pinyin-0.2.0.zip) | `suibi_pinyin` |
| 随笔双拼（自然码） | [下载 ZIP](https://github.com/PlayerAI/rime-suibi/raw/refs/heads/main/dist/rime-suibi-double-pinyin-0.2.0.zip) | `suibi_double_pinyin` |
| 随笔微软双拼 | [下载 ZIP](https://github.com/PlayerAI/rime-suibi/raw/refs/heads/main/dist/rime-suibi-mspy-0.2.0.zip) | `suibi_mspy` |

每包均适用于 Windows、CachyOS 和 Debian，包含所选方案、完整词库、Lua 文件与源码，无需另外安装其他随笔方案。[SHA-256 校验清单](dist/SHA256SUMS)。

Windows 配合小狼毫，CachyOS、Debian 配合 Fcitx5-Rime；运行需要 librime-lua。无需修改 Rime 引擎。

下载并解压所需包；安装器自动只启用该包的方案。也可同时安装多个包，共享词库。源码目录安装可加 `--scheme suibi_pinyin`、`--scheme suibi_double_pinyin` 或 `--scheme suibi_mspy` 选择单个方案；不指定则安装全部。

先按 [安装说明](docs/INSTALL.md) 安装对应前端，再进入解压后的目录（包含 `README.md` 和 `package.json`）执行：

```powershell
# Windows，Python 3.10 或以上
py -m pip install -r requirements.txt
py tools/install.py --enable
```

```bash
# CachyOS / Debian：先安装 python-yaml / python3-yaml
python3 tools/install.py --enable
```

从 GitHub 源码安装时，例如只选微软双拼：

```bash
python tools/install.py --scheme suibi_mspy --enable
```

安装器会保留现有方案；如只想使用随笔微软双拼，可在小狼毫方案选单设置中取消其他方案。重新部署后，在 Rime 方案选单中选择所安装的随笔方案。自定义用户目录请传入 `--target`；`--dry-run` 可预览操作。覆盖前自动备份，详见安装说明。

## 怎么用

正常输入时沿用 Rime 拼音组词、整句和用户词频学习。想找单字时，输入一个完整音节（双拼为两键），按反引号，再按目标字的**笔顺从头**补笔。例如 `` zhong`phh `` 或 `` vs`phh `` 可找“重”“种”等字。

- `Space` / `Enter` 确认候选，`1`—`5` 选字，`-` / `=` 翻页。
- `Backspace` 逐笔删除；删掉反引号后恢复普通拼音。`Esc` 取消本次输入。
- 没有拼音时输入 `` `szhs ``，可以找到“中”，候选旁显示 `(zhong)`，选择后只输入“中”。多音字列出词库已有读音，不标声调。
- 单独按反引号进入反查，接着输入笔画才显示候选；连续按两次反引号输入一个字面符号。
- 微软双拼的 `;` 用于韵母 ing，例如 `y;` 是 ying。
- 辅助状态只接受五个笔画字母；无匹配时保持空候选，不用近似结果替代。
- 辅助状态的 `Shift` 不切英文，左右移动不进入音节内部；需要改音节时先退格退出辅助。

## 数据与验证

字集限定为《通用规范汉字表》的 8,105 字（含简繁共用字），其中 **8,104 字、8,676 个字音、540,478 条词语**进入拼音词库。来源缺少“呣”的可用普通拼音读音，笔画反查仍可找到它，旁注“读音未收录”。

小狼毫 0.17.4 / librime 1.13.1 和 Debian 13 / WSL2 各通过 28 项实际引擎检查，另有 12 项核心与安装测试通过；微软双拼 v0.2.0 已在本机小狼毫安装并成功部署。详情见 [验证记录](docs/STATUS.md)。CachyOS 尚未在实机桌面测试。

辅助和反查候选按静态字频排序，暂不学习个人选字习惯；普通拼音继续使用 Rime 用户词典学习。这里“学拼音”指通过候选注释了解读音。当前不支持词语整串辅码、字表外汉字或声调标注。

## 开发

生成文件已随项目提供；普通安装不用下载和重建词库。修改方案或数据请修改生成源，再运行构建和验证，见 [开发流程](docs/WORKFLOW.md)。[文档导航](docs/INDEX.md) 列出实现结构、来源和当前状态。

## 开源许可

项目采用 **GNU GPL v3.0（GPL-3.0-only）**，详见 [LICENSE](LICENSE)。感谢 Rime、雾凇拼音及其数据贡献者。第三方署名、原始来源和修改说明见 [NOTICE.md](NOTICE.md)，输入文件版本与 SHA-256 见 [data/sources.json](data/sources.json)。
