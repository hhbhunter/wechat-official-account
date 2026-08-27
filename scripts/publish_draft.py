#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号内容生产发布脚本
============================

封装微信公众平台「内容 → 草稿 → 发布/群发」全流程 API。

功能:
  - 获取 access_token（带内存缓存，自动续期）
  - 上传永久图片素材（封面/配图），返回 media_id 与 url
  - 新增图文草稿到草稿箱（cgi-bin/draft/add）
  - 获取草稿列表（cgi-bin/draft/batchget）
  - 发布草稿（cgi-bin/freepublish/submit）—— 订阅号/服务号均可用
  - 群发（cgi-bin/message/mass/sendall）—— 需已认证服务号

凭据来源（按优先级）：
  1. 环境变量 WECHAT_APPID / WECHAT_APPSECRET
  2. 同目录 .env 文件

依赖：
  pip install requests

注意：
  微信「接口测试号（沙箱）」仅支持基础消息/菜单接口，**不支持** draft /
  freepublish / mass 等高级接口。本脚本可在测试号下获取 token 并上传图片，
  但 add-draft / publish / mass 需替换为「已认证订阅号或服务号」的真实凭据。
"""

import os
import sys
import json
import time
import argparse

try:
    import requests
except ImportError:
    sys.stderr.write("缺少依赖 requests，请先执行: pip install requests\n")
    sys.exit(1)


API_BASE = "https://api.weixin.qq.com/cgi-bin"


# ── 凭据加载 ────────────────────────────────────────────────
def _load_dotenv():
    """从脚本同目录的 .env 读取键值（若环境变量未设置）。"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


_load_dotenv()

APPID = os.environ.get("WECHAT_APPID", "")
APPSECRET = os.environ.get("WECHAT_APPSECRET", "")

_token_cache = {"token": None, "expire": 0}


def get_access_token(force=False):
    """获取 access_token，内置缓存与自动续期（提前 200 秒刷新）。"""
    global _token_cache
    if not force and _token_cache["token"] and time.time() < _token_cache["expire"]:
        return _token_cache["token"]
    if not APPID or not APPSECRET:
        raise RuntimeError(
            "未配置 WECHAT_APPID / WECHAT_APPSECRET。请在 .env 或环境变量中填写。"
        )
    resp = requests.get(
        f"{API_BASE}/token",
        params={"grant_type": "client_credential", "appid": APPID, "secret": APPSECRET},
        timeout=10,
    )
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"获取 access_token 失败: {data}")
    _token_cache["token"] = data["access_token"]
    _token_cache["expire"] = time.time() + int(data.get("expires_in", 7200)) - 200
    return _token_cache["token"]


def _post_json(path, payload, token=None):
    token = token or get_access_token()
    resp = requests.post(f"{API_BASE}/{path}?access_token={token}", json=payload, timeout=30)
    return resp.json()


def upload_image(path):
    """上传永久图片素材（封面/正文配图），返回 media_id 与 url。"""
    if not os.path.exists(path):
        raise RuntimeError(f"图片文件不存在: {path}")
    token = get_access_token()
    url = f"{API_BASE}/material/add_material?access_token={token}&type=image"
    with open(path, "rb") as f:
        resp = requests.post(url, files={"media": f}, timeout=60)
    data = resp.json()
    if "media_id" not in data:
        raise RuntimeError(f"上传图片失败: {data}")
    return data  # 含 media_id, url


def add_draft(articles):
    """新增图文草稿。articles 为单篇 dict 或 dict 列表。返回 media_id。"""
    if isinstance(articles, dict):
        articles = [articles]
    data = _post_json("draft/add", {"articles": articles})
    if "media_id" not in data:
        raise RuntimeError(f"新增草稿失败: {data}")
    return data


def list_drafts(offset=0, count=20, no_content=1):
    """获取草稿列表。no_content=1 不返回正文以省流量。"""
    data = _post_json(
        "draft/batchget",
        {"offset": offset, "count": count, "no_content": no_content},
    )
    if "errcode" in data and data["errcode"] != 0:
        raise RuntimeError(f"获取草稿列表失败: {data}")
    return data


def publish(media_id):
    """发布草稿（订阅号/服务号通用）。返回 publish_id，用 get_publish_status 轮询。"""
    data = _post_json("freepublish/submit", {"media_id": media_id})
    if "publish_id" not in data:
        raise RuntimeError(f"发布失败: {data}")
    return data


def get_publish_status(publish_id):
    """查询发布状态。"""
    return _post_json("freepublish/get", {"publish_id": publish_id})


def mass_send(media_id, is_to_all=True, tag_id=None):
    """群发图文（需已认证服务号）。"""
    if tag_id is not None:
        filter_field = {"is_to_all": False, "tag_id": tag_id}
    else:
        filter_field = {"is_to_all": is_to_all}
    payload = {
        "filter": filter_field,
        "mpnews": {"media_id": media_id},
        "msgtype": "mpnews",
        "send_ignore_reprint": 0,
    }
    data = _post_json("message/mass/sendall", payload)
    if "msg_id" not in data:
        raise RuntimeError(f"群发失败: {data}")
    return data


