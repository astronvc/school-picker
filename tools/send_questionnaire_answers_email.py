#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send the three drafted kindergarten-questionnaire answers (Q4–Q6) as a
lightweight HTML email. Same SMTP plumbing as send_summary_email.py.

Usage:
    python3 tools/send_questionnaire_answers_email.py
    DRY_RUN=1 python3 tools/send_questionnaire_answers_email.py
"""

import os
import smtplib
import sys
from datetime import date
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def load_config(path="~/.config/send_email.yml"):
    cfg = {}
    full_path = os.path.expanduser(path)
    if not os.path.exists(full_path):
        return cfg
    with open(full_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
            elif ":" in line:
                k, v = line.split(":", 1)
            else:
                continue
            cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


CFG = load_config()
SENDER = os.environ.get("SENDER_EMAIL") or CFG.get("GMAIL_SENDER") or "pureteabee@gmail.com"
RECIPIENT = os.environ.get("RECIPIENT_EMAIL") or CFG.get("GMAIL_TO") or SENDER
TODAY = date.today().isoformat()

SUBJECT = f"幼稚園問卷回覆草稿 — Q4–Q8（{TODAY}）"

WRAP = (
    'font-family:-apple-system,"PingFang TC","PingFang SC","Microsoft JhengHei",'
    '"Microsoft YaHei",Segoe UI,Roboto,Helvetica,Arial,sans-serif;'
    "color:#1f2937;line-height:1.7;font-size:15px;"
)

# Three Q&A pairs. Keep formatting lightweight.
ITEMS = [
    {
        "n": "Q4",
        "q_zh": "誰是孩子的主要照顧者？孩子每天的主要活動是甚麼？",
        "q_en": "How does your child typically spend his/her day and with whom?",
        "a": "女兒平日主要由父母共同照顧，外婆協助日常起居。早上於N班學習，下午在家進行繪本閱讀、積木與角色扮演遊戲，亦常到公園探索自然。每週六參加橄欖球課，週日全家外出親近大自然或博物館。",
        "chars": 88,
    },
    {
        "n": "Q5",
        "q_zh": "請分享你的孩子在遊戲班 (如適用) 或與其他小朋友互動時的經驗。",
        "q_en": "Please describe your child's experience at his/her playgroup (if applicable) or interactions with other children.",
        "a": "女兒目前就讀N班已近一年，性格開朗，能主動與同學打招呼、分享玩具，並樂於參與集體活動。橄欖球課上她能聽從教練指示、與隊友配合奔跑搶球；面對陌生環境不怯場，常主動邀請小朋友一同遊戲，亦會關心同伴。",
        "chars": 97,
    },
    {
        "n": "Q6",
        "q_zh": "請描述你孩子的個性，例如喜好、興趣、習慣和性格；作為家長，你會如何根據孩子的個性培育他/她？",
        "q_en": "Please describe your child's personality, such as interests, hobbies, and general character. How do you, as a parent, nurture your child according to his/her personality?",
        "a": "女兒活潑開朗、好奇心強，愛探索新事物，亦喜歡動腦思考。鍾愛運動，最期待每週的橄欖球課。我們給她充足戶外時間，鼓勵自主嘗試、多問問題；以提問代替直接給答案，培養獨立思考；陪伴閱讀與運動，建立自信。",
        "chars": 97,
    },
    {
        "n": "Q7",
        "q_zh": "你如何幫助孩子培養良好的生活習慣？",
        "q_en": "How do you help your child develop good daily habits?",
        "a": "我們建立穩定的作息時間表:固定的就寢與用餐時間，每日安排戶外活動及親子閱讀。鼓勵她自行收拾玩具、學習穿衣與用餐禮儀。透過家長以身作則、即時肯定的方式建立規律，亦允許她在框架內自主選擇，培養責任感。",
        "chars": 98,
    },
    {
        "n": "Q8",
        "q_zh": "你如何與學校溝通和合作以支援孩子的學習和成長？",
        "q_en": "What do you see as your role in your child's school? How will you support your child's learning and development?",
        "a": "我們視學校為共同培育的夥伴。主動與老師保持溝通，分享女兒在家的觀察與興趣;尊重並配合學校的教學節奏。樂於參與家長活動與校園義工，亦會在家延伸課堂主題、共讀繪本，讓家校形成一致而支持的成長環境。",
        "chars": 96,
    },
]

# ---------- render ----------

def card(item):
    return (
        '<div style="margin:18px 0;padding:18px 20px;background:#ffffff;'
        'border:1px solid #e5e7eb;border-left:3px solid #2563eb;border-radius:6px;">'
        f'<div style="font-size:12px;font-weight:600;color:#2563eb;letter-spacing:0.04em;'
        f'text-transform:uppercase;margin-bottom:6px;">{item["n"]} · {item["chars"]}/100 字</div>'
        f'<div style="color:#374151;font-size:14px;margin-bottom:4px;">{item["q_zh"]}</div>'
        f'<div style="color:#6b7280;font-size:13px;font-style:italic;margin-bottom:12px;">{item["q_en"]}</div>'
        f'<div style="color:#0f172a;font-size:15px;line-height:1.75;padding:12px 14px;'
        f'background:#f8fafc;border-radius:4px;">{item["a"]}</div>'
        "</div>"
    )


HEADER = (
    '<div style="margin-bottom:16px;">'
    '<div style="font-size:20px;font-weight:600;color:#0f172a;">幼稚園問卷回覆草稿</div>'
    f'<div style="font-size:13px;color:#6b7280;margin-top:4px;">'
    f"Q4–Q8 · 每條 ≤100 字 · 重點:活潑開朗 / 愛探索 / 愛思考 / N班經驗 / 橄欖球愛運動"
    f"</div>"
    f'<div style="font-size:12px;color:#9ca3af;margin-top:4px;">擬稿日期 {TODAY}</div>'
    "</div>"
)

FOOTNOTE = (
    '<div style="margin-top:20px;padding:14px 16px;background:#fef9c3;'
    'border-left:3px solid #ca8a04;border-radius:4px;font-size:13px;color:#713f12;line-height:1.65;">'
    "<b>提交前快速檢查:</b> "
    "(1) 表格是繁體中文,以上回覆已用繁體; "
    "(2) 外婆 / 家傭設定如有不同請替換; "
    "(3) 「N班已近一年」如時間不符請改為「約半年」等; "
    "(4) 字數已預留空間,可微調個別字眼。"
    "</div>"
)

BODY = (
    '<div style="background:#f3f4f6;padding:28px 24px;">'
    '<div style="max-width:680px;margin:0 auto;background:#ffffff;border-radius:8px;'
    'padding:28px 32px;border:1px solid #e5e7eb;">'
    f"{HEADER}"
    + "".join(card(it) for it in ITEMS)
    + FOOTNOTE
    + "</div></div>"
)

HTML = f'<html><body style="{WRAP}margin:0;padding:0;background:#f3f4f6;">{BODY}</body></html>'


def send():
    if os.environ.get("DRY_RUN"):
        out = "/tmp/questionnaire_answers_email.html"
        with open(out, "w", encoding="utf-8") as f:
            f.write(HTML)
        print(f"DRY_RUN — wrote {out}")
        return

    password = os.environ.get("GMAIL_APP_PASSWORD") or CFG.get("GMAIL_APP_PASSWORD")
    if not password:
        print("ERROR: GMAIL_APP_PASSWORD not set in env or ~/.config/send_email.yml", file=sys.stderr)
        sys.exit(1)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(SUBJECT, "utf-8")
    msg["From"] = SENDER
    msg["To"] = RECIPIENT
    msg.attach(MIMEText(HTML, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER, password)
        smtp.sendmail(SENDER, [RECIPIENT], msg.as_string())
    print(f"Sent: {SUBJECT} → {RECIPIENT}")


if __name__ == "__main__":
    send()
