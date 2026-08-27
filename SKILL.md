---
name: wechat-official-account
description: 微信公众号内容生产发布助手 — 覆盖选题/写稿/排版，到调用公众平台 API 上传图片素材、新增草稿箱（draft/add）、发布（freepublish/submit）与群发（mass/sendall）。当用户要“写公众号文章”“生成图文”“发草稿”“群发推文”“运营公众号”时触发。从 .env 读取 AppID/AppSecret，内置测试凭据占位与账号能力校验。
agent_created: true
---

# 微信公众号内容生产发布助手

辅助完成「内容生产 → 素材上传 → 草稿箱 → 发布/群发」的全流程，并通过
`scripts/publish_draft.py` 直连微信公众平台开放接口落地执行。

## When to Use

- 用户要写 / 润色 / 排版公众号文章（单篇或多篇）
- 用户要“发到草稿箱”“发草稿”“存为草稿”
- 用户要“群发推文”“发布文章”到公众号
- 用户需要公众号图文结构模板、写作清单、配图建议

## Prerequisites

1. Python 3.8+ 与依赖：`pip install requests`
2. 凭据配置（二选一，脚本自动加载）：
   - 环境变量 `WECHAT_APPID` / `WECHAT_APPSECRET`
   - 或 `scripts/.env`（可复制根目录 `.env.example`）
3. **账号能力**（重要）：测试号 / 未认证订阅号不支持草稿与发布接口，
   真实发布需替换为「已认证订阅号」或「已认证服务号」凭据。详见
   `references/wechat_api.md` 的能力矩阵。

## Workflow

### 1. 内容生产

- 用 `assets/article_template.md` 的 JSON 结构与正文 HTML 模板组织内容。
- 标题 ≤ 64 字含关键词，写 digest 摘要，拆分 2-4 个小节。
- 如需配图，先调用素材上传拿到封面 / 配图 media_id（见步骤 2）。

### 2. 上传图片素材

```bash
python scripts/publish_draft.py upload-image ./cover.jpg
# 返回 media_id（封面用）与 url（正文 <img> 用）
```

### 3. 新增草稿

将文章写成 JSON 文件（参考模板），然后：

```bash
python scripts/publish_draft.py add-draft --article article.json --thumb <封面media_id>
# 返回草稿 media_id
```

### 4. 发布 / 群发（需人工复核）

> ⚠️ 安全护栏：`publish` 与 `mass` **必须加 `--confirm`** 才会真正调用接口，
> 否则脚本拒绝执行并打印复核清单。务必先在草稿箱人工复核内容后再确认。

- 发布（订阅号 / 服务号通用）：

  ```bash
  python scripts/publish_draft.py publish --media-id <草稿media_id> --confirm
  python scripts/publish_draft.py publish-status --publish-id <publish_id>
  ```

- 群发（需已认证服务号）：

  ```bash
  python scripts/publish_draft.py mass --media-id <草稿media_id> [--tag-id 123] --confirm
  ```

- `add-draft` 会自动扫描标题/摘要/正文，命中医疗、金融、新闻、特殊食品等关键词时
  打印 `[资质提醒]`（仅提醒，不拦截）。

### 5. 查看草稿

```bash
python scripts/publish_draft.py list-drafts --count 20
```

## Scripts

- `scripts/publish_draft.py` — 主脚本，封装 token 缓存、素材上传、草稿、
  发布、群发与查询。子命令：`token` / `upload-image` / `add-draft` /
  `list-drafts` / `publish` / `publish-status` / `mass`。

## References

- `references/wechat_api.md` — 接口端点、请求体、errcode 与账号能力矩阵。
- `references/compliance.md` — 合规风险、特殊行业资质与发布前检查清单（必读）。
- `assets/article_template.md` — 图文 JSON 结构与正文 HTML 模板、写作清单。

## Notes

- access_token 每日限 2000 次且 2 小时过期，脚本已内置内存缓存，勿重复申请。
- 草稿正文为 HTML，外链与部分标签受限；图片用永久素材 media_id / url。
- 群发 1 次/天（订阅号）或 4 次/月（服务号），且群发后不可撤回。
