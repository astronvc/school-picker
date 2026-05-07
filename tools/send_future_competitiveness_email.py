#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send the future-competitiveness curriculum comparison as a single HTML email.

Reads credentials the same way as send_summary_email.py:
  ~/.config/send_email.yml with GMAIL_APP_PASSWORD / GMAIL_SENDER / GMAIL_TO.

Usage:
    python3 tools/send_future_competitiveness_email.py
    DRY_RUN=1 python3 tools/send_future_competitiveness_email.py
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

SUBJECT = f"HK School Picker — Curriculum future-competitiveness ({TODAY})"

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
    f"font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;"
    f"color:{C_TEXT};line-height:1.55;font-size:15px;"
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


def table(headers, rows, col_widths=None):
    th = "".join(
        f'<th style="text-align:left;padding:8px 10px;background:{C_HEAD};color:#fff;'
        f'font-weight:600;font-size:13px;border-bottom:1px solid {C_BORDER};">{h}</th>'
        for h in headers
    )
    body = []
    for i, row in enumerate(rows):
        bg = "#f8fafc" if i % 2 else "#ffffff"
        tds = "".join(
            f'<td style="padding:8px 10px;border-bottom:1px solid {C_BORDER};vertical-align:top;font-size:13px;">{c}</td>'
            for c in row
        )
        body.append(f'<tr style="background:{bg};">{tds}</tr>')
    return (
        f'<table style="border-collapse:collapse;width:100%;border:1px solid {C_BORDER};border-radius:8px;overflow:hidden;">'
        f"<thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table>"
    )


def ul(items, color=C_TEXT):
    lis = "".join(
        f'<li style="margin:4px 0;color:{color};font-size:14px;">{x}</li>' for x in items
    )
    return f'<ul style="padding-left:20px;margin:6px 0;">{lis}</ul>'


# ---------- content ----------

HEADER = (
    f'<div style="background:{C_PRIMARY};color:#fff;padding:22px 24px;border-radius:10px 10px 0 0;">'
    f'<div style="font-size:22px;font-weight:700;">Curriculum future-competitiveness</div>'
    f'<div style="font-size:14px;opacity:0.9;margin-top:4px;">'
    f"IB vs A-Level vs AP (HKIS / AIS) vs DSE — for the 2040–2050 economy"
    f"</div>"
    f'<div style="font-size:12px;opacity:0.75;margin-top:8px;">Updated {TODAY} · school-picker · 01-curricula/future-competitiveness-comparison.md</div>'
    f"</div>"
)

TLDR = card(
    f'<div style="font-size:15px;">'
    f"<b>Ranking for this family's stated philosophy:</b> "
    f"<span style=\"font-weight:600;color:{C_ACCENT};\">"
    f"IB &gt; A-Level &gt; AP (HKIS-tier) &gt; AP (AIS-tier) &gt; DSE</span>."
    f"</div>"
    f'<div style="margin-top:8px;color:{C_MUTED};font-size:14px;">'
    f"Curriculum sets a ceiling. School culture of inquiry determines whether that ceiling is reached. "
    f"<b>A weak IB school is worse than a strong A-Level school.</b>"
    f"</div>",
    "TL;DR",
)

