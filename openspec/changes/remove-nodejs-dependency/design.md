## Context

当前 `third_party/XianYuApis/utils/goofish_utils.py` 通过 `execjs` 调用 `static/goofish_js_version_2.js` 中的 JS 函数。`execjs` 内部依赖 Node.js 运行时，增加了环境配置成本和潜在的跨平台兼容问题。

涉及替换的 4 个函数全部使用 JS 标准库或纯计算逻辑，无需浏览器 API，Python 标准库 `hashlib`、`uuid`、`time`、`random` 可完全覆盖。

`decrypt` 函数（自定义 protobuf 反序列化，~490 行 JS 逻辑）不在 MCP 服务调用链中，仅在 `goofish_live.py`（WebSocket 消息监听）中使用，保留不动。

## Goals / Non-Goals

**Goals:**
- 4 个 execjs 调用替换为纯 Python 实现，行为完全一致
- 移除 `pyproject.toml` 中的 `PyExecJS` 依赖
- `README.md` 环境要求去掉 Node.js
- 当前所有 MCP 工具行为不受影响

**Non-Goals:**
- 不重构 `decrypt`（保持现有 execjs 实现）
- 不删除 JS 源文件（`decrypt` 仍需要）
- 不修改 `goofish_live.py`
- 不修改 MCP 层接口

## Decisions

### 1. 在 `goofish_utils.py` 原地替换 vs 新建模块
- 选择：**原地替换**
- 理由：函数签名不变，调用方零改动。新建模块会增加一个间接层，且原文件已有其他工具函数（Cookie 处理等），拆出来没有明显收益。

### 2. 实现方式：逐函数独立 vs 统一封装
- 选择：**逐函数独立**
- 理由：与 JS 原结构的调用方式一致，每个函数独立可测、可验证

### 3. `decrypt` 处理方式
- 选择：**保留 execjs，运行时条件导入**
- 方案：
  ```python
  try:
      _have_execjs = True
      xianyu_js = execjs.compile(...)
  except ImportError:
      _have_execjs = False

  def decrypt(data):
      if not _have_execjs:
          raise RuntimeError("decrypt 需要 PyExecJS / Node.js")
      return xianyu_js.call('decrypt', data)
  ```
- 理由：避免强制安装 `PyExecJS`，但 `decrypt` 用户仍可自行安装使用

### 4. 验证策略
- 本地运行原 JS 生成一组输入-输出对
- Python 实现逐条对比，确认结果一致

## Risks / Trade-offs

- **[兼容性] 未来 JS 签名算法更新** → Python 侧需要同步更新。但签名算法（MD5 拼接）属于闲鱼 mtop 协议的稳定部分，高频更新的可能性低。
- **[decrypt 的 execjs 条件导入] 低风险场景** → MCP 层不会触发此路径，仅影响 `goofish_live.py` 用户。后者已声明 Node.js 需求。
