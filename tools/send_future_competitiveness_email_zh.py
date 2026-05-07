#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文版（简体）:Send the future-competitiveness curriculum comparison.

Pattern matches send_future_competitiveness_email.py — same SMTP plumbing,
Mandarin body. Professional terms that are awkward to translate (curriculum
names, exam codes, school abbreviations) stay in English with a Chinese
gloss on first use only.

Usage:
    python3 tools/send_future_competitiveness_email_zh.py
    DRY_RUN=1 python3 tools/send_future_competitiveness_email_zh.py
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

SUBJECT = f"香港选校 — 课程未来竞争力对比（{TODAY}）"

C_BG = "#f8fafc"
C_CARD = "#ffffff"
C_TEXT = "#0f172a"
C_MUTED = "#475569"
C_PRIMARY = "#1e3a8a"
C_ACCENT = "#0369a1"
C_GOOD = "#15803d"
C_BAD = "#b91c1c"
C_BORDER = "#e2e8f0"
C_HEAD = "#1e293b"

WRAP = (
    f'font-family:-apple-system,"PingFang SC","Microsoft YaHei",'
    f'"Hiragino Sans GB",Segoe UI,Roboto,Helvetica,Arial,sans-serif;'
    f"color:{C_TEXT};line-height:1.65;font-size:15px;"
)


def card(inner, title=None):
    head = (
        f'<div style="font-weight:600;font-size:17px;color:{C_PRIMARY};margin:0 0 10px 0;">{title}</div>'
        if title
        else ""
    )
    return (
        f'<div style="background:{C_CARD};border:1px solid {C_BORDER};border-radius:10px;'
        f'padding:18px 20px;margin:12px 0;">{head}{inner}</div>'
    )


def table(headers, rows):
    th = "".join(
        f'<th style="text-align:left;padding:8px 10px;background:{C_HEAD};color:#fff;'
        f'font-weight:600;font-size:13px;border-bottom:1px solid {C_BORDER};">{h}</th>'
        for h in headers
    )
    body = []
    for i, row in enumerate(rows):
        bg = "#f8fafc" if i % 2 else "#ffffff"
        tds = "".join(
            f'<td style="padding:8px 10px;border-bottom:1px solid {C_BORDER};vertical-align:top;font-size:13px;line-height:1.55;">{c}</td>'
            for c in row
        )
        body.append(f'<tr style="background:{bg};">{tds}</tr>')
    return (
        f'<table style="border-collapse:collapse;width:100%;border:1px solid {C_BORDER};border-radius:8px;overflow:hidden;">'
        f"<thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table>"
    )


def ul(items, color=C_TEXT):
    lis = "".join(
        f'<li style="margin:5px 0;color:{color};font-size:14px;line-height:1.65;">{x}</li>' for x in items
    )
    return f'<ul style="padding-left:20px;margin:6px 0;">{lis}</ul>'


# ---------- 内容 ----------

HEADER = (
    f'<div style="background:{C_PRIMARY};color:#fff;padding:22px 24px;border-radius:10px 10px 0 0;">'
    f'<div style="font-size:22px;font-weight:700;">课程未来竞争力对比</div>'
    f'<div style="font-size:14px;opacity:0.9;margin-top:4px;">'
    f"IB（国际文凭）vs A-Level（英国高考）vs AP（美国大学先修课程）vs DSE（香港中学文凭）"
    f"——以 2040–2050 年的就业市场为锚点"
    f"</div>"
    f'<div style="font-size:12px;opacity:0.75;margin-top:8px;">更新日期 {TODAY} · school-picker · 01-curricula/future-competitiveness-comparison.md</div>'
    f"</div>"
)