EIGHT_AXES = card(
    table(
        ["Skill", "IB DP", "A-Level", "AP @ HKIS", "AP @ AIS", "HKDSE"],
        [
            [
                "Math depth",
                "Math AA HL solid; Further Math rare",
                f'<b style="color:{C_GOOD};">Best — Further Maths</b>',
                "Calc BC + post-AP Multivar / LinAlg / DiffEq",
                f'<span style="color:{C_BAD};">Calc BC ceiling — no post-AP</span>',
                "M2 historically rigorous; school-dependent",
            ],
            [
                "Physics depth",
                "Physics HL (algebra-based)",
                "Calculus-based, rigorous",
                f'<b style="color:{C_GOOD};">Physics C: Mech + E&M</b>',
                f'<span style="color:{C_BAD};">Physics 1/2 algebra — one tier below</span>',
                "Algebra-only; narrow",
            ],
            [
                "Original research",
                f'<b style="color:{C_GOOD};">EE 4,000w + 6 IAs (mandatory)</b>',
                "EPQ optional; varies by school",
                "AP Capstone offered",
                "AP Capstone full diploma offered",
                "IES procedural / checkbox",
            ],
            [
                "Writing & argument",
                "TOK + EE force structure",
                "EPQ + essay-heavy humanities",
                "Variable; school-dependent",
                "Variable; school-dependent",
                "Weak; exam-format dominates",
            ],
            [
                "Cross-domain breadth",
                f'<b style="color:{C_GOOD};">Forced (6 groups + TOK + CAS)</b>',
                "Narrow by design (3–4 subjects)",
                "Flexible — student-chosen",
                "Flexible — student-chosen",
                "Narrow + test-prep tilt",
            ],
            [
                "Agency / self-direction",
                "EE topic + CAS + IA design",
                "EPQ if seriously taken",
                "AP Research is best AP vector",
                "Same — capped by post-AP ceiling",
                "Compliance culture; low",
            ],
            [
                "AI-literacy fit",
                f'<b style="color:{C_GOOD};">EE updated for May 2027 (AI disclosure)</b>',
                "Lagging",
                "Lagging",
                "Lagging",
                "Lagging",
            ],
            [
                "Taste / arts",
                "Group 6 mandatory",
                "Art / Music optional",
                "AP Studio Art / Music Theory",
                "AP Studio Art / Music Theory",
                "Weak; not exam-prestigious",
            ],
        ],
    ),
    "The eight skills that matter (per future-skills-analysis.md)",
)

AIS_VS_HKIS = card(
    f"<p>Why AP splits into two columns: per <code>02-schools/american-international-school.md</code>, "
    f"there is a verified one-tier gap in offerings between HK's two main AP schools.</p>"
    + table(
        ["", "HKIS (Repulse Bay)", "AIS (Kowloon Tong)"],
        [
            ["AP Calculus", "AB, BC", "AB, BC"],
            [
                "Post-AP math",
                f'<b style="color:{C_GOOD};">Multivariable + Linear Algebra + DiffEq published</b>',
                f'<span style="color:{C_BAD};">Not confirmed in public materials</span>',
            ],
            [
                "AP Physics",
                f'<b style="color:{C_GOOD};">Physics C: Mech + E&M (calc-based)</b>',
                f'<span style="color:{C_BAD};">Physics 1, Physics 2 only (algebra-based)</span>',
            ],
            ["AP Capstone", "Yes", "Yes (full diploma; ~16 AP subjects)"],
            ["Dual-language", "DLI program", "Mandarin as world language"],
        ],
    )
    + f'<p style="margin-top:10px;color:{C_MUTED};font-size:13px;">'
    f"<b>Translation for an MIT/CMU/Stanford-class STEM applicant:</b> AIS's published math/physics ceiling is "
    f"<b>one full course-tier below HKIS</b>. Both offer Capstone, AP's only real research scaffolding. "
    f"Without Capstone <i>and</i> a school culture of original work, AP is coverage-style and shallow — "
    f"the worst fit for the AI-era skill stack despite producing fine test scores."
    f"</p>",
    "AP at AIS ≠ AP at HKIS",
)

WHY_IB = card(
    "<p>The 2040–2050 economy rewards what IB structurally <b>forces</b>:</p>"
    + ul(
        [
            "<b>4,000-word independent research project</b> (EE) — closest secondary analogue to a university dissertation",
            "<b>Explicit thinking-about-thinking</b> (TOK) — epistemology as a graded subject",
            "<b>Six Internal Assessments</b> approximating small dissertations across domains",
            "<b>Breadth that prevents premature narrowing</b> — TOK + Group 6 + CAS",
        ]
    )
    + f'<p style="color:{C_MUTED};font-size:13px;">'
    f"IB's <b>May 2027 EE update</b> with mandatory AI-use disclosure is the only curriculum currently aligning its assessment with the AI era. "
    f"<b>Limitation:</b> math/physics depth is good but not exceptional — for an MIT-class STEM kid, IB needs supplementation (Olympiads, MIT OCW, summer programmes)."
    f"</p>",
    "Why IB wins on this lens",
)

