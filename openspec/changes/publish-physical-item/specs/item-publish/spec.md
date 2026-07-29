## ADDED Requirements

### Requirement: 发布实体商品
系统 SHALL 提供通过闲鱼 PC 端发布全新实体商品的能力。

系统 SHALL 支持以下步骤：
1. 上传商品图片（调用 `upload_media`）
2. 构造发布 payload（标题、价格、描述、图片 URL、类目、运费等）
3. 调用 `mtop.idle.pc.idleitem.publish` 提交发布请求

#### Scenario: 成功发布实体商品
- **WHEN** 客户端提供商品标题、价格、描述和至少一张图片
- **THEN** 系统先上传图片获取 URL
- **THEN** 系统构造完整 payload 并调用 publish 接口
- **THEN** 系统返回发布结果，包含新商品的 `item_id`

#### Scenario: 缺少图片
- **WHEN** 客户端未提供任何商品图片
- **THEN** 系统返回错误，提示至少需要一张图片

#### Scenario: 发布失败 — 图片上传失败
- **WHEN** 上传图片时闲鱼接口返回错误
- **THEN** 系统返回错误信息，提示图片上传失败原因

### Requirement: 响应格式
发布结果 SHALL 包含以下字段：
- `success` (bool)：是否发布成功
- `item_id` (string)：新发布的商品 ID（成功时）
- `api` (string)：实际调用的 API 名称
- `raw` (object)：闲鱼接口的原始响应
