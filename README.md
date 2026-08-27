# 微信公众号内容生产发布助手 · 使用说明

辅助完成「内容生产 → 素材上传 → 草稿箱 → 发布 / 群发」全流程。核心脚本
`scripts/publish_draft.py` 直连微信公众平台开放接口落地执行。

---

## 一、目录结构

```
wechat-official-account/
├── SKILL.md                      # 技能主文档(触发场景 / 工作流 / 资源引用)
├── README.md                     # 本使用说明
├── scripts/
│   ├── publish_draft.py          # 主脚本:token / 上传 / 草稿 / 发布 / 群发
│   └── .env.example              # 凭据配置示例
├── references/
│   └── wechat_api.md             # 接口端点 / errcode / 账号能力矩阵
└── assets/
    └── article_template.md       # 图文 JSON 结构 + 正文 HTML 模板 + 写作清单
```

---

## 二、安装与发布状态

- **本地已发布**:已复制到 `C:\Users\test\.workbuddy\skills\wechat-official-account\`,
  WorkBuddy 会自动发现并在你说「写公众号文章 / 发草稿 / 群发推文」等时触发。
- **源文件**:`C:\workbuddy\wechat-official-account\`(开发与备份用)。
- **分发包**:`C:\workbuddy\wechat-official-account.zip`(用 `package_skill.py` 校验打包)。

---

## 三、配置凭据

脚本按优先级读取凭据:
1. 环境变量 `WECHAT_APPID` / `WECHAT_APPSECRET`
2. 脚本同目录 `scripts/.env`

**步骤:**
1. 复制示例:`scripts/.env.example` → `scripts/.env`
2. 填入真实凭据:
   ```
   WECHAT_APPID=wx你的appid
   WECHAT_APPSECRET=你的appsecret
   ```
3. 凭据来源:
   - 正式号:公众平台 → 设置与开发 → 基本配置 → 开发者 ID / AppSecret
   - 测试号(沙箱):https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login

> `.env` 含密钥,**切勿提交到 Git 或外传**。

---

## 四、依赖

```bash
pip install requests
```

---

## 五、快速开始(命令行)

进入脚本目录后执行:

```bash
# 1) 获取 access_token(验证连通性)
python publish_draft.py token

# 2) 上传封面 / 配图,返回 media_id 与 url
python publish_draft.py upload-image ./cover.png

# 3) 新增图文草稿(文章用 JSON 描述,模板见 assets/article_template.md)
python publish_draft.py add-draft --article ./article.json --thumb <封面media_id>

# 4) 列出草稿箱
python publish_draft.py list-drafts --count 20

# 5) 发布草稿(订阅号 / 服务号通用)
python publish_draft.py publish --media-id <media_id>

# 6) 查询发布状态
python publish_draft.py publish-status --publish-id <publish_id>

# 7) 群发(需已认证服务号)
python publish_draft.py mass --media-id <media_id> [--tag-id <标签id>]
```

---

## 六、推荐工作流

1. **写稿**:用 `assets/article_template.md` 的 HTML 排版模板产出正文,
   套到 `article.json`(含 title / thumb_media_id / digest / content 等字段)。
2. **备图**:`upload-image` 上传封面与配图,拿到 `media_id` 回填到 article。
3. **入草稿**:`add-draft` 写入草稿箱,到公众平台核对排版。
4. **发布 / 群发**:确认无误后 `publish`(定时发布)或 `mass`(即时群发)。

---

## 七、账号能力矩阵(关键限制)

| 接口 | 测试号(沙箱) | 未认证订阅号 | 已认证订阅号 | 已认证服务号 |
|------|:--:|:--:|:--:|:--:|
| token / 上传图片 | ✅ | ✅ | ✅ | ✅ |
| draft/add 草稿 | ❌ | ❌ | ✅ | ✅ |
| freepublish 发布 | ❌ | ❌ | ✅ | ✅ |
| mass 群发 | ❌ | ❌ | ❌ | ✅ |

> 用**测试号**只能验证 `token` 和 `upload-image`;其余接口需换成**已认证账号**凭据,
> 否则返回 `48001 api unauthorized`。

---

## 八、常见错误排查

| 现象 | 原因 / 处理 |
|------|------|
| `未配置 WECHAT_APPID / WECHAT_APPSECRET` | 检查 `.env` 或环境变量 |
| `40013 invalid appid` | AppID 填错 |
| `40125 invalid appsecret` | AppSecret 错误 / 已被重置 |
| `48001 api unauthorized` | 当前账号无该接口权限(见能力矩阵) |
| `45009 api freq out of limit` | 接口调用超限,稍后重试 |
| 上传图片报 `41005` | 文件不存在或格式非图片 |

---

## 九、安全与合规

- `.env` 密钥不入库、不外传;正式发布前确认 `.gitignore` 已忽略。
- 群发内容遵守平台规则,避免诱导分享、抄袭等违规导致封禁。
- 草稿发布后历史记录可删不可撤回,正式群发前务必在草稿箱复核。
- 完整合规要点与发布前检查清单见 **`references/compliance.md`**。

### 9.1 发布 / 群发人工复核闸门

`publish` 与 `mass` 命令**必须加 `--confirm`** 才会真正调用接口;否则脚本拒绝执行
并打印复核清单。这是防止自动化误发的关键护栏:

```bash
# 不加 --confirm → 拦截并打印检查清单,exit 1
python publish_draft.py publish --media-id <id>
python publish_draft.py mass --media-id <id> --tag-id <tag>

# 人工复核无误后,显式确认
python publish_draft.py publish --media-id <id> --confirm
python publish_draft.py mass --media-id <id> --confirm
```

### 9.2 特殊行业资质提醒

`add-draft` 会扫描标题/摘要/正文,命中医疗、金融、新闻、特殊食品等关键词时打印
`[资质提醒]`,提示可能需相应资质(仅提醒,不拦截),详见 `references/compliance.md`。