WHY_ALEVEL = card(
    "<p>For a STEM-deep kid against rote learning, "
    "<b>A-Level Further Maths + Physics + Chem (+ EPQ)</b> is the deepest pre-university quantitative track in any mainstream Western curriculum:</p>"
    + ul(
        [
            "<b>Further Maths</b>: complex numbers, matrices, induction proofs, ODEs, group theory — closest to first-year university math",
            "<b>A-Level Physics</b>: calculus-based, rigorous derivations, deeper per topic than IB Physics HL",
            "<b>EPQ</b>: 5,000-word independent research project; can match IB EE depth <i>if school takes it seriously</i>",
        ]
    )
    + f'<p style="color:{C_MUTED};font-size:13px;">'
    f"<b>The catch:</b> A-Level becomes past-paper drilling without EPQ + research culture. "
    f"<b>EPQ uptake is the diagnostic</b> — schools that don't push EPQ are signalling exam-shop."
    f"</p>",
    "Why A-Level is the strong second",
)

WHY_DSE_LAST = card(
    f'<p>DSE M2 isn\'t weak (historically deeper than IB Math AA HL on pure math). The issue is <b>curriculum-culture mismatch</b>:</p>'
    + ul(
        [
            "DSE <i>culture</i> in HK is the 做题 / 填鸭式 engine the family explicitly rejects",
            "IES is procedural — not real investigation",
            "Cram-tutoring is structurally required to be competitive",
            "The treadmill optimizes for skills being commoditized by AI",
        ]
    )
    + f'<p style="color:{C_MUTED};font-size:13px;">'
    f"<b>DSE makes sense only if both</b>: (1) Mainland top-university route (Tsinghua/Peking via Joint Programme) is the <i>primary</i> goal — its one irreversible advantage, with 165 mainland universities accepting DSE in 2026/27; "
    f"(2) the school is a rare DSS (DBS, SPCC, La Salle, DGS) that culturally cultivates inquiry rather than drilling. "
    f"<b>The mainland JAS option is irreversibly lost without DSE — the only one-way door in this analysis.</b>"
    f"</p>",
    "Why DSE ranks last for this family specifically",
)

VERDICT = card(
    f'<div style="font-weight:600;color:{C_GOOD};margin-bottom:6px;">Tier 1 — best fit</div>'
    + ul(
        [
            "<b>IB DP</b> at strong IB school (CIS, GSIS, ESF Island, Renaissance) with <b>Math AA HL + Physics HL + STEM-focused EE</b>. Add Olympiads / MIT OCW for STEM depth.",
            "<b>A-Level (Math + Further Maths + Physics + 1 humanities) + EPQ</b> at Harrow / Malvern / Kellett Sixth Form / GSIS British. <b>Verify EPQ uptake before committing.</b>",
            "<b>AP Capstone at HKIS</b> with Calc BC + Physics C (Mech + E&M) + post-AP math. Locks in US-orientation.",
        ]
    )
    + f'<div style="font-weight:600;color:{C_ACCENT};margin:14px 0 6px;">Tier 2 — workable with caveats</div>'
    + ul(
        [
            "<b>AP Capstone at AIS</b> — strong on research scaffolding; STEM ceiling capped one tier below HKIS. Acceptable if destination isn't MIT-class STEM.",
            "<b>DSE at DSS school + supplementary APs (Calc BC, Physics C) + external research project</b> — preserves mainland JAS pathway while patching DSE's depth and research gaps.",
        ]
    )
    + f'<div style="font-weight:600;color:{C_BAD};margin:14px 0 6px;">Tier 3 — generally avoid</div>'
    + ul(
        [
            "<b>Pure AP without Capstone</b> — little structural inquiry; depends entirely on student initiative.",
            "<b>Pure DSE at non-DSS school</b> — exam culture risk too high; structurally misaligned with stated philosophy.",
        ]
    ),
    "Ranked verdict",
)