# ── 命令行接口 ──────────────────────────────────────────────
def _read_article(path):
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    if isinstance(obj, dict):
        return [obj]
    if isinstance(obj, list):
        return obj
    raise RuntimeError("article 文件必须是对象或数组")


# ── 合规辅助 ────────────────────────────────────────────────
# 特殊行业关键词 → 发布前需具备对应资质,命中则告警提醒(非拦截)。
SENSITIVE_INDUSTRY_KEYWORDS = {
    "医疗健康": ["医疗", "医院", "诊所", "问诊", "处方", "药品", "保健品", "减肥", "美容整形", "医美"],
    "金融": ["贷款", "理财", "证券", "股票", "基金", "保险", "信用卡", "P2P", "投资", "融资"],
    "新闻时政": ["新闻", "时政", "记者", "报道", "舆情", "政府"],
    "特殊食品": ["婴幼儿配方", "特殊医学用途", "保健食品"],
}


def check_sensitive_industry(text):
    """扫描文本命中特殊行业关键词,返回命中的行业类别列表。"""
    if not text:
        return []
    hits = []
    for industry, kws in SENSITIVE_INDUSTRY_KEYWORDS.items():
        if any(kw in text for kw in kws):
            hits.append(industry)
    return hits


def _require_human_review(action):
    """发布 / 群发前的人工复核闸门。未显式确认则拒绝执行并给出复核清单。"""
    checklist = [
        "1. 内容已通过草稿箱人工复核,无诱导分享/关注、色情低俗、虚假谣言、侵权等问题",
        "2. 如涉及医疗/金融/新闻等特殊行业,已取得相应资质",
        "3. 群发对象 / 标签选择正确(群发不可逆)",
        "4. AppSecret 等密钥未外泄,.env 未提交到版本库",
    ]
    sys.stderr.write(
        f"[拦截] {action} 需要人工复核确认。请逐项核对后加 --confirm 执行:\n"
        + "\n".join(checklist) + "\n"
    )
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="微信公众号内容发布工具")
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("token", help="获取并打印 access_token")

    p_img = sub.add_parser("upload-image", help="上传图片素材")
    p_img.add_argument("path", help="图片文件路径")

    p_add = sub.add_parser("add-draft", help="新增草稿")
    p_add.add_argument("--article", required=True, help="文章 JSON 文件（单篇或数组）")
    p_add.add_argument("--thumb", help="封面图 media_id（可先用 upload-image 获取）")

    p_list = sub.add_parser("list-drafts", help="列出草稿")
    p_list.add_argument("--count", type=int, default=20)
    p_list.add_argument("--offset", type=int, default=0)

    p_pub = sub.add_parser("publish", help="发布草稿（需 --confirm 人工复核）")
    p_pub.add_argument("--media-id", required=True)
    p_pub.add_argument("--confirm", action="store_true", help="确认已完成人工复核")

    p_st = sub.add_parser("publish-status", help="查询发布状态")
    p_st.add_argument("--publish-id", required=True)

    p_mass = sub.add_parser("mass", help="群发（需认证服务号，需 --confirm 人工复核）")
    p_mass.add_argument("--media-id", required=True)
    p_mass.add_argument("--tag-id", default=None, help="按标签群发（可选）")
    p_mass.add_argument("--confirm", action="store_true", help="确认已完成人工复核")

    args = parser.parse_args()

    try:
        if args.action == "token":
            print(get_access_token())
        elif args.action == "upload-image":
            print(json.dumps(upload_image(args.path), ensure_ascii=False, indent=2))
        elif args.action == "add-draft":
            articles = _read_article(args.article)
            if args.thumb:
                for a in articles:
                    a.setdefault("thumb_media_id", args.thumb)
            # 特殊行业资质提醒(非拦截)
            blob = " ".join(
                str(a.get("title", "")) + str(a.get("digest", "")) + str(a.get("content", ""))
                for a in articles
            )
            hits = check_sensitive_industry(blob)
            if hits:
                sys.stderr.write(
                    f"[资质提醒] 检测到可能涉及特殊行业: {', '.join(hits)}。"
                    "若未取得相应资质,发布可能被平台拦截或处罚。\n"
                )
            print(json.dumps(add_draft(articles), ensure_ascii=False, indent=2))
        elif args.action == "list-drafts":
            print(json.dumps(list_drafts(args.offset, args.count), ensure_ascii=False, indent=2))
        elif args.action == "publish":
            if not args.confirm:
                _require_human_review("publish")
            print(json.dumps(publish(args.media_id), ensure_ascii=False, indent=2))
        elif args.action == "publish-status":
            print(json.dumps(get_publish_status(args.publish_id), ensure_ascii=False, indent=2))
        elif args.action == "mass":
            if not args.confirm:
                _require_human_review("mass")
            print(json.dumps(mass_send(args.media_id, tag_id=args.tag_id), ensure_ascii=False, indent=2))
    except RuntimeError as e:
        sys.stderr.write(f"错误: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