# 注脚:专业术语保留英文,首次出现给中文释义
GLOSSARY = card(
    "<p style=\"margin:0 0 8px;font-weight:600;\">术语对照(首次出现保留英文,后文沿用英文以保持精确度):</p>"
    + ul(
        [
            "<b>IB DP</b> — International Baccalaureate Diploma Programme,国际文凭大学预科项目",
            "<b>A-Level</b> — General Certificate of Education Advanced Level,英国普通教育高级证书(英式高考)",
            "<b>AP</b> — Advanced Placement,美国大学先修课程",
            "<b>HKDSE / DSE</b> — Hong Kong Diploma of Secondary Education,香港中学文凭考试",
            "<b>EE</b> — Extended Essay,IB 的 4,000 字独立研究论文",
            "<b>IA</b> — Internal Assessment,IB 各学科的校内评估",
            "<b>TOK</b> — Theory of Knowledge,IB 的「知识论」必修课",
            "<b>CAS</b> — Creativity, Activity, Service,IB 的创新、行动与服务项目",
            "<b>EPQ</b> — Extended Project Qualification,A-Level 的扩展项目资格(可选,5,000 字独立研究)",
            "<b>AP Capstone</b> — AP 的两年研究序列(AP Seminar + AP Research),含 4,000–5,000 字独立研究 + 答辩",
            "<b>IES</b> — Independent Enquiry Study,DSE 通识科的独立专题研究",
            "<b>Math AA HL / Math AI HL</b> — IB 数学的两条赛道:Analysis & Approaches(分析与方法,偏理论,适合 STEM)vs Applications & Interpretation(应用与解释,偏数据建模)",
            "<b>Calc BC / Physics C</b> — AP 的微积分 BC(单变量)与物理 C(基于微积分的力学 + 电磁学)",
            "<b>Further Maths</b> — A-Level 进阶数学,西方主流课程中预科级数学最深的科目",
            "<b>HKIS / AIS</b> — Hong Kong International School(浅水湾)vs American International School(九龙塘),两所香港主要 AP 学校",
            "<b>JAS</b> — 港澳台联招制度下的「内地高校招收香港学生计划」,2026/27 学年共 165 所内地高校接受 DSE 成绩",
            "<b>STEM</b> — Science, Technology, Engineering, Mathematics,理工科",
        ]
    ),
    "术语说明",
)

TLDR = card(
    f'<div style="font-size:15px;">'
    f"<b>对本家庭教育理念的排序:</b> "
    f"<span style=\"font-weight:600;color:{C_ACCENT};\">"
    f"IB &gt; A-Level &gt; AP(HKIS 体系)&gt; AP(AIS 体系)&gt; DSE</span>。"
    f"</div>"
    f'<div style="margin-top:8px;color:{C_MUTED};font-size:14px;">'
    f"课程设定的是<b>能力上限</b>,而学校的<b>探究文化</b>决定能否触及这个上限。"
    f"<b>一所平庸的 IB 学校,不如一所优秀的 A-Level 学校。</b>"
    f"</div>",
    "核心结论",
)

EIGHT_AXES = card(
    table(
        ["未来核心能力", "IB DP", "A-Level", "AP @ HKIS", "AP @ AIS", "HKDSE"],
        [
            [
                "数学深度",
                "Math AA HL 扎实;Further Math 罕见",
                f'<b style="color:{C_GOOD};">最强 — Further Maths</b>',
                "Calc BC + 后置(post-AP)Multivariable / Linear Algebra / DiffEq",
                f'<span style="color:{C_BAD};">Calc BC 封顶 — 未确认有 post-AP</span>',
                "M2 模块历史上严谨;高度依赖学校",
            ],
            [
                "物理深度",
                "Physics HL(代数为主)",
                "基于微积分,推导严谨",
                f'<b style="color:{C_GOOD};">Physics C:Mechanics + E&M</b>',
                f'<span style="color:{C_BAD};">仅 Physics 1/2(代数)— 比 HKIS 低一档</span>',
                "纯代数;覆盖面窄",
            ],
            [
                "原创研究训练",
                f'<b style="color:{C_GOOD};">EE 4,000 字 + 6 篇 IA(强制)</b>',
                "EPQ 可选;各校差异极大",
                "提供 AP Capstone",
                "提供 AP Capstone 完整文凭",
                "IES 流于形式 / 走过场",
            ],
            [
                "写作与论证",
                "TOK + EE 强制结构化论证",
                "EPQ + 人文学科重论文",
                "因校而异",
                "因校而异",
                "弱;考试格式主导",
            ],
            [
                "跨学科广度",
                f'<b style="color:{C_GOOD};">强制(6 学科组 + TOK + CAS)</b>',
                "刻意收窄(仅 3–4 科)",
                "灵活 — 学生自选",
                "灵活 — 学生自选",
                "窄 + 备考导向",
            ],
            [
                "自主性与主动性",
                "EE 选题 + CAS + IA 设计",
                "若认真做 EPQ 则强",
                "AP Research 是 AP 体系最佳载体",
                "同上 — 但被 post-AP 天花板拉低",
                "服从型文化;低",
            ],
            [
                "AI 时代评估对齐度",
                f'<b style="color:{C_GOOD};">EE 已为 2027 年 5 月首次评估更新(强制声明 AI 使用)</b>',
                "落后",
                "落后",
                "落后",
                "落后",
            ],
            [
                "审美 / 艺术",
                "Group 6 强制",
                "艺术 / 音乐 A-Level 可选",
                "AP Studio Art / Music Theory",
                "AP Studio Art / Music Theory",
                "弱;非升学优势科目",
            ],
        ],
    ),
    "八项关键能力对比(详见 future-skills-analysis.md)",
)

