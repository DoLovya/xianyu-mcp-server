## ADDED Requirements

### Requirement: Trae can configure cookie via env
当 MCP Server 通过 Trae 启动时，服务端 SHALL 支持通过进程环境变量进行首次配置，而无需编辑仓库内的 `.env` 文件。

#### Scenario: Configure by XIANYU_COOKIE
- **WHEN** 进程环境变量中存在非空 `XIANYU_COOKIE`
- **THEN** 服务端 SHALL 使用该 Cookie 作为登录凭据
- **AND THEN** 服务端 SHALL 不依赖仓库根目录 `.env` 是否存在或是否包含 `XIANYU_COOKIE`

#### Scenario: Configure by XIANYU_COOKIE_FILE
- **WHEN** 进程环境变量 `XIANYU_COOKIE` 为空或不存在
- **AND WHEN** 进程环境变量中存在非空 `XIANYU_COOKIE_FILE`
- **THEN** 服务端 SHALL 读取 `XIANYU_COOKIE_FILE` 指向的文件内容作为 Cookie

#### Scenario: Preference order
- **WHEN** `XIANYU_COOKIE` 与 `XIANYU_COOKIE_FILE` 同时为非空
- **THEN** 服务端 SHALL 优先使用 `XIANYU_COOKIE`

