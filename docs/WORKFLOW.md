# 开发与验证

需要 Python 3.10 或以上。以下命令在仓库根目录执行；Windows 可将 `python` 换成 `py`，Linux 可用虚拟环境安装开发依赖。

```bash
python -m pip install -r requirements-dev.txt
python tools/build.py --fetch
python tools/build.py --check
python -m unittest discover -s tests -v
```

`--fetch` 仅在缓存不存在时下载固定版本上游词库；所有输入均校验 SHA-256。生成物不得直接手改。普通安装只需要 `requirements.txt` 的 PyYAML；运行输入法不需要 Python 或 Lupa。

## 真实引擎测试

测试创建独立 `.build/engine-*` 目录，编译三套方案与不加载随笔 Lua 的普通流程对照方案，不读取或修改实际用户词库。

Windows x64：

```powershell
py tools/prepare_windows_runtime.py
py tools/test_engine.py --library .cache/runtime/dist/lib/rime.dll --output .build/windows-results.json
```

此工具下载并校验官方 librime 1.17.0 的固定归档，使用 Windows `tar` 解包，不安装系统服务。若系统 `tar` 不支持 7z，可手动解压同一校验通过的归档至该目录。

已安装开发用 Rime 库的 Debian amd64：

```bash
python3 tools/test_engine.py --library /usr/lib/x86_64-linux-gnu/librime.so.1 --plugin /usr/lib/x86_64-linux-gnu/rime-plugins/librime-lua.so --output .build/debian-results.json
```

CachyOS / Arch x64（需要 `librime`）：

```bash
python3 tools/test_engine.py --library /usr/lib/librime.so.1 --plugin /usr/lib/rime-plugins/librime-lua.so --output .build/arch-results.json
```

无系统安装权限的 Debian 13 可运行 `python3 tools/prepare_debian_runtime.py`，将缺失依赖解包至项目 `.cache/debian/root`。运行测试时需把其 `usr/lib/x86_64-linux-gnu` 加入 `LD_LIBRARY_PATH`，并将 `--library`、`--plugin` 改为该目录内的实际路径。此工具使用当前 Debian 软件源，不是固定版本容器的替代品。

`.github/workflows/test.yml` 配置 Windows、Debian 13 和 Arch 兼容引擎检查；配置存在不表示远端已经运行，也不能替代 CachyOS 桌面验收。

## 安装预览与打包

```bash
python tools/install.py --target .build/install-preview --enable --dry-run
python tools/package.py
```

输出 `dist/rime-suibi-pinyin-0.2.0.zip`、`dist/rime-suibi-double-pinyin-0.2.0.zip`、`dist/rime-suibi-mspy-0.2.0.zip` 和 `dist/SHA256SUMS`。包内包括运行方案、GPL 正文、来源数据、构建工具和测试，不包括动态库、个人 Rime 数据、Git 元数据或密钥。每个 ZIP 只包含一个可安装方案，适用于三个平台，不提供独立 EXE/DEB 安装器。

提交前查看 `git status --short`、生成一致性及暂存差异；仅纳入本任务路径。提交、推送和发布分别按用户授权执行。

独立包保留所有生成源；若在单方案解压目录开发，先运行 `build.py --fetch` 会生成全部三方案，再运行 `--check`。
