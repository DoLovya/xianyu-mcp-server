# pure-python-sign

## 概述

提供纯 Python 实现的签名生成与设备标识生成能力，替代原通过 `execjs` 调用 JS 文件的实现方式。

## 功能要求

### REQ-1: 生成签名

- 输入：时间戳 `t`（毫秒字符串）、`token`（从 Cookie `_m_h5_tk` 提取的签名令牌）、`data`（请求体 JSON 字符串）
- 输出：MD5 十六进制签名
- 算法：`MD5(token + "&" + t + "&" + "34839810" + "&" + data)`
- 必须与 JS 版本 `generate_sign` 的输出完全一致

### REQ-2: 生成消息 MID

- 输出：格式为 `{随机3位数字}{当前毫秒时间戳} 0` 的字符串
- 等价于 JS 的 `generate_mid`

### REQ-3: 生成 UUID

- 输出：格式为 `-{当前毫秒时间戳}1` 的字符串
- 等价于 JS 的 `generate_uuid`

### REQ-4: 生成设备 ID

- 输入：`user_id` 字符串
- 输出：UUID v4 格式（不含分隔符或含连字符）+ `-` + `user_id`
- 等价于 JS 的 `generate_device_id`

### REQ-5: 向后兼容

- 函数签名（参数顺序、返回值类型）与原 JS 调用保持一致
- `goofish_utils.py` 中 `decrypt` 函数保持原有 execjs 实现不变