RED_FLAGS = card(
    f'<p style="color:{C_BAD};font-weight:600;margin:0 0 6px;">Curriculum-agnostic disqualifiers — what to walk away from</p>'
    + ul(
        [
            "<b>Daily/weekly ranking culture posted publicly</b> — predicts anxiety + conformity",
            "<b>'Test results' as dominant marketing message</b> — implies what they optimize for",
            "<b>All-teacher-directed schedule</b>; minimal independent / project / lunch flex",
            "<b>No visible student work</b> outside marketing-polished display pieces",
            "Curriculum requires <b>Math AI rather than Math AA</b>, or DSE Compulsory without M1/M2, for STEM kids",
            "<b>Tutors / juku culture <i>required</i> to keep up</b> — school isn't teaching, it's curating",
            "Teachers with little subject depth (BEd-only across STEM upper years)",
            "Senior leadership talks 'discipline' / 'rigour' (drill-sense) more than 'thinking' / 'originality'",
            "AI policy purely <b>'we ban AI'</b> (naive) <i>or</i> 'we use AI everywhere' with no disclosure framework",
            "EE / Capstone topics from a school-approved template list",
            "<b>AP school</b>: AP Capstone not offered, or most students skip it",
            "<b>A-Level school</b>: EPQ not offered, or &lt;30% uptake",
            "<b>IB school</b>: Math AI is the default math choice",
            "<b>DSE school</b>: cram-school sponsorship visible on premises",
        ],
        color=C_TEXT,
    ),
    "Red flags",
)

GREEN_FLAGS = card(
    f'<p style="color:{C_GOOD};font-weight:600;margin:0 0 6px;">Strong signals — schools that match the lens</p>'
    + ul(
        [
            "Students can <b>articulate</b> their EE / IA / EPQ / Capstone with conviction",
            "Recent alumni doing <b>interesting things</b> (start-ups, papers, unusual paths) — not just admit count",
            "Math/physics teachers excitedly point you to their <b>olympiad-team kids' work</b>",
            "Culture of <b>'we made this'</b> — student projects, publications, events with real stakes",
            "<b>Bilingual academic content</b> beyond language classes",
            "Embedded mentors: practicing scientists / artists / entrepreneurs",
            "<b>AI integrated explicitly</b>: teach use, audit, disclose; outputs clearly beyond what AI alone produces",
            "<b>AP school</b>: Capstone diploma + post-AP math + Physics C",
            "<b>A-Level school</b>: EPQ uptake &gt;70% + Further Maths regularly examined + visible Olympiad culture",
            "<b>IB school</b>: Math AA HL is the default; EE topics look like real questions; TOK by senior faculty",
            "<b>DSS school running both DSE + IB</b>: students freely choose end of Y9 by aptitude, not imposed tracking",
        ],
        color=C_TEXT,
    ),
    "Green flags",
)

META = card(
    "<p>Three corollaries:</p>"
    + ul(
        [
            "<b>The school matters more than the curriculum.</b> A great teacher in a DSE school can outperform a mediocre teacher in IB.",
            "<b>The math choice within each curriculum matters more than the curriculum label.</b> Math AA HL ≫ Math AI HL. A-Level + Further Maths ≫ A-Level Maths alone. Calc BC ≫ AB. Physics C ≫ Physics 1/2. DSE M2 ≫ DSE without extension.",
            "<b>Research practice can be added externally</b> — Olympiads, MIT OCW, summer programmes (RSI, Yau Math Camp, BWSI). Possibly the single most important investment alongside any curriculum.",
        ]
    )
    + f'<p style="color:{C_MUTED};font-size:13px;margin-top:10px;">'
    f"Full file: <code>01-curricula/future-competitiveness-comparison.md</code> · "
    f"reasoning behind the 8 skills: <code>future-skills-analysis.md</code> · "
    f"general curriculum comparison: <code>comparison-matrix.md</code>"
    f"</p>",
    "The meta-point",
)

BODY = (
    f'<div style="background:{C_BG};padding:24px;">'
    f'<div style="max-width:760px;margin:0 auto;">'
    f"{HEADER}"
    f'<div style="background:{C_BG};padding:0 4px;">'
    f"{TLDR}{EIGHT_AXES}{AIS_VS_HKIS}{WHY_IB}{WHY_ALEVEL}{WHY_DSE_LAST}{VERDICT}{RED_FLAGS}{GREEN_FLAGS}{META}"
    f"</div>"
    f"</div></div>"
)

HTML = f'<html><body style="{WRAP}margin:0;padding:0;background:{C_BG};">{BODY}</body></html>'


def send():
    if os.environ.get("DRY_RUN"):
        out = "/tmp/future_competitiveness_email.html"
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
