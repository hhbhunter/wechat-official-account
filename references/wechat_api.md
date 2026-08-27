# 微信公众平台 API 参考（内容 / 草稿 / 发布）

本文档供 WorkBuddy 在调用微信公众平台接口时参考。所有接口 base:
`https://api.weixin.qq.com/cgi-bin`

---

## 鉴权：access_token

```
GET /token?grant_type=client_credential&appid=APPID&secret=APPSECRET
```

返回：`{ "access_token": "...", "expires_in": 7200 }`

- 每日调用上限 2000 次，有效期 2 小时，需缓存复用（脚本已内置内存缓存）
- 出错返回：`{ "errcode": 40013, "errmsg": "invalid appid" }`

常用 errcode：

| code | 含义 |
|------|------|
| 40013 | 不合法 AppID |
| 40001 | 无效凭证（令牌过期/错误） |
| 42001 | access_token 超时 |
| 48001 | API 功能未授权（账号类型不支持，如测试号/未认证订阅号） |
| 45009 | 接口调用超限 |

---

## 上传图片素材（永久）

```
POST /material/add_material?access_token=TOKEN&type=image
Content-Type: multipart/form-data，字段 media=文件
```

返回：`{ "media_id": "...", "url": "https://..." }`

- 用于封面图（`thumb_media_id`）与正文 `<img>` 引用的素材
- 临时素材有效期 3 天；草稿正文图片建议用永久素材

---

## 新增草稿

```
POST /draft/add?access_token=TOKEN
```

Body：

```json
{
  "articles": [
    {
      "title": "标题",
      "author": "作者",
      "digest": "摘要（选填，列表展示）",
      "content": "<p>正文（HTML）</p>",
      "content_source_url": "原文链接（选填）",
      "thumb_media_id": "封面图 media_id（必填）",
      "need_open_comment": 0,
      "only_fans_can_comment": 0
    }
  ]
}
```

返回：`{ "media_id": "草稿 media_id" }`

- 多篇图文：articles 数组放多篇（最多 8 篇）
- content 为 HTML，支持 `<p><img><strong><section>` 等；外链受限

---

## 获取草稿列表

```
POST /draft/batchget?access_token=TOKEN
Body: { "offset": 0, "count": 20, "no_content": 0 }
```

- `no_content=1` 不返回正文（省流量）
- 返回：`{ "total_count": N, "item_count": M, "item": [ { "media_id":.., "content": {...}, "update_time":.. } ] }`

---

## 发布（草稿 → 已发布）

```
POST /freepublish/submit?access_token=TOKEN
Body: { "media_id": "草稿 media_id" }
```

返回：`{ "publish_id": "publish_xxx" }`

查询状态：

```
POST /freepublish/get?access_token=TOKEN
Body: { "publish_id": "publish_xxx" }
```

返回：`{ "publish_status": 0/1/2, "article_id": "已发布图文 id", ... }`

- `publish_status`：0=发布中，1=发布成功，2=发布失败

---

## 群发（需已认证服务号）

```
POST /message/mass/sendall?access_token=TOKEN
```

Body（全部粉丝）：

```json
{
  "filter": { "is_to_all": true },
  "mpnews": { "media_id": "草稿 media_id" },
  "msgtype": "mpnews",
  "send_ignore_reprint": 0
}
```

按标签：

```json
{ "filter": { "is_to_all": false, "tag_id": 123 }, "mpnews": {...}, "msgtype": "mpnews" }
```

---

## 能力矩阵（账号类型）

| 接口 | 测试号(沙箱) | 未认证订阅号 | 已认证订阅号 | 已认证服务号 |
|------|:---:|:---:|:---:|:---:|
| token | ✅ | ✅ | ✅ | ✅ |
| 上传图片 | ✅ | ✅ | ✅ | ✅ |
| draft/add | ❌ 48001 | ❌ 48001 | ✅ | ✅ |
| freepublish/submit | ❌ | ❌ | ✅ | ✅ |
| mass/sendall | ❌ | ❌ | ❌ | ✅ |

> **关键结论**：测试号与未认证订阅号**无法**走本 skill 的
> `add-draft` / `publish` / `mass`。用于真实发布时，把 `.env` 里的
> AppID/AppSecret 换成「已认证订阅号或服务号」的凭据。
