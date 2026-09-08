# 文档导航

核查日期：2026-09-08。此目录只描述 `rime-suibi`。产品范围依据用户明确要求：简体、全拼和双拼加笔画、Windows/CachyOS/Debian、GPL；具体实现选择是 v0.3.0 当前行为，不另立未经批准的产品规范。

| 主题 | 权威入口 | 角色与适用范围 |
| --- | --- | --- |
| 项目定位与用法 | [README](../README.md) | PROJECT 入口，当前功能与范围 |
| 安装与恢复 | [INSTALL](INSTALL.md) | 三平台依赖、目录、启用与回退 |
| 结构边界 | [ARCHITECTURE](../ARCHITECTURE.md) | 实现事实、生成源与运行路径 |
| 开发命令 | [WORKFLOW](WORKFLOW.md) | 构建、测试、打包 |
| 进度与证据 | [STATUS](STATUS.md) | 本地验证事实和待验收项 |
| 第三方资料 | [NOTICE](../NOTICE.md) | 署名、来源、修改和许可说明 |
| 数据版本 | [sources.json](../data/sources.json) | 构建输入版本与哈希 |

生成内容应修改生成源，路径映射见 ARCHITECTURE。新的验证结果更新 STATUS，不以 CI 文件存在代替执行通过。
