## ADDED Requirements

### Requirement: 编辑商品信息
系统 SHALL 提供编辑已发布商品信息的能力，支持修改标题、价格、描述、图片等核心字段。

系统 SHALL 提供两种调用模式：
- **快速编辑模式**：客户端只需指定 `item_id` 和需要修改的字段，其余字段自动从当前商品详情补全
- **直接编辑模式**：客户端直接提供完整 `payload`，跳过详情读取步骤

#### Scenario: 快速编辑模式 — 修改商品标题和价格
- **WHEN** 客户端调用 `edit_item`，指定 `item_id`、`title="新标题"`、`price="99.00"`
- **THEN** 系统先自动调用 `get_item_edit_detail` 获取当前商品全部字段
- **THEN** 系统用客户端指定的 `title` 和 `price` 覆盖对应字段
- **THEN** 系统调用 `edit_item` 提交编辑请求
- **THEN** 系统返回编辑结果（成功/失败及详情）

#### Scenario: 直接编辑模式 — 提供完整 payload
- **WHEN** 客户端调用 `edit_item`，提供 `item_id` 和完整的 `payload` 参数
- **THEN** 系统跳过详情读取步骤，直接调用 `edit_item` 提交 payload
- **THEN** 系统返回编辑结果

#### Scenario: 编辑失败 — 虚拟商品
- **WHEN** 客户端尝试编辑一个虚拟/数字商品
- **THEN** 闲鱼接口返回错误，系统如实透传错误信息
- **THEN** 系统不会在工具层拦截或做特殊处理

#### Scenario: 编辑失败 — 未找到商品
- **WHEN** 客户端指定的 `item_id` 不存在或已删除
- **THEN** 系统返回错误信息，提示商品不存在

### Requirement: 响应格式
编辑结果 SHALL 包含以下字段：
- `success` (bool)：是否编辑成功
- `item_id` (string)：被编辑的商品 ID
- `api` (string)：实际调用的 API 名称
- `raw` (object)：闲鱼接口的原始响应