AIS_VS_HKIS = card(
    f"<p>为何 AP 拆成两栏:据本仓 <code>02-schools/american-international-school.md</code> 已核实,"
    f"香港两所主要 AP 学校在课程供给上存在<b>整整一档的差距</b>。</p>"
    + table(
        ["", "HKIS(浅水湾)", "AIS(九龙塘)"],
        [
            ["AP 微积分", "AB, BC", "AB, BC"],
            [
                "post-AP 数学",
                f'<b style="color:{C_GOOD};">公开开设 Multivariable + Linear Algebra + DiffEq</b>',
                f'<span style="color:{C_BAD};">公开材料未确认提供</span>',
            ],
            [
                "AP 物理",
                f'<b style="color:{C_GOOD};">Physics C:Mechanics + E&M(基于微积分)</b>',
                f'<span style="color:{C_BAD};">仅 Physics 1, Physics 2(代数)</span>',
            ],
            ["AP Capstone", "提供", "提供完整文凭(约 16 门 AP 学科)"],
            ["双语", "DLI 双语沉浸项目", "Mandarin 作为外语科目"],
        ],
    )
    + f'<p style="margin-top:10px;color:{C_MUTED};font-size:13px;">'
    f"<b>对志在 MIT / CMU / Stanford 级别 STEM 申请者的解读:</b>"
    f"AIS 公开的数理上限<b>整整比 HKIS 低一档</b>。"
    f"两校都提供 Capstone — 这是 AP 体系唯一具备的真实研究脚手架。"
    f"若学校<b>既无 Capstone、又缺乏原创性工作的文化</b>,纯 AP 路径的「广而浅」会成为 AI 时代能力栈中<b>最不利</b>的选择,"
    f"哪怕考试分数依然漂亮。"
    f"</p>",
    "AP @ AIS ≠ AP @ HKIS",
)

WHY_IB = card(
    "<p>2040–2050 年的经济结构,正好奖励 IB 在结构上<b>强制要求</b>的东西:</p>"
    + ul(
        [
            "<b>4,000 字独立研究项目</b>(EE)— 中学阶段最接近大学毕业论文的训练",
            "<b>显式的「思考如何思考」</b>(TOK)— 把认识论作为成绩科目",
            "<b>六篇 IA</b>跨学科,等同于多份小型论文",
            "<b>强制的广度</b>防止过早窄化 — TOK + Group 6 + CAS",
        ]
    )
    + f'<p style="color:{C_MUTED};font-size:13px;">'
    f"IB 的 <b>EE 2027 年 5 月评估改革</b>(含强制声明 AI 使用、显式强调原创分析),"
    f"是目前唯一在<b>评估端对齐 AI 时代</b>的主流课程。"
    f"<b>局限:</b>数理深度仅算「优良」,并非「顶尖」 — 对志在 MIT 级 STEM 的孩子,"
    f"IB 需要校外补充(数学奥赛、MIT OCW 公开课、暑期项目)。"
    f"</p>",
    "为何 IB 在这个视角下胜出",
)

WHY_ALEVEL = card(
    "<p>对一个理工偏好、且抗拒填鸭式的孩子,"
    "<b>A-Level Further Maths + Physics + Chemistry(+ EPQ)</b>"
    "是西方主流课程中<b>预科级数学最深的组合</b>:</p>"
    + ul(
        [
            "<b>Further Maths</b>:复数、矩阵、归纳法证明、极坐标曲线、ODE、群论基础 — 最接近大学一年级数学",
            "<b>A-Level Physics</b>:基于微积分、推导严谨,单科深度超过 IB Physics HL",
            "<b>EPQ</b>:5,000 字独立研究项目;<i>若学校认真对待</i>,深度可与 IB EE 媲美",
        ]
    )
    + f'<p style="color:{C_MUTED};font-size:13px;">'
    f"<b>关键陷阱:</b>没有 EPQ + 研究文化的 A-Level,会沦为机械刷历年真题。"
    f"<b>EPQ 的开设率与认真度,是判断学校真实定位的最佳信号</b> — "
    f"不推 EPQ 的学校,本质上就是「应试加工厂」。"
    f"</p>",
    "为何 A-Level 是稳健的第二选择",
)

