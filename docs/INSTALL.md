# 安装随笔 v0.3.0

**v0.3.0 新增词语首字辅助。升级时执行安装命令后重新部署；更新需同时复制方案 YAML 和 Lua 文件。**

每种方案各有一个独立包，每包均适用于 Windows、CachyOS 和 Debian。安装前需有支持 librime-lua 模块的 Rime 前端。下列命令安装系统依赖；随笔文件本身安装到当前用户目录，无需管理员权限。选择全拼 `rime-suibi-pinyin-0.3.0.zip`、自然码 `rime-suibi-double-pinyin-0.3.0.zip` 或微软 `rime-suibi-mspy-0.3.0.zip`。下载源码或解压所选包后，在包含 README 的目录执行随笔安装命令。

## Windows

1. 安装 [小狼毫官方发行版](https://github.com/rime/weasel/releases)。如已经安装，先从托盘菜单打开“用户文件夹”，确认实际路径。
2. 使用 Python 3.10 或以上执行：

```powershell
py -m pip install -r requirements.txt
py tools/install.py --enable
```

默认位置为 `%APPDATA%\Rime`。自定义目录示例：

```powershell
py tools/install.py --target 'D:\RimeUser' --enable
```

3. 在小狼毫托盘菜单点击“重新部署”，等部署完成后，用 Rime 方案选单选择安装的随笔方案。常见选单快捷键是 `Ctrl+反引号`，以你的现有配置为准。

## CachyOS

使用 Fcitx5-Rime：

```bash
sudo pacman -S --needed fcitx5 fcitx5-rime fcitx5-configtool fcitx5-gtk fcitx5-qt python python-yaml
python3 tools/install.py --enable
```

当前 [Arch librime 包](https://archlinux.org/packages/extra/x86_64/librime/files/)包含 `rime-plugins/librime-lua.so`，无需另找独立 Lua 插件包。CachyOS 使用其兼容包的安装路线；当前源码已在 CachyOS 本机隔离引擎测试通过，桌面应用集成仍待人工验收。

在桌面的输入法设置中启用 Fcitx5，在 Fcitx5 配置工具中添加“中州韵 / Rime”，再从 Fcitx5 的 Rime 菜单重新部署。Wayland 下的启动与应用集成遵循桌面环境配置，参见 [Fcitx5 官方设置说明](https://fcitx-im.org/wiki/Setup_Fcitx_5)，不要直接覆盖现有会话环境变量。

## Debian

当前验证基线为 **Debian 13（trixie）**：

```bash
sudo apt update
sudo apt install fcitx5 fcitx5-rime fcitx5-config-qt fcitx5-frontend-gtk3 fcitx5-frontend-qt5 librime-plugin-lua python3 python3-yaml im-config
python3 tools/install.py --enable
```

Debian 将 [librime-plugin-lua](https://packages.debian.org/trixie/librime-plugin-lua) 单独打包，须显式安装。在 `im-config` 中选择 Fcitx5，按提示重新登录，再添加 Rime 输入法并重新部署。Fcitx5-Rime 包信息见 [Debian 官方包页](https://packages.debian.org/trixie/fcitx5-rime)。其他 Debian 版本未作为本轮验证基线。

两个 Linux 平台默认用户目录均为 `${XDG_DATA_HOME:-$HOME/.local/share}/fcitx5/rime`，可通过 `--target` 指定实际位置。

## 手动安装（无需 Python）

保持目录结构，把以下文件复制到 Rime 用户目录，覆盖同名文件前先备份：

- `suibi.dict.yaml` 和所选包内唯一的 `suibi_*.schema.yaml`
- `cn_dicts/suibi_chars.dict.yaml`、`cn_dicts/suibi_words.dict.yaml`
- `lua/suibi/` 内的六个 `.lua` 文件

在现有 `default.custom.yaml` 的 `patch` 中追加所选方案。若没有自定义方案列表，可使用以下追加写法；如已有 `schema_list` 或 `schema_list/+`，在现有列表追加，不能重复创建同名 YAML 键：

```yaml
patch:
  "schema_list/+":
    - schema: suibi_pinyin
```

上例为全拼；自然码改用 `suibi_double_pinyin`，微软改用 `suibi_mspy`。按需添加多行即可共存。然后重新部署并切换方案。

## 备份与恢复

脚本不传 `--enable` 时只安装随笔的运行文件，不修改选单。加 `--enable` 时合并现有配置值；首次追加会重新排版 YAML，注释不保留。原文件逐字节备份在用户目录的 `.suibi-backups/<时间与编号>/`。不支持的配置结构会在复制前报错，可改用手动启用。

用 `--dry-run` 预览目标和变动文件。重复执行相同安装不重复备份相同内容。

恢复时先退出输入法，查阅对应备份的 `manifest.json`：把 `replaced` 文件从备份复制回原位；若要撤销新增文件，只移除清单 `created` 中确认属于本次安装的文件。保留用户词库。若安装后又修改过配置，手动合并备份内容，以免覆盖后续改动。最后重新启动输入法并部署。

## 快速验收和排错

全拼输入 `zhongguo` 应有“中国”；双拼输入 `vsgo` 应有“中国”。随后输入 `` zhong`phh `` 或 `` vs`phh ``，候选应只剩对应读音且以撇横横起笔的字。退格删除反引号后，应恢复正常拼音候选。

若方案不存在，检查用户目录与 `default.custom.yaml`，并确认重新部署完成。若普通拼音可用但辅助无效，检查部署日志是否出现 Lua 模块加载错误，确认 `lua/suibi/` 完整、前端包含匹配的 librime-lua；不要混装来自不同版本的动态库。初次部署会编译约 54 万条词语，实际时间取决于设备。

独立包中 `package.json` 指定默认安装方案，`--enable` 只启用该方案；保留此文件。源码目录中可传 `--scheme suibi_pinyin`、`--scheme suibi_double_pinyin` 或 `--scheme suibi_mspy`，省略则安装全部。手动复制不需要复制 `package.json`。各方案共享同版本的词库和 Lua 文件，建议保持版本一致。

词语验收：三种方案均可输入 `` jilu`n `` 查“记录”，输入 `` jilu`z `` 查“纪录”。候选旁应显示“首字”，预编辑区显示已输入的笔画。Enter、Space、数字键均应只提交词语；退格删掉反引号恢复普通候选。

反查验收：空输入时键入 `` `szhs ``，应可找到“中”及 `(zhong)` 注释；连续两个反引号输入一个字面反引号。
