# `mtop.idle.web.xyh.item.list` 接口记录

## 目的

用于获取指定用户个人主页下的商品列表，支持分页，并可返回分组信息。

本仓库已确认该接口可用于拉取当前登录账号自己的全部商品列表。

## 取证来源

### 浏览器网络抓包

- 页面：`https://www.goofish.com/personal?userId=2206538887867`
- 关键请求：
  - `POST https://h5api.m.goofish.com/h5/mtop.idle.web.xyh.item.list/1.0/`

### 前端源码定位

来源文件：

- `https://g.alicdn.com/idle-pc/xy-site/0.0.168/js/p_personal-index.js`

关键调用逻辑：

```js
mtop.idle.web.xyh.item.list
```

前端封装等价参数：

```js
{
  api: "mtop.idle.web.xyh.item.list",
  v: "1.0",
  data: {
    needGroupInfo,
    pageNumber,
    userId,
    pageSize: 20,
    groupName,
    groupId,
    defaultGroup,
    groupSortId,
    filterPanelGroupId,
    nextPageModel,
    nextPageNum
  }
}
```

## 请求信息

### URL

```text
https://h5api.m.goofish.com/h5/mtop.idle.web.xyh.item.list/1.0/
```

### Query 参数

```text
jsv=2.7.2
appKey=34839810
v=1.0
type=originaljson
accountSite=xianyu
dataType=json
timeout=20000
api=mtop.idle.web.xyh.item.list
sessionOption=AutoLoginOnly
spm_cnt=a21ybx.personal.0.0
sign=<基于 token+t+data 生成>
t=<毫秒时间戳>
```

### Body

表单字段：

```text
data=<JSON 字符串>
```

第一页请求示例：

```json
{
  "needGroupInfo": true,
  "pageNumber": 1,
  "userId": "2206538887867",
  "pageSize": 20
}
```

下一页请求示例：

```json
{
  "pageNumber": 2,
  "userId": "2206538887867",
  "pageSize": 20,
  "groupName": "综合",
  "groupId": 47664662,
  "defaultGroup": true,
  "nextPageModel": "<第一页返回值>",
  "nextPageNum": "<第一页返回值>"
}
```

## 响应结构

顶层关键字段：

```json
{
  "ret": ["SUCCESS::调用成功"],
  "data": {
    "cardList": [],
    "itemGroupList": [],
    "nextPage": true,
    "nextPageNum": "...",
    "nextPageModel": "...",
    "topItem": {},
    "totalCount": 26
  }
}
```

### `itemGroupList`

示例分组：

```json
[
  { "groupId": 47664662, "groupName": "综合", "itemNumber": 26, "groupType": 0, "defaultGroup": true },
  { "groupId": 47664663, "groupName": "在售", "itemNumber": 17, "groupType": 0, "defaultGroup": true },
  { "groupId": 47664664, "groupName": "已售出", "itemNumber": 9, "groupType": 1, "defaultGroup": true }
]
```

### `cardList`

单个商品卡片关键字段：

```json
{
  "cardData": {
    "id": "814648814870",
    "title": "Python远程安装！",
    "itemStatus": 0,
    "priceInfo": { "preText": "¥", "price": "10" },
    "picInfo": { "picUrl": "http://img.alicdn.com/..." },
    "detailParams": {
      "itemId": "814648814870",
      "categoryId": 50023914,
      "title": "Python远程安装！",
      "soldPrice": "10"
    }
  },
  "cardType": 1003
}
```

## 已验证行为

- 单页默认 `pageSize=20`
- 账号 `2206538887867` 当前共 26 个商品
- 第 1 页返回 20 条
- 第 2 页返回 6 条
- 聚合两页后可拿全量商品列表

## 当前在仓库中的用途

- `third_party/XianYuApis/goofish_apis.py`：底层 HTTP 封装
- `.mcp/XianYuApis_MCP/tools/xianyu_api_tools.py`：MCP 工具聚合
- `.mcp/XianYuApis_MCP/server.py`：对外暴露 `list_my_items` 工具
