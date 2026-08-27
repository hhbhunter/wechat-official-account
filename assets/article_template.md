# 公众号图文模板

将下方结构作为内容生产骨架。正文使用 HTML（微信图文编辑器的 `content` 字段），
支持 `<p> <img> <strong> <em> <section> <h1>-<h3> <ul> <ol> <blockquote>` 等。

---

## 单篇文章 JSON（传给 `publish_draft.py add-draft --article`）

保存到文件（如 `article.json`）：

```json
{
  "title": "标题（建议 ≤ 64 字，含关键词）",
  "author": "公众号名称/作者",
  "digest": "摘要（选填，列表/分享卡片展示，≤ 120 字）",
  "content": "<!-- 正文 HTML，见下 -->",
  "thumb_media_id": "封面图 media_id（先 upload-image 拿到）",
  "content_source_url": "",
  "need_open_comment": 1,
  "only_fans_can_comment": 0
}
```

---

## 正文 HTML 模板

```html
<div>
  <h1 style="text-align:center;">标题</h1>
  <p style="text-align:center;color:#888;font-size:14px;">作者 · 2026-08-27</p>

  <p>开场白：用 1-2 句说清这篇文章解决什么问题、给读者什么价值。</p>

  <h2>一、小标题</h2>
  <p>段落正文，手机端每段 ≤ 5 行，字号 16-17px 最佳。</p>
  <img src="封面或配图 media_id 对应 url，或外链图片" alt="配图说明"/>

  <h2>二、小标题</h2>
  <blockquote>金句/要点提炼，视觉上更突出。</blockquote>

  <h2>三、小结与行动建议</h2>
  <p>用 3 条以内要点收尾，给出明确的下一步动作。</p>

  <p style="color:#888;font-size:13px;">—— 原创内容，转载请注明出处 ——</p>
</div>
```

---

## 写作检查清单

- [ ] 标题含核心关键词，长度 ≤ 64 字
- [ ] 有摘要（digest），提升列表点击率
- [ ] 封面图已上传并拿到 `thumb_media_id`
- [ ] 正文分 2-4 个小节，每段手机阅读友好
- [ ] 至少 1 张配图（提升完读率）
- [ ] 文末有引导关注/互动话术