WHY_DSE_LAST = card(
    f'<p>DSE 的 M2 模块本身并不弱(纯数学深度甚至历史上超过 IB Math AA HL)。'
    f"问题在于<b>课程与文化的错配</b>:</p>"
    + ul(
        [
            "DSE 的<i>校园文化</i>在香港即等同于「做题、填鸭式」,正是本家庭明确反对的",
            "IES 流于程式化 — 不是真正的研究",
            "要在 DSE 体系中保持竞争力,事实上必须依赖补习社 — 这本身就说明学校教学不到位",
            "整个备考机制,优化的恰恰是 AI 正在快速取代的能力",
        ]
    )
    + f'<p style="color:{C_MUTED};font-size:13px;">'
    f"<b>选 DSE 只有在以下两个条件同时成立时才合理:</b>"
    f"(1)<b>内地顶尖大学路径</b>(清北复交,通过港澳台联招 / JAS)是<i>主要</i>目标 — "
    f"这是 DSE 唯一且不可替代的优势,2026/27 学年共有 165 所内地高校接受 DSE 成绩;"
    f"(2)学校是少数真正培养探究精神而非刷题的 DSS 学校(DBS、SPCC、La Salle、DGS 等)。"
    f"<b>不读 DSE 就永久失去 JAS 通道 — 这是本分析中唯一的一道单向门。</b>"
    f"</p>",
    "为何 DSE 在「本家庭情境」下排在最后",
)

VERDICT = card(
    f'<div style="font-weight:600;color:{C_GOOD};margin-bottom:6px;">第一档 — 最佳契合</div>'
    + ul(
        [
            "<b>IB DP</b>,在优质 IB 学校(CIS、GSIS、ESF Island School、Renaissance College 等),"
            "搭配 <b>Math AA HL + Physics HL + 理工方向 EE</b>。校外补 Olympiad / MIT OCW 提升数理深度。",
            "<b>A-Level(Math + Further Maths + Physics + 1 门人文)+ EPQ</b>,"
            "在 Harrow、Malvern、Kellett Sixth Form、GSIS British Stream 等。"
            "<b>报名前务必核实 EPQ 的实际开设率与质量。</b>",
            "<b>HKIS 的 AP Capstone</b>,搭配 Calc BC + Physics C(Mech + E&M)+ post-AP 数学。"
            "锁定美国本科申请方向。",
        ]
    )
    + f'<div style="font-weight:600;color:{C_ACCENT};margin:14px 0 6px;">第二档 — 可行,但有保留</div>'
    + ul(
        [
            "<b>AIS 的 AP Capstone</b> — 研究脚手架强(完整 Capstone 文凭),"
            "但 STEM 上限比 HKIS 低一档。若孩子的目标不是 MIT 级理工,可接受。",
            "<b>DSE(在 DSS 学校)+ 自学 AP(Calc BC、Physics C)+ 校外研究项目</b> — "
            "保留 JAS 内地通道,同时弥补 DSE 在数理深度与研究训练上的缺口。"
            "工作量较大,且能做到这一组合的学校不多。",
        ]
    )
    + f'<div style="font-weight:600;color:{C_BAD};margin:14px 0 6px;">第三档 — 一般应回避</div>'
    + ul(
        [
            "<b>纯 AP(无 Capstone)</b> — 缺乏结构性研究训练,完全依赖学生个人主动性。",
            "<b>非 DSS 学校的纯 DSE</b> — 备考文化风险过高,与本家庭理念结构性不符。",
        ]
    ),
    "排序结论",
)

RED_FLAGS = card(
    f'<p style="color:{C_BAD};font-weight:600;margin:0 0 6px;">不分课程的「劝退信号」 — 看到这些就该转身</p>'
    + ul(
        [
            "<b>每日/每周排名公开张贴</b> — 预示焦虑文化与同质化,而非自信与主动",
            "<b>「考试成绩」是学校的主要营销卖点</b> — 暴露了学校真正在优化的是什么",
            "<b>全程教师主导的时间表</b> — 几乎没有自主项目 / 午休弹性",
            "<b>校园里看不到学生作品</b>,只有营销公关包装过的展示",
            "课程让<b>理工孩子被分到 Math AI 而非 Math AA</b>,或 DSE 不带 M1/M2 模块",
            "<b>必须靠补习社才能跟上</b> — 学校实际上不是在教学,而是在筛选「家里能请得起补习」的孩子",
            "高年级 STEM 老师整体仅有教育学本科学位,缺乏学科深度",
            "高层管理谈「纪律」「严格」(应试意义上的)远多于「思考」「原创」",
            "AI 政策要么<b>「全面禁用 AI」</b>(天真,违背 OECD/EC AILit 框架),要么<b>「全员用 AI」却没有任何披露机制</b> — 两种都是红旗",
            "EE / Capstone 选题来自学校预先批准的模板列表 — 说明学生根本没在自主选择",
            "<b>AP 学校:</b>不开设 AP Capstone,或大部分学生选择跳过",
            "<b>A-Level 学校:</b>不开设 EPQ,或选课率低于 30%",
            "<b>IB 学校:</b>Math AI 是默认数学课",
            "<b>DSE 学校:</b>校园里能看到补习社赞助标志(横幅、合作课程、品牌化的「应试策略讲座」)",
        ],
        color=C_TEXT,
    ),
    "红旗",
)

GREEN_FLAGS = card(
    f'<p style="color:{C_GOOD};font-weight:600;margin:0 0 6px;">值得追的强信号 — 与本视角对齐的学校</p>'
    + ul(
        [
            "学生能<b>有信念地讲清楚</b>自己的 EE / IA / EPQ / Capstone / 个人项目",
            "近年校友<b>在做有意思的事情</b>(创业、发表论文、走非典型路径)— 而不只是「藤校录取人数」",
            "数学 / 物理老师<b>主动兴奋地</b>带你看奥赛队学生的成果",
            "学校文化是「<b>我们做出来了什么</b>」 — 学生项目、出版物、有真实利害的学生组织活动",
            "<b>学术内容本身使用双语教学</b>,而不仅仅是语言课",
            "在校嵌入式导师 — 真在做研究的科学家、艺术家、创业者(不是营销开放日的客串嘉宾)",
            "<b>显式整合 AI</b>:教学生使用、审查、披露 AI;最终作品明显超出 AI 单独所能产出的水平",
            "<b>AP 学校:</b>提供 Capstone 完整文凭 + post-AP 数学 + Physics C",
            "<b>A-Level 学校:</b>EPQ 选课率 &gt;70% + Further Maths 常规开设 + 可见的奥赛文化",
            "<b>IB 学校:</b>STEM 学生默认 Math AA HL;EE 选题像「真问题」;TOK 由资深教师上",
            "<b>同时开设 DSE + IB 的 DSS 学校</b>:学生在 Y9 末根据兴趣 / 能力<b>自主</b>选择路径,而非学校强制分流",
        ],
        color=C_TEXT,
    ),
    "绿旗",
)

META = card(
    "<p>三条推论:</p>"
    + ul(
        [
            "<b>学校比课程更重要。</b>"
            "DSE 学校里的好老师,胜过 IB 学校里的平庸老师。",
            "<b>「同一课程内的具体科目选择」比「课程标签本身」更重要。</b>"
            "Math AA HL ≫ Math AI HL;A-Level + Further Maths ≫ 单 A-Level Maths;"
            "Calc BC ≫ AB;Physics C ≫ Physics 1/2;DSE M2 ≫ DSE 不带扩展模块。",
            "<b>研究训练可以校外补</b> — 数学奥赛、物理奥赛、MIT OCW、暑期科研项目"
            "(RSI、丘成桐数学营、BWSI 等)。可能是任何课程之上<b>单笔回报最高的投资</b>。",
        ]
    )
    + f'<p style="color:{C_MUTED};font-size:13px;margin-top:10px;">'
    f"完整文档:<code>01-curricula/future-competitiveness-comparison.md</code> · "
    f"八项能力的论证依据:<code>future-skills-analysis.md</code> · "
    f"通用课程对比:<code>comparison-matrix.md</code>"
    f"</p>",
    "总结性观察",
)

BODY = (
    f'<div style="background:{C_BG};padding:24px;">'
    f'<div style="max-width:760px;margin:0 auto;">'
    f"{HEADER}"
    f'<div style="background:{C_BG};padding:0 4px;">'
    f"{TLDR}{GLOSSARY}{EIGHT_AXES}{AIS_VS_HKIS}{WHY_IB}{WHY_ALEVEL}{WHY_DSE_LAST}{VERDICT}{RED_FLAGS}{GREEN_FLAGS}{META}"
    f"</div>"
    f"</div></div>"
)

HTML = f'<html><body style="{WRAP}margin:0;padding:0;background:{C_BG};">{BODY}</body></html>'


def send():
    if os.environ.get("DRY_RUN"):
        out = "/tmp/future_competitiveness_email_zh.html"
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
