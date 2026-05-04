#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send the personalized HK school-picker summary as TWO rich HTML emails:
one in English, one in Mandarin (Simplified Chinese).

Credentials
-----------
By default reads from ~/.config/send_email.yml with this format
(both KEY=VALUE and KEY: VALUE lines work):

    GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
    GMAIL_SENDER=pureteabee@gmail.com
    GMAIL_TO=pureteabee@gmail.com

App password (16 chars) generated at:
    https://myaccount.google.com/apppasswords
(2-Step Verification must be enabled on the Google account first.)

Env vars override the config file:
    GMAIL_APP_PASSWORD, SENDER_EMAIL, RECIPIENT_EMAIL

Usage
-----
    python3 tools/send_summary_email.py
    DRY_RUN=1 python3 tools/send_summary_email.py    # render to dry_run_en/zh.html

Re-run safely. Idempotent: this just composes and sends.
"""

import os
import smtplib
import sys
from datetime import date
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def load_config(path="~/.config/send_email.yml"):
    """Load credentials from ~/.config/send_email.yml.

    Accepts both KEY=VALUE and KEY: VALUE line formats. Tolerates blanks,
    comments (#), and surrounding quotes on values.
    """
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

SUBJECT_EN = f"HK School Picker — Personalized Summary ({TODAY})"
SUBJECT_ZH = f"香港选校 — 个性化总结（{TODAY}）"

# ---------- design tokens (inline because email clients strip <style>) ----------

C_PRIMARY = "#1e3a8a"
C_ACCENT = "#0e7490"
C_BEST = "#15803d"
C_CAVEAT = "#b45309"
C_DANGER = "#b91c1c"
C_TEXT = "#111827"
C_MUTED = "#6b7280"
C_BORDER = "#e5e7eb"
C_BG = "#f9fafb"
C_CARD = "#ffffff"
C_TBL_HDR = "#f3f4f6"
C_TBL_ALT = "#fafafa"

FONT = ("font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, "
        "Arial, sans-serif;")

WRAP = (f"max-width:760px;margin:0 auto;padding:24px;background:{C_BG};"
        f"color:{C_TEXT};{FONT}line-height:1.55;font-size:14px;")

CARD = (f"background:{C_CARD};border:1px solid {C_BORDER};border-radius:8px;"
        "padding:18px 20px;margin:14px 0;")

URGENT_CARD = (f"background:#fef2f2;border:1px solid {C_DANGER};border-left:4px solid {C_DANGER};"
               "border-radius:8px;padding:18px 20px;margin:14px 0;")

H1 = (f"color:{C_PRIMARY};margin:0 0 6px 0;font-size:24px;font-weight:700;"
      f"letter-spacing:-0.01em;")

H2 = (f"color:{C_PRIMARY};margin:32px 0 12px 0;font-size:18px;font-weight:600;"
      f"border-bottom:2px solid {C_PRIMARY};padding-bottom:6px;")

H2_DANGER = (f"color:{C_DANGER};margin:32px 0 12px 0;font-size:18px;font-weight:700;"
             f"border-bottom:2px solid {C_DANGER};padding-bottom:6px;")

H3 = (f"color:{C_TEXT};margin:0 0 4px 0;font-size:16px;font-weight:600;")

MUTED = f"color:{C_MUTED};font-size:13px;"

PILL_BEST = (f"background:{C_BEST};color:#fff;border-radius:99px;"
             "padding:2px 10px;font-size:11px;font-weight:600;display:inline-block;")
PILL_CAVEAT = (f"background:{C_CAVEAT};color:#fff;border-radius:99px;"
               "padding:2px 10px;font-size:11px;font-weight:600;display:inline-block;")
PILL_INFO = (f"background:{C_PRIMARY};color:#fff;border-radius:99px;"
             "padding:2px 10px;font-size:11px;font-weight:600;display:inline-block;")
PILL_OUT = (f"background:{C_DANGER};color:#fff;border-radius:99px;"
            "padding:2px 10px;font-size:11px;font-weight:600;display:inline-block;")
PILL_URGENT = (f"background:{C_DANGER};color:#fff;border-radius:4px;"
               "padding:3px 10px;font-size:11px;font-weight:700;display:inline-block;"
               "letter-spacing:0.05em;")

TBL = (f"width:100%;border-collapse:collapse;margin:8px 0;font-size:13px;"
       f"border:1px solid {C_BORDER};border-radius:6px;overflow:hidden;")

TH = (f"background:{C_TBL_HDR};color:{C_TEXT};text-align:left;padding:8px 10px;"
      f"font-weight:600;border-bottom:1px solid {C_BORDER};")

TD = f"padding:8px 10px;border-bottom:1px solid {C_BORDER};vertical-align:top;"

LINK = f"color:{C_ACCENT};text-decoration:none;font-weight:500;"


# ---------- generic builders ----------

def school_card(label_pill, label_text, name, fields, why_label, why, caveat_label, caveats):
    """Render one school card. `fields` is a list of (label, value) string tuples."""
    rows = "\n".join(
        f'    <tr><td style="{TH};width:28%;">{lbl}</td><td style="{TD}">{val}</td></tr>'
        for lbl, val in fields
    )
    return f"""
<div style="{CARD}">
  <div style="display:block;margin-bottom:8px;">
    <span style="{label_pill}">{label_text}</span>
  </div>
  <h3 style="{H3}">{name}</h3>
  <table style="{TBL};margin-top:10px;">
{rows}
  </table>
  <p style="margin:10px 0 4px 0;"><b style="color:{C_BEST};">{why_label}:</b> {why}</p>
  <p style="margin:0;"><b style="color:{C_CAVEAT};">{caveat_label}:</b> {caveats}</p>
</div>
"""


# ---------- ENGLISH content ----------

def build_en_html():
    fld = {
        "curriculum": "Curriculum",
        "location": "Location",
        "fees": "Annual tuition (2025/26)",
        "capital": "Capital / debenture",
        "ib": "2025 IB outcome",
        "mandarin": "Mandarin",
        "app_window": "Application window",
        "apply": "Apply at",
    }
    why_lbl, caveat_lbl = "Why", "Caveats"

    isf = school_card(
        PILL_BEST, "TIER A — top fit",
        "The ISF Academy",
        [
            (fld["curriculum"], "IB MYP + DP; <b>70% Mandarin / 30% English</b> Foundation Year through G4"),
            (fld["location"], "Cyberport, Pokfulam (HK Island, west)"),
            (fld["fees"], "HK$152,880 (FY) → HK$241,110 (G11–12)"),
            (fld["capital"], "<b>Annual Capital Levy HK$40,000/yr</b> (within cap) · Capital Note option (one-time, larger)"),
            (fld["ib"], "Avg 38.6, 51% over 40, 1 perfect 45"),
            (fld["mandarin"], "<b>Deepest authentic Mandarin immersion in HK</b> — 70/30 ratio in junior years; perfect linguistic fit for a Mandarin-dominant child"),
            (fld["app_window"], "<b>FY entry (age 4)</b> — for her DOB (mid-Sep 2023, Aug 31 cutoff), target <b>AY2028/29 entry</b>. Applications open ~Sep 2027 (~16 months out). FY is ISF's main entry point for primary."),
            (fld["apply"], f'<a style="{LINK}" href="https://academy.isf.edu.hk/admissions/">academy.isf.edu.hk/admissions</a>'),
        ],
        why_lbl,
        "Single best-aligned school in HK for a Mandarin-dominant girl. Bilingual + IB + Chinese-virtues ethos + Cyberport facilities. Annual Capital Levy avoids the big-debenture trap entirely.",
        caveat_lbl,
        "Not the absolute top STEM (compensate via Olympiads / external math); Mandarin dilutes somewhat in upper years; Foundation Year intake is competitive.",
    )

    spcc = school_card(
        PILL_BEST, "TIER A — top fit",
        "St Paul's Co-educational College (SPCC)",
        [
            (fld["curriculum"], "DSE + IB DP <b>parallel</b> from S5 (dual-track DSS)"),
            (fld["location"], "MacDonnell Road, Mid-Levels (HK Island, central)"),
            (fld["fees"], "DSE ~HK$70K · IB local ~HK$160K · IB non-local ~HK$201K"),
            (fld["capital"], "<b>None</b> ✓ (primary capital fee/debenture not publicly published — verify on visit)"),
            (fld["ib"], "<b>Avg 42.1 — #1 in HK 2025</b>"),
            (fld["mandarin"], "English-medium with strong Putonghua-Chinese; substantial mainland-heritage cohort"),
            (fld["app_window"], "<b>P1 entry</b> — target Sep 2028 application for AY2029/30 (P1 in Sep 2029). Through-train from SPCC Primary feeder is the strategic entry."),
            (fld["apply"], f'<a style="{LINK}" href="https://www.spcc.edu.hk/admissions/">spcc.edu.hk/admissions</a>'),
        ],
        why_lbl,
        "Top academic ceiling in HK at fraction of international cost. No debenture, mainland-heritage friendly, central location. Co-ed, dual-track keeps DSE option open.",
        caveat_lbl,
        "S1 ratio ~20:1; SPCC Primary feeder is the strategic entry — P1 application is the key window 2028–29.",
    )

    vsa = school_card(
        PILL_INFO, "TIER A — strong",
        "Victoria Shanghai Academy (VSA)",
        [
            (fld["curriculum"], "IB Continuum (PYP, MYP, DP); bilingual English + Putonghua primary"),
            (fld["location"], "Aberdeen / Shum Wan (HK Island, south)"),
            (fld["fees"], "~HK$130K → HK$230K across grades"),
            (fld["capital"], "One-off capital, modest ✓ within cap (exact debenture not published — verify)"),
            (fld["ib"], "Avg 37.6 (5 perfect scorers in 2025)"),
            (fld["mandarin"], "Strong bilingual model — among the best for HK families wanting authentic Putonghua"),
            (fld["app_window"], "<b>Y1 entry</b> — AY2027/28 deadline already passed (2026-02-05). Apply ~Feb 2027 for AY2028/29 entry. Round 1+2 group interviews; no written assessment."),
            (fld["apply"], f'<a style="{LINK}" href="https://www.vsa.edu.hk/admissions/">vsa.edu.hk/admissions</a>'),
        ],
        why_lbl,
        "Bilingual IB Continuum at moderate cost; more accessible than ISF/CIS. Mainland-heritage friendly cohort.",
        caveat_lbl,
        "Aberdeen commute may not work from Quarry Bay (verify); less academic ceiling than SPCC.",
    )

    gtc = school_card(
        PILL_INFO, "TIER A — strong",
        "G.T. (Ellen Yeung) College",
        [
            (fld["curriculum"], "Local NSS (DSE) + IB DP from senior years"),
            (fld["location"], "Tiu Keng Leng, Tseung Kwan O"),
            (fld["fees"], "DSE ~HK$44K · <b>IBDP HK$88,550</b> (DSS bottom of range from HK$35,310)"),
            (fld["capital"], "<b>None</b> ✓"),
            (fld["ib"], "<b>Avg 40.04, 56% over 40</b> — exceptional outcome at this fee point"),
            (fld["mandarin"], "EMI with strong Chinese; mainland-heritage friendly"),
            (fld["app_window"], "<b>P1 entry</b> — target Sep 2028 application for AY2029/30 (P1 in Sep 2029). Interview format/notification not in public materials — confirm on visit."),
            (fld["apply"], f'<a style="{LINK}" href="https://www.gtcollege.edu.hk/admission">gtcollege.edu.hk/admission</a>'),
        ],
        why_lbl,
        "World-class IB outcomes at a fraction of international cost. Gifted-pedagogy approach maps cleanly to anti-rote, research-leaning preference.",
        caveat_lbl,
        "TKO location (long commute from HK Island Eastern); through-train means committing early.",
    )

    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>HK School Picker — Personalized Summary</title></head>
<body style="margin:0;padding:0;background:{C_BG};">
<div style="{WRAP}">

<div style="{CARD}">
  <h1 style="{H1}">HK School Picker — Personalized Summary</h1>
  <div style="{MUTED}">For: 2.5 yo girl · HK passport · mainland heritage · Mandarin-dominant
  · debenture cap HK$1M · mainland-uni optional</div>
  <div style="{MUTED};margin-top:6px;">
    Source repo:
    <a style="{LINK}" href="https://github.com/astronvc/school-picker">github.com/astronvc/school-picker</a>
    · Generated {TODAY}
  </div>
</div>

<h2 style="{H2_DANGER}"><span style="{PILL_URGENT}">URGENT</span> &nbsp; DOB-aware timeline</h2>
<div style="{URGENT_CARD}">
  <p style="margin:0 0 8px 0;">Child DOB confirmed: <b>mid-September 2023</b>. She's a "September baby" sitting right at most schools' age-cutoff cusp. <b>Implication: CDNIS Oct 2026 / SIS Sep 2026 deadlines for AY2027/28 entry DO NOT apply to her cohort</b> — those are for kids born Sep 2022 or earlier.</p>
  <table style="{TBL}">
    <tr>
      <th style="{TH};width:14%;">Cutoff</th>
      <th style="{TH};width:36%;">Schools</th>
      <th style="{TH};width:24%;">Her cohort</th>
      <th style="{TH}">Action window</th>
    </tr>
    <tr><td style="{TD}"><b>Aug 31</b></td><td style="{TD}">Most internationals (CDNIS, SIS, ISF, VSA, CIS, HKIS, HKA, Stamford, Carmel, Malvern, NAIS)</td><td style="{TD}">AY2028/29 K2/Reception/FY/EY1 entry (4 yrs 11 mo on Aug 31, 2028)</td><td style="{TD}">Apply <b>Sep–Oct 2027</b> (~16 months)</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>Dec 31</b></td><td style="{TD}">ESF kindergartens</td><td style="{TD}"><b>ESF K2 AY2027/28 entry</b> (4 yrs 3 mo on Dec 31, 2027)</td><td style="{TD}"><b style="color:{C_DANGER};">Apply Sep 2026</b> (~4 months)</td></tr>
    <tr><td style="{TD}"><b>Dec 31</b> (HK local)</td><td style="{TD}">DSS (SPCC, GTC, DGS)</td><td style="{TD}">AY2029/30 P1 entry</td><td style="{TD}">Apply Sep 2028 (~28 months)</td></tr>
  </table>
  <p style="margin:8px 0 0 0;"><b style="color:{C_DANGER};">Single actionable urgent date:</b> <b>Sep 2026 — ESF K2 applications open for AY2027/28 entry.</b> If any ESF school on list (RCHK, Discovery College, Hillside International Kindergarten, etc.), <b>buy ESF Individual Nomination Right HK$500K BEFORE applying</b> (must be in place at application time; cheapest priority lever in HK at HK$500K).</p>
</div>

<h2 style="{H2}">Family snapshot</h2>
<table style="{TBL}">
  <tr><td style="{TH}">Child</td><td style="{TD}">2.5 yo girl, currently at Tutor Time Dorset (Quarry Bay area, ~50/50 EN/CN at school)</td></tr>
  <tr><td style="{TH}">Language profile</td><td style="{TD}">~70% Mandarin / 30% English at home — Mandarin-dominant</td></tr>
  <tr><td style="{TH}">Citizenship</td><td style="{TD}">HK passport (child); parents from mainland China</td></tr>
  <tr><td style="{TH}">Philosophy</td><td style="{TD}">Strong academic + confidence + competitive — <b>against</b> 做题 / 考试 / 填鸭式; pro independent thinking + research approach + STEM depth</td></tr>
  <tr><td style="{TH}">Annual fee</td><td style="{TD}">Open</td></tr>
  <tr><td style="{TH}">Debenture cap</td><td style="{TD}"><b>HK$1,000,000</b></td></tr>
  <tr><td style="{TH}">Mainland uni</td><td style="{TD}">Optional (not primary)</td></tr>
  <tr><td style="{TH}">Religion</td><td style="{TD}">Mild preference, not strong filter</td></tr>
  <tr><td style="{TH}">Boarding</td><td style="{TD}">Neutral</td></tr>
</table>

<h2 style="{H2}">Three mainland-university paths (clarification)</h2>
<p style="margin:6px 0;">JAS ≠ 华侨联考. Three different routes for HK passport holders to mainland top universities — easy to confuse.</p>
<table style="{TBL}">
  <tr>
    <th style="{TH};width:24%;">Path</th>
    <th style="{TH};width:24%;">Mechanism</th>
    <th style="{TH};width:22%;">Curriculum required</th>
    <th style="{TH};width:30%;">For us (mainland optional)</th>
  </tr>
  <tr>
    <td style="{TD}"><b>JAS</b><br><span style="{MUTED}">内地高校招收香港中学文凭考试学生计划</span></td>
    <td style="{TD}">HKDSE → 165 mainland universities (incl. 清北, 复旦) — no mainland exam</td>
    <td style="{TD}"><b>Requires HKDSE</b></td>
    <td style="{TD}"><span style="{PILL_INFO}">SKIP if mainland not primary</span> Best path scale-wise but locks curriculum to DSE.</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD}"><b>港澳台华侨联招</b><br><span style="{MUTED}">HMT Joint Examination</span></td>
    <td style="{TD}">Separate exam in mainland; easier than Gaokao but real prep needed</td>
    <td style="{TD}">Any (but exam is in Chinese, mainland-style)</td>
    <td style="{TD}"><span style="{PILL_INFO}">Fallback option</span> Available later if needed.</td>
  </tr>
  <tr>
    <td style="{TD}"><b>International undergrad</b><br><span style="{MUTED}">国际本科招生</span></td>
    <td style="{TD}">Direct application to each mainland uni's intl track using IB/AP/A-Level + SAT/TOEFL</td>
    <td style="{TD}">IB / AP / A-Level all eligible</td>
    <td style="{TD}"><span style="{PILL_BEST}">PRESERVES OPTION</span> Smaller, more competitive — but keeps door open with any curriculum.</td>
  </tr>
</table>
<p style="{MUTED};margin-top:6px;">Verdict: choose curriculum on philosophy + STEM depth + future-skills — not on mainland-uni access.</p>

<h2 style="{H2}">Tier A — top-fit candidates (apply / visit first)</h2>
{isf}
{spcc}
{vsa}
{gtc}

<h2 style="{H2}">American International School (AIS HK) — independent evaluation</h2>
<div style="{CARD}">
  <div style="margin-bottom:8px;"><span style="{PILL_CAVEAT}">TIER C — backup / fit-dependent</span></div>
  <h3 style="{H3}">American International School Hong Kong</h3>
  <p style="margin:6px 0 10px 0;{MUTED}">Independent verdict, past the "not academic" reputation. Full eval (~430 lines) at <code>02-schools/american-international-school.md</code>.</p>
  <table style="{TBL}">
    <tr><td style="{TH};width:28%;">Curriculum</td><td style="{TD}">US standards-based + AP (incl. AP Capstone — Seminar + Research). Founded 1986, WASC-accredited.</td></tr>
    <tr><td style="{TH}">Location</td><td style="{TD}">125 Waterloo Road, Kowloon Tong (MTR-served)</td></tr>
    <tr><td style="{TH}">Annual tuition</td><td style="{TD}">~HK$200K (varies by grade — verify on school site)</td></tr>
    <tr><td style="{TH}">Capital / debenture</td><td style="{TD}"><b>Capital levy ~HK$12K/yr — no debenture</b> ✓ trivially within cap</td></tr>
    <tr><td style="{TH}">Admissions</td><td style="{TD}">Rolling first-come — easy entry, low friction</td></tr>
  </table>
  <p style="margin:10px 0 4px 0;"><b style="color:{C_BEST};">"Not academic" verdict —</b>
  partially accurate but mischaracterized. AIS is not weak, but not top-tier either.
  AP results sit ~10pp behind HKIS (85% scoring 3+ in 2022 vs HKIS 95% scoring 3+ in 2024–25);
  no documented MIT / Stanford / Princeton / CMU placements in the 2023–25 window
  while HKIS, ISF, ICS, CIS all show such placements. Documented placements include UC Berkeley, UCLA, NYU, Cornell, Northwestern, BU, occasional Columbia / Oxford.</p>
  <p style="margin:8px 0 4px 0;"><b style="color:{C_DANGER};">Decisive against for our family:</b><br>
  (1) <b>STEM ceiling is the load-bearing gap.</b> AIS publishes AP Calc BC + AP Physics 2 (algebra-based) as ceiling.
  <b>No AP Physics C, no Multivariable, no Linear Algebra, no Differential Equations.</b>
  HKIS publishes all of these. For a STEM-leaning family this is a hard structural gap.<br>
  (2) <b>Mandarin treated as specialist subject</b> (3–5 hr/week, ability-grouped) — <i>not</i> a content medium.
  Will plateau a Mandarin-dominant child rather than compound the asset.
  ISF, SPCC, VSA, GTC, SIS all dominate AIS on both Mandarin and academic-ceiling dimensions within the same debenture envelope.</p>
  <p style="margin:8px 0 0 0;"><b style="color:{C_BEST};">Decisive for (case for keeping on list):</b>
  no debenture (HK$12K/yr capital levy), rolling first-come admissions (easy entry),
  AP Capstone is a real research program (good fit for anti-rote preference),
  secular co-ed, Kowloon Tong MTR-served.
  <b>Use as low-friction backup</b> while applying to Tier A.</p>
</div>

<h2 style="{H2}">Tier B / C (backup portfolio)</h2>
<table style="{TBL}">
  <tr>
    <th style="{TH}">Tier</th>
    <th style="{TH}">School</th>
    <th style="{TH}">Curriculum · Location</th>
    <th style="{TH}">Annual fee · Capital</th>
    <th style="{TH}">2025 IB</th>
  </tr>
  <tr><td style="{TD}">B</td><td style="{TD}">Singapore Intl School (SIS)</td><td style="{TD}">IGCSE+IB · Aberdeen</td><td style="{TD}">HK$123–275K · capital levy</td><td style="{TD}">39.0 / 47% over 40</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">B</td><td style="{TD}">CDNIS</td><td style="{TD}">IB Continuum · Aberdeen</td><td style="{TD}">HK$161–290K · HK$80K reservation; <b style="color:{C_CAVEAT};">secondary debenture ~HK$2.2M (above cap; lower priority without)</b></td><td style="{TD}">37.7 / 38% over 40</td></tr>
  <tr><td style="{TD}">B</td><td style="{TD}">PLKCKY</td><td style="{TD}">IB · Sham Shui Po</td><td style="{TD}">HK$99–264K · ✓</td><td style="{TD}">52% over 40</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">B</td><td style="{TD}">St Stephen's College</td><td style="{TD}">IB or DSE · Stanley · boarding option</td><td style="{TD}">PR HK$74K / non-PR HK$151K · ✓</td><td style="{TD}">39.7</td></tr>
  <tr><td style="{TD}">B</td><td style="{TD}">DGS (girls only)</td><td style="{TD}">DSE + A-Level · Jordan</td><td style="{TD}">HK$42K · ✓</td><td style="{TD}">No IB; A-Level via Cambridge</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">C</td><td style="{TD}">AIS HK (American)</td><td style="{TD}">US + AP + AP Capstone · Kowloon Tong</td><td style="{TD}">~HK$200K · HK$12K/yr levy ✓</td><td style="{TD}">No IB; AP ~85% scoring 3+ (2022)</td></tr>
  <tr><td style="{TD}">C</td><td style="{TD}">Malvern College HK</td><td style="{TD}">IB Continuum · Tai Po</td><td style="{TD}">HK$209–268K · debenture (verify ≤HK$1M)</td><td style="{TD}">39.0 / 33% over 40</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">C</td><td style="{TD}">HKA (Hong Kong Academy)</td><td style="{TD}">IB Continuum · Sai Kung</td><td style="{TD}">HK$117–265K · debenture HK$630K ✓ or HK$32K/yr</td><td style="{TD}">progressive; small cohort</td></tr>
  <tr><td style="{TD}">C</td><td style="{TD}">ESF Renaissance College (RCHK)</td><td style="{TD}">All 4 IB programmes · Ma On Shan</td><td style="{TD}">HK$148–196K · NCL HK$50K ✓ (or INR HK$500K ✓)</td><td style="{TD}">36.0</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">C</td><td style="{TD}">Carmel School (Elsa High)</td><td style="{TD}">IB Continuum · MidLev/SKW</td><td style="{TD}">HK$80–226K · modest ✓</td><td style="{TD}">38.1 / 43% over 40</td></tr>
  <tr><td style="{TD}">C</td><td style="{TD}">Stamford American School</td><td style="{TD}">IB DP · Ho Man Tin / new West Kowloon HS</td><td style="{TD}">HK$217–264K · HK$150K one-off ✓ or HK$30K/yr</td><td style="{TD}">newer; first IB cohorts</td></tr>
</table>
<p style="{MUTED};margin-top:8px;">DBS excluded (boys only). Schools above debenture cap shown in next section with caveats.</p>

<h2 style="{H2}"><span style="color:{C_CAVEAT};">⚠</span> Above debenture cap — apply with realistic caveat</h2>
<div style="{CARD};border-left:4px solid {C_CAVEAT};">
  <p style="margin:0 0 8px 0;">These schools <b>do accept non-debenture applicants</b> — but realistic admission probability is materially reduced without paying for capital priority. Listed for completeness; apply only if you want to spend the application effort knowing the constraints.</p>
  <table style="{TBL}">
    <tr>
      <th style="{TH};width:18%;">School</th>
      <th style="{TH};width:24%;">Capital for priority</th>
      <th style="{TH};width:28%;">What you get with it</th>
      <th style="{TH}">Without it — realistic chance</th>
    </tr>
    <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ CIS</b></td><td style="{TD}">CNR HK$15M direct · HK$1.1–1.5M secondary market</td><td style="{TD}">Corporate Nomination Right gives priority application slot at Reception / S1</td><td style="{TD}">General-pool acceptance ~5–8%. Sibling/alumni priority + EDB 70% non-local quota tightening for 2026/27 puts HK-passport non-CNR applicants at very low odds.</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ Harrow HK</b></td><td style="{TD}">Capital Certificate ~HK$3.3M (fully resellable on secondary market)</td><td style="{TD}">Priority application slot</td><td style="{TD}">Tuen Mun location reduces demand somewhat — capacity exists. Non-Certificate chance: moderate but materially below Certificate-holder probability.</td></tr>
    <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ HKIS</b></td><td style="{TD}">Family Debenture HK$3M / Corporate HK$5M (<b>no resale</b>; par refund after 15 years)</td><td style="{TD}">Priority application slot</td><td style="{TD}">~3–5% general-pool acceptance for HK-passport applicants without sibling/alumni priority. Strictest no-resale debenture in HK — capital is locked for 15 years.</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ GSIS</b> (English stream)</td><td style="{TD}">Infrastructure Debenture HK$6M</td><td style="{TD}">"First Admissions Priority"</td><td style="{TD}">Without debenture: general pool, lower priority + tighter non-local quota. EIS English stream less competitive than GIS German stream but still demanding (avg IB 41.0).</td></tr>
    <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ YCIS</b></td><td style="{TD}">Debenture from HK$2M (resellable)</td><td style="{TD}">Priority application slot</td><td style="{TD}">YCIS less prestige-driven than CIS/HKIS — non-debenture chance is moderate but still reduced. Co-teaching bilingual model is the key draw.</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ CDNIS</b> (debenture path)</td><td style="{TD}">Secondary-market only ~HK$2.2M (school no longer issues new)</td><td style="{TD}">Priority application slot</td><td style="{TD}">Without debenture path: HK$80K reservation deposit only. CDNIS general pool is competitive but achievable for the right profile (bilingual track, mainland heritage).</td></tr>
  </table>
  <p style="{MUTED};margin-top:8px;"><b>Footnote:</b> "Capital for priority" is the up-front cost to enter the priority application tier. The "without it" estimates are heuristics from admissions consultants and parent reports — verify with each school. <b style="color:{C_CAVEAT};">The decisive factor in 2026/27 is the EDB 70% non-local quota tightening</b> (see Insight #4) — it reduces HK-passport general-pool chance at every premier international school regardless of capital. Apply with eyes open.</p>
</div>

<h2 style="{H2}">Key insights — what the research actually says</h2>
<table style="{TBL}">
  <tr>
    <th style="{TH};width:6%;">#</th>
    <th style="{TH}">Insight</th>
  </tr>
  <tr>
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">1</td>
    <td style="{TD}"><b>The 2026 evidence sharply validates your anti-rote bias.</b> METR (AI task-horizon doubling every ~7 mo) + Brynjolfsson "Canaries" study (13% relative employment decline for 22–25 yos in AI-exposed jobs) confirm: optimizing for "rank #1 on the standardised exam" optimizes for the skill being commoditized in real time.</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">2</td>
    <td style="{TD}"><b>Curriculum hierarchy for our goals:</b> A-Level + Further Maths + EPQ ≈ IB DP (strong school) ≈ AP Capstone (only HKIS / AIS in HK) > dual-track DSE+IB > pure DSE.</td>
  </tr>
  <tr>
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">3</td>
    <td style="{TD}"><b>DSS arbitrage is real.</b> SPCC topped HK IB at 42.1 average in 2025 at ~HK$160K · GTC at HK$88K hit 40.04 / 56% over 40 — outcomes comparable to or better than international schools at fractions of cost.</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">4</td>
    <td style="{TD}"><b>HK passport is now a <i>disadvantage</i>, not advantage, at premier internationals.</b> EDB 70% non-local quota tightening for 2026/27 — eight school operators including ESF failed targets in 2025/26. ESF Individual Nomination Right HK$500K is the cheapest priority lever in HK.</td>
  </tr>
  <tr>
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">5</td>
    <td style="{TD}"><b>Mandarin-native is an asset, not a remediation problem.</b> Schools that compound it: ISF (70/30), CIS (50/50), VSA, CDNIS bilingual track, YCIS co-teaching, SIS, SPCC. AIS HK does NOT compound — Mandarin is a 3–5 hr/wk specialist subject there.</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">6</td>
    <td style="{TD}"><b>Mainland-uni paths are 3 distinct routes, not 1.</b> Since mainland is optional for us, IB or A-Level both preserve credible (smaller) paths via international undergrad admissions — no need to bias curriculum to DSE.</td>
  </tr>
</table>

<h2 style="{H2}">Action timeline (2.5 yo girl)</h2>
<table style="{TBL}">
  <tr>
    <th style="{TH};width:14%;">Year</th>
    <th style="{TH};width:10%;">Age</th>
    <th style="{TH}">Action</th>
  </tr>
  <tr>
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2026 (now)</td>
    <td style="{TD}">2.5–3</td>
    <td style="{TD}"><b style="color:{C_DANGER};">URGENT:</b> ESF K2 applications open Sep 2026 for AY2027/28 entry (she IS eligible under ESF Dec 31 cutoff). <b>Buy ESF Individual Nomination Right HK$500K BEFORE applying</b> if any ESF school on list. Stay at Tutor Time. <b>Visit 4–6 target schools</b>. (Note: CDNIS Oct 2026 / SIS Sep 2026 deadlines are for AY2027/28 = kids born Sep 2022 or earlier — NOT her cohort.)</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2027</td>
    <td style="{TD}">3–4</td>
    <td style="{TD}"><b>VSA Y1 application window</b> (~Feb 2027 for AY2028/29 entry). K2 / Reception applications at thru-train internationals: HKA, Stamford, Malvern, Carmel.</td>
  </tr>
  <tr>
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2028</td>
    <td style="{TD}">4–5</td>
    <td style="{TD}"><b>P1/Y1 applications open at ISF, SPCC, GTC, ESF.</b> Continue English exposure → ~50/50 by P1 entry. Begin DSS feeder strategy.</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2029</td>
    <td style="{TD}">5–6</td>
    <td style="{TD}"><b>P1 entry</b> at chosen primary school for AY2029/30. Notifications spring 2029.</td>
  </tr>
  <tr>
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2030</td>
    <td style="{TD}">6–7</td>
    <td style="{TD}">P1 in session (or already at thru-train if K2-entered earlier in 2027/28).</td>
  </tr>
</table>
<p style="{MUTED};margin-top:6px;">
Strategic positioning given DOB (mid-Sep 2023): the <b>only</b> action in next 4 months is the <b>ESF K2 application (Sep 2026)</b> for AY2027/28 entry — buy the Individual Nomination Right HK$500K first.
Then <b>main K2/Reception application wave Sep–Oct 2027</b> for thru-train internationals (ISF FY, VSA Y1, CDNIS EY1, SIS Prep, RCHK, HKA, Stamford, Carmel, Malvern) for AY2028/29 entry.
<b>Then P1 wave Sep 2028</b> for top DSS (SPCC, GTC, DGS) for AY2029/30 entry.
With Mandarin-dominant profile, ISF FY at AY2028/29 is the strongest single positioning.
</p>

<h2 style="{H2}">Estimated 12-year cost (rough order of magnitude)</h2>
<table style="{TBL}">
  <tr>
    <th style="{TH}">School</th>
    <th style="{TH}">Annual avg × 12</th>
    <th style="{TH}">Capital / debenture</th>
    <th style="{TH}">Total est. (HK$)</th>
    <th style="{TH}">Within cap?</th>
  </tr>
  <tr><td style="{TD}"><b>GTC</b> (NSS→IBDP)</td><td style="{TD}">HK$70K × 12 = HK$0.84M</td><td style="{TD}">None</td><td style="{TD}"><b>HK$0.84M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>SPCC</b> (DSE→IB local)</td><td style="{TD}">HK$130K × 12 = HK$1.56M</td><td style="{TD}">None</td><td style="{TD}"><b>HK$1.56M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr><td style="{TD}"><b>VSA</b></td><td style="{TD}">HK$180K × 12 = HK$2.16M</td><td style="{TD}">Modest one-off</td><td style="{TD}"><b>~HK$2.2M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>RCHK</b> (no INR)</td><td style="{TD}">HK$170K × 12 = HK$2.04M</td><td style="{TD}">HK$50K NCL</td><td style="{TD}"><b>~HK$2.1M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr><td style="{TD}"><b>RCHK + INR</b> (priority)</td><td style="{TD}">HK$170K × 12 = HK$2.04M</td><td style="{TD}">+HK$500K INR</td><td style="{TD}"><b>~HK$2.55M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>AIS HK</b></td><td style="{TD}">HK$200K × 12 = HK$2.4M</td><td style="{TD}">HK$12K × 12 = HK$0.144M</td><td style="{TD}"><b>~HK$2.55M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr><td style="{TD}"><b>ISF</b> (Annual Capital Levy)</td><td style="{TD}">HK$200K × 12 = HK$2.4M</td><td style="{TD}">HK$40K × 12 = HK$0.48M</td><td style="{TD}"><b>HK$2.88M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>HKA</b></td><td style="{TD}">HK$190K × 12 = HK$2.28M</td><td style="{TD}">HK$630K family debenture (refundable; verify)</td><td style="{TD}"><b>~HK$2.9M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ CDNIS</b> (debenture path)</td><td style="{TD}">HK$226K × 12 = HK$2.7M</td><td style="{TD}">~HK$2.2M secondary debenture</td><td style="{TD}"><b>~HK$4.9M</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">OVER CAP</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ Harrow HK</b></td><td style="{TD}">HK$185K × 12 = HK$2.22M</td><td style="{TD}">Capital Certificate ~HK$3.3M (resellable)</td><td style="{TD}"><b>~HK$5.5M</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">OVER CAP</span></td></tr>
  <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ YCIS</b></td><td style="{TD}">HK$210K × 12 = HK$2.52M</td><td style="{TD}">~HK$2M debenture (resellable)</td><td style="{TD}"><b>~HK$4.5M+</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">OVER CAP</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ HKIS</b></td><td style="{TD}">HK$265K × 12 = HK$3.18M</td><td style="{TD}">HK$3–5M debenture (no resale)</td><td style="{TD}"><b>HK$6M+</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">OVER CAP</span></td></tr>
  <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ GSIS</b> (English stream)</td><td style="{TD}">HK$170K × 12 = HK$2.04M</td><td style="{TD}">HK$6M Infrastructure Debenture</td><td style="{TD}"><b>HK$8M+</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">OVER CAP</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ CIS direct</b></td><td style="{TD}">HK$235K × 12 = HK$2.82M</td><td style="{TD}">HK$15M CNR</td><td style="{TD}"><b>HK$17M+</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">OVER CAP</span></td></tr>
</table>
<p style="{MUTED};margin-top:6px;">Numbers are <i>order-of-magnitude</i> using current fee snapshots; refundable debentures partially recoverable; sibling discounts not applied. Verify with each school before committing.</p>

<p style="margin:14px 0 6px 0;"><b>Cost-efficient frontier within debenture cap</b>:</p>
<ul style="margin:0 0 0 18px;padding:0;">
  <li><b>GTC ~HK$0.84M total</b> — hardest to beat on $/IB-point if TKO commute is acceptable</li>
  <li><b>SPCC ~HK$1.56M</b> — top IB outcomes in HK at moderate cost</li>
  <li><b>VSA ~HK$2.2M</b> · <b>RCHK ~HK$2.1M</b> — bilingual IB Continuum, mid-cost</li>
  <li><b>ISF ~HK$2.88M</b> — premium cost, best-in-HK Mandarin immersion</li>
  <li><b>AIS HK ~HK$2.55M</b> — within cap but Tier C on fit (STEM ceiling + Mandarin dilution)</li>
</ul>

<h2 style="{H2}">Next steps</h2>
<ol style="margin:6px 0 6px 18px;padding:0;">
  <li><b style="color:{C_DANGER};">URGENT (next 5 months):</b> apply to CDNIS EY1 (deadline 2026-10-02) and SIS HK Prep Years (deadline 2026-09-30). Confirm child's exact DOB to verify age cohort fit.</li>
  <li><b>Decide</b>: thru-train international K2 (CDNIS / SIS) vs P1 portfolio (SPCC, GTC, DGS) in 2028</li>
  <li><b>Visit</b> ISF + SPCC + GTC + VSA in next 3 months</li>
  <li><b>Buy ESF Individual Nomination Right HK$500K</b> if any ESF school on list — cheapest priority lever in HK</li>
  <li><b>Continue English exposure at home</b> — aim for ~50/50 by K3 entry</li>
  <li><b>Re-score</b> shortlist after visits in <code>04-evaluation/shortlist.md</code></li>
</ol>

<div style="margin-top:24px;padding:14px;background:{C_TBL_HDR};border-radius:8px;{MUTED}">
  Full knowledge base lives at
  <a style="{LINK}" href="https://github.com/astronvc/school-picker">github.com/astronvc/school-picker</a>.
  See <code>04-evaluation/application-windows.md</code> for full per-school deadline detail
  and <code>02-schools/american-international-school.md</code> for the AIS HK deep eval.
  <br>
  Generated by tools/send_summary_email.py · {TODAY}
</div>

</div>
</body>
</html>
"""


# ---------- 中文 (Mandarin / Simplified Chinese) content ----------

def build_zh_html():
    fld = {
        "curriculum": "课程",
        "location": "位置",
        "fees": "年学费 (2025/26)",
        "capital": "资本费 / 债权",
        "ib": "2025 IB 成绩",
        "mandarin": "普通话项目",
        "app_window": "申请窗口",
        "apply": "申请链接",
    }
    why_lbl, caveat_lbl = "优势", "注意事项"

    isf = school_card(
        PILL_BEST, "第一梯队 — 最佳匹配",
        "弘立书院 The ISF Academy",
        [
            (fld["curriculum"], "IB MYP + DP；Foundation Year 至 G4 阶段 <b>70%普通话 / 30%英语</b>"),
            (fld["location"], "数码港，薄扶林（港岛西）"),
            (fld["fees"], "港币 152,880（FY）→ 港币 241,110（G11–12）"),
            (fld["capital"], "<b>年度资本费 港币40,000/年</b>（在上限内）· 也可选一次性较大额的 Capital Note"),
            (fld["ib"], "平均 38.6，51% 超 40 分，1 人满分 45"),
            (fld["mandarin"], "<b>香港最深入的真正普通话沉浸式教学</b> — 初中阶段 70/30 比例；非常适合普通话主导的孩子"),
            (fld["app_window"], "<b>FY 入学（4 岁）</b> — 按她出生日期（2023 年 9 月中，Aug 31 截止），目标 <b>AY2028/29 入学</b>。申请约 2027 年 9 月开放（约 16 个月后）。FY 是 ISF 小学的主要入学点。"),
            (fld["apply"], f'<a style="{LINK}" href="https://academy.isf.edu.hk/admissions/">academy.isf.edu.hk/admissions</a>'),
        ],
        why_lbl,
        "香港最契合普通话主导女孩的学校。双语 + IB + 中华美德 + 数码港设施。年度资本费完全避开了大额债权陷阱。",
        caveat_lbl,
        "并非顶尖 STEM（可通过奥数/外部数学补足）；高年级中文比例略下降；FY 招生竞争激烈。",
    )

    spcc = school_card(
        PILL_BEST, "第一梯队 — 最佳匹配",
        "圣保罗男女中学 St Paul's Co-educational College (SPCC)",
        [
            (fld["curriculum"], "DSE + IB DP <b>双轨并行</b>，自 S5 选择（DSS 直资双轨）"),
            (fld["location"], "麦当奴道，半山（港岛中部）"),
            (fld["fees"], "DSE 约港币 70,000 · IB 本地约港币 160,000 · IB 非本地约港币 201,000"),
            (fld["capital"], "<b>无</b> ✓（小学部资本费/债权未公开 — 参访时核实）"),
            (fld["ib"], "<b>平均 42.1 — 2025 年香港第一</b>"),
            (fld["mandarin"], "英语为教学语言，配合扎实的普通话/中文；具相当数量的内地背景学生群体"),
            (fld["app_window"], "<b>P1 入学</b> — 目标 2028 年 9 月申请，对应 2029/30 学年（2029 年 9 月升 P1）。SPCC Primary 直属小学是关键入口。"),
            (fld["apply"], f'<a style="{LINK}" href="https://www.spcc.edu.hk/admissions/">spcc.edu.hk/admissions</a>'),
        ],
        why_lbl,
        "香港顶尖学术成绩，费用却仅为国际学校的零头。无债权、对内地背景家庭友好、地理位置中心。男女合校；双轨制保留 DSE 选项。",
        caveat_lbl,
        "S1 录取比例约 20:1；SPCC Primary 直属小学是关键入口 — P1 申请是 2028–29 学年的核心窗口。",
    )

    vsa = school_card(
        PILL_INFO, "第一梯队 — 强势选项",
        "维多利亚（上海）学校 Victoria Shanghai Academy (VSA)",
        [
            (fld["curriculum"], "IB Continuum（PYP, MYP, DP）；小学阶段英语 + 普通话双语"),
            (fld["location"], "香港仔/深湾（港岛南）"),
            (fld["fees"], "约港币 130,000 → 230,000，因年级而异"),
            (fld["capital"], "一次性资本费用，金额温和 ✓ 在上限内（确切债权金额未公布 — 请核实）"),
            (fld["ib"], "平均 37.6（2025 年 5 名满分）"),
            (fld["mandarin"], "强双语模型 — 是香港追求真正普通话教育家庭的首选之一"),
            (fld["app_window"], "<b>Y1 入学</b> — 2027/28 学年截止日已过（2026-02-05）。约 2027 年 2 月申请，对应 2028/29 学年入学。第 1 + 2 轮小组面试；无笔试。"),
            (fld["apply"], f'<a style="{LINK}" href="https://www.vsa.edu.hk/admissions/">vsa.edu.hk/admissions</a>'),
        ],
        why_lbl,
        "中等成本的双语 IB Continuum；比 ISF/CIS 更易入读。对内地背景家庭友好。",
        caveat_lbl,
        "香港仔通勤可能不适合鲗鱼涌一带（请确认）；学术上限略低于 SPCC。",
    )

    gtc = school_card(
        PILL_INFO, "第一梯队 — 强势选项",
        "优才（杨殷有娣）书院 G.T. (Ellen Yeung) College",
        [
            (fld["curriculum"], "本地 NSS（DSE）+ 高年级 IB DP"),
            (fld["location"], "调景岭，将军澳"),
            (fld["fees"], "DSE 约港币 44,000 · <b>IBDP 港币 88,550</b>（DSS 范围下限自港币 35,310 起）"),
            (fld["capital"], "<b>无</b> ✓"),
            (fld["ib"], "<b>平均 40.04，56% 超 40 分</b> — 在此费用水平堪称卓越"),
            (fld["mandarin"], "英语为教学语言，配以扎实中文；对内地背景家庭友好"),
            (fld["app_window"], "<b>P1 入学</b> — 目标 2028 年 9 月申请，对应 2029/30 学年（2029 年 9 月升 P1）。面试形式/通知未公开 — 参访时确认。"),
            (fld["apply"], f'<a style="{LINK}" href="https://www.gtcollege.edu.hk/admission">gtcollege.edu.hk/admission</a>'),
        ],
        why_lbl,
        "以国际学校零头的费用，达到世界一流的 IB 成绩。资优教育法与「反应试、研究导向」理念高度契合。",
        caveat_lbl,
        "TKO（将军澳）位置（从港岛东通勤偏远）；直通车意味着早期承诺。",
    )

    return f"""<!doctype html>
<html lang="zh-Hans">
<head><meta charset="utf-8"><title>香港选校 — 个性化总结</title></head>
<body style="margin:0;padding:0;background:{C_BG};">
<div style="{WRAP}">

<div style="{CARD}">
  <h1 style="{H1}">香港选校 — 个性化总结</h1>
  <div style="{MUTED}">适合：2.5 岁女孩 · 香港护照 · 内地家庭背景 · 普通话为主
  · 资本/债权上限港币 100 万 · 内地大学非主选</div>
  <div style="{MUTED};margin-top:6px;">
    资料库：
    <a style="{LINK}" href="https://github.com/astronvc/school-picker">github.com/astronvc/school-picker</a>
    · 生成于 {TODAY}
  </div>
</div>

<h2 style="{H2_DANGER}"><span style="{PILL_URGENT}">紧急</span> &nbsp; 按出生日期重订时间表</h2>
<div style="{URGENT_CARD}">
  <p style="margin:0 0 8px 0;">孩子出生日期已确认：<b>2023 年 9 月中</b>。她是"九月生"，正好处于多数学校的年龄截止线临界点。<b>含义：之前提到的 CDNIS 2026 年 10 月 / SIS 2026 年 9 月截止日（针对 2027/28 学年入学）<u>不适用</u>于她的年龄层</b> — 那是给 2022 年 9 月之前出生的孩子的。</p>
  <table style="{TBL}">
    <tr>
      <th style="{TH};width:14%;">截止日</th>
      <th style="{TH};width:36%;">学校</th>
      <th style="{TH};width:24%;">她的年龄层</th>
      <th style="{TH}">行动窗口</th>
    </tr>
    <tr><td style="{TD}"><b>8 月 31 日</b></td><td style="{TD}">大多数国际学校（CDNIS、SIS、ISF、VSA、CIS、HKIS、HKA、Stamford、Carmel、Malvern、NAIS）</td><td style="{TD}">AY2028/29 K2/Reception/FY/EY1 入学（2028 年 8 月 31 日时 4 岁 11 个月）</td><td style="{TD}"><b>2027 年 9–10 月申请</b>（约 16 个月后）</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>12 月 31 日</b></td><td style="{TD}">ESF 幼稚园</td><td style="{TD}"><b>ESF K2 AY2027/28 入学</b>（2027 年 12 月 31 日时 4 岁 3 个月）</td><td style="{TD}"><b style="color:{C_DANGER};">2026 年 9 月申请</b>（约 4 个月后）</td></tr>
    <tr><td style="{TD}"><b>12 月 31 日</b>（香港本地）</td><td style="{TD}">DSS（SPCC、GTC、DGS）</td><td style="{TD}">AY2029/30 P1 入学</td><td style="{TD}">2028 年 9 月申请（约 28 个月后）</td></tr>
  </table>
  <p style="margin:8px 0 0 0;"><b style="color:{C_DANGER};">唯一现实紧急的日期：</b><b>2026 年 9 月 — ESF K2 申请开放，对应 AY2027/28 入学。</b>若名单中有 ESF 学校（RCHK、Discovery College、Hillside International Kindergarten 等），<b>申请前必须购买 ESF 个人提名权港币 50 万</b>（申请时需已在手；港币 50 万是香港最便宜的优先入学杠杆）。</p>
</div>

<h2 style="{H2}">家庭概况</h2>
<table style="{TBL}">
  <tr><td style="{TH}">孩子</td><td style="{TD}">2.5 岁女孩，目前就读 Tutor Time Dorset（鲗鱼涌一带，校内英语/中文约 50/50）</td></tr>
  <tr><td style="{TH}">家庭语言</td><td style="{TD}">在家约 70% 普通话 / 30% 英语 — 普通话为主</td></tr>
  <tr><td style="{TH}">国籍</td><td style="{TD}">香港护照（孩子）；父母来自中国内地</td></tr>
  <tr><td style="{TH}">教育理念</td><td style="{TD}">重视学术 + 自信 + 竞争力 — <b>反对</b>做题/考试/填鸭式；崇尚独立思考 + 研究方法 + STEM 深度</td></tr>
  <tr><td style="{TH}">年学费</td><td style="{TD}">不限</td></tr>
  <tr><td style="{TH}">资本费/债权上限</td><td style="{TD}"><b>港币 1,000,000</b></td></tr>
  <tr><td style="{TH}">内地大学</td><td style="{TD}">可选（非主要）</td></tr>
  <tr><td style="{TH}">宗教取向</td><td style="{TD}">略有偏好，但非强约束</td></tr>
  <tr><td style="{TH}">寄宿</td><td style="{TD}">不优先不排除</td></tr>
</table>

<h2 style="{H2}">进入内地大学的三种途径（澄清）</h2>
<p style="margin:6px 0;">JAS ≠ 华侨联考。香港护照持有者进入内地一流大学有三条不同的途径 — 容易混淆。</p>
<table style="{TBL}">
  <tr>
    <th style="{TH};width:24%;">途径</th>
    <th style="{TH};width:24%;">机制</th>
    <th style="{TH};width:22%;">所需课程</th>
    <th style="{TH};width:30%;">对我们而言（内地非主选）</th>
  </tr>
  <tr>
    <td style="{TD}"><b>JAS</b><br><span style="{MUTED}">内地高校招收香港中学文凭考试学生计划</span></td>
    <td style="{TD}">凭 HKDSE 申请 165 所内地大学（含清北、复旦）— 不需另考</td>
    <td style="{TD}"><b>必须考 HKDSE</b></td>
    <td style="{TD}"><span style="{PILL_INFO}">内地非主选则可跳过</span> 规模最大的途径，但课程锁定为 DSE。</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD}"><b>港澳台华侨联招</b><br><span style="{MUTED}">HMT 联合招生考试</span></td>
    <td style="{TD}">在内地的另一种考试；比高考容易但仍需认真准备</td>
    <td style="{TD}">任何课程（但考试为中文，按内地风格）</td>
    <td style="{TD}"><span style="{PILL_INFO}">备用方案</span> 如有需要可日后启用。</td>
  </tr>
  <tr>
    <td style="{TD}"><b>国际本科招生</b><br><span style="{MUTED}">International undergrad</span></td>
    <td style="{TD}">用 IB/AP/A-Level + SAT/TOEFL 直接申请各内地大学的国际本科项目</td>
    <td style="{TD}">IB / AP / A-Level 皆可</td>
    <td style="{TD}"><span style="{PILL_BEST}">保留选项</span> 规模较小、竞争激烈 — 但任何课程都能保留这扇门。</td>
  </tr>
</table>
<p style="{MUTED};margin-top:6px;">结论：基于教育理念 + STEM 深度 + 未来能力来选课程 — 而非以内地大学准入为导向。</p>

<h2 style="{H2}">第一梯队 — 最佳匹配（优先申请/参访）</h2>
{isf}
{spcc}
{vsa}
{gtc}

<h2 style="{H2}">美国国际学校（AIS HK）— 独立评估</h2>
<div style="{CARD}">
  <div style="margin-bottom:8px;"><span style="{PILL_CAVEAT}">第三梯队 — 备选/视情况而定</span></div>
  <h3 style="{H3}">美国国际学校 American International School Hong Kong</h3>
  <p style="margin:6px 0 10px 0;{MUTED}">独立结论，超越"不够学术"的口碑。完整评估（约 430 行）在 <code>02-schools/american-international-school.md</code>。</p>
  <table style="{TBL}">
    <tr><td style="{TH};width:28%;">课程</td><td style="{TD}">美国课标 + AP（含 AP Capstone：Seminar + Research）。1986 年创立，WASC 认证。</td></tr>
    <tr><td style="{TH}">位置</td><td style="{TD}">九龙塘窝打老道 125 号（地铁可达）</td></tr>
    <tr><td style="{TH}">年学费</td><td style="{TD}">约港币 200K（按年级而异 — 请向学校核实）</td></tr>
    <tr><td style="{TH}">资本费/债权</td><td style="{TD}"><b>资本费约港币 12K/年 — 无债权</b> ✓ 远在上限内</td></tr>
    <tr><td style="{TH}">招生</td><td style="{TD}">先到先得 — 入学容易、阻力小</td></tr>
  </table>
  <p style="margin:10px 0 4px 0;"><b style="color:{C_BEST};">"不够学术"的结论 —</b>
  部分属实但被误读。AIS 并非弱校，但也不属顶尖。AP 成绩约比 HKIS 落后 10 个百分点
  （AIS 2022 年 85% 得 3+ 分 vs HKIS 2024–25 年 95% 得 3+ 分）；
  2023–25 窗口期未见 MIT/斯坦福/普林斯顿/CMU 录取记录，而 HKIS、ISF、ICS、CIS 均有此类记录。
  有据可查的录取包括 UC Berkeley、UCLA、NYU、Cornell、Northwestern、BU，偶有 Columbia / Oxford。</p>
  <p style="margin:8px 0 4px 0;"><b style="color:{C_DANGER};">不适合我们家庭的关键原因：</b><br>
  (1) <b>STEM 上限是核心短板。</b>AIS 公开课程上限为 AP Calc BC + AP Physics 2（代数版）。
  <b>没有 AP Physics C、没有多变量微积分、没有线性代数、没有微分方程。</b>
  HKIS 全部都有。对 STEM 倾向的家庭而言，这是结构性硬伤。<br>
  (2) <b>普通话作为专项科目</b>（每周 3–5 小时，按能力分组）— <i>而非</i>内容媒介。
  对普通话主导的孩子，会让母语优势停滞，而不是复利化。
  ISF、SPCC、VSA、GTC、SIS 在相同债权预算内，无论普通话还是学术上限均胜过 AIS。</p>
  <p style="margin:8px 0 0 0;"><b style="color:{C_BEST};">保留在名单的理由：</b>
  无债权（港币 12K/年资本费）、先到先得招生（入学容易）、
  AP Capstone 是真正的研究项目（契合反应试理念）、
  非宗教、男女合校、九龙塘地铁直达。
  <b>可作为申请第一梯队时的低阻力备选</b>。</p>
</div>

<h2 style="{H2}">第二/三梯队（备选）</h2>
<table style="{TBL}">
  <tr>
    <th style="{TH}">梯队</th>
    <th style="{TH}">学校</th>
    <th style="{TH}">课程·位置</th>
    <th style="{TH}">年费·资本费</th>
    <th style="{TH}">2025 IB</th>
  </tr>
  <tr><td style="{TD}">B</td><td style="{TD}">新加坡国际学校 (SIS)</td><td style="{TD}">IGCSE+IB · 香港仔</td><td style="{TD}">港币 123–275K · 资本费</td><td style="{TD}">39.0 / 47% 超 40</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">B</td><td style="{TD}">加拿大国际学校 (CDNIS)</td><td style="{TD}">IB Continuum · 香港仔</td><td style="{TD}">港币 161–290K · 港币 80K 预订金；<b style="color:{C_CAVEAT};">二级市场债权约港币 220 万（超出上限；不购买则优先级降低）</b></td><td style="{TD}">37.7 / 38% 超 40</td></tr>
  <tr><td style="{TD}">B</td><td style="{TD}">保良局蔡继有学校 (PLKCKY)</td><td style="{TD}">IB · 深水埗</td><td style="{TD}">港币 99–264K · ✓</td><td style="{TD}">52% 超 40</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">B</td><td style="{TD}">圣士提反书院 (SSC)</td><td style="{TD}">IB 或 DSE · 赤柱 · 含寄宿选项</td><td style="{TD}">本地港币 74K / 非本地 151K · ✓</td><td style="{TD}">39.7</td></tr>
  <tr><td style="{TD}">B</td><td style="{TD}">拔萃女书院 DGS（仅女生）</td><td style="{TD}">DSE + A-Level · 佐敦</td><td style="{TD}">港币 42K · ✓</td><td style="{TD}">无 IB；提供 A-Level（剑桥）</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">C</td><td style="{TD}">美国国际学校 AIS HK</td><td style="{TD}">美国课标 + AP + AP Capstone · 九龙塘</td><td style="{TD}">约港币 200K · 港币 12K/年资本费 ✓</td><td style="{TD}">无 IB；AP 约 85% 得 3+ 分（2022）</td></tr>
  <tr><td style="{TD}">C</td><td style="{TD}">墨尔文国际学校 Malvern HK</td><td style="{TD}">IB Continuum · 大埔</td><td style="{TD}">港币 209–268K · 债权（请核实 ≤港币 100 万）</td><td style="{TD}">39.0 / 33% 超 40</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">C</td><td style="{TD}">香港学堂 HKA</td><td style="{TD}">IB Continuum · 西贡</td><td style="{TD}">港币 117–265K · 债权 港币 630K ✓ 或港币 32K/年</td><td style="{TD}">进步式；小班</td></tr>
  <tr><td style="{TD}">C</td><td style="{TD}">启新书院 (RCHK / ESF)</td><td style="{TD}">全 4 个 IB 项目 · 马鞍山</td><td style="{TD}">港币 148–196K · NCL 港币 50K ✓（或 INR 港币 500K ✓）</td><td style="{TD}">36.0</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">C</td><td style="{TD}">嘉米利学校 Carmel (Elsa High)</td><td style="{TD}">IB Continuum · 半山/筲箕湾</td><td style="{TD}">港币 80–226K · 温和 ✓</td><td style="{TD}">38.1 / 43% 超 40</td></tr>
  <tr><td style="{TD}">C</td><td style="{TD}">史丹福美国学校 SAIS</td><td style="{TD}">IB DP · 何文田 / 西九新中学校园</td><td style="{TD}">港币 217–264K · 港币 150K 一次性 ✓ 或港币 30K/年</td><td style="{TD}">较新；首批 IB 学生</td></tr>
</table>
<p style="{MUTED};margin-top:8px;">DBS 排除（仅招男生）。超出债权上限的学校见下一节，附带说明。</p>

<h2 style="{H2}"><span style="color:{C_CAVEAT};">⚠</span> 超出债权上限 — 申请须有现实预期</h2>
<div style="{CARD};border-left:4px solid {C_CAVEAT};">
  <p style="margin:0 0 8px 0;">这些学校<b>都接受不购买债权的申请</b>—但若不支付资本优先费用，实际录取概率会大幅降低。此处列出仅供参考；只在愿意付出申请成本并理解此限制的前提下申请。</p>
  <table style="{TBL}">
    <tr>
      <th style="{TH};width:18%;">学校</th>
      <th style="{TH};width:24%;">优先所需资本</th>
      <th style="{TH};width:28%;">购买后享有</th>
      <th style="{TH}">不购买 — 现实概率</th>
    </tr>
    <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ CIS</b></td><td style="{TD}">CNR 港币 1500 万直接申请 · 港币 110–150 万二级市场</td><td style="{TD}">Corporate Nomination Right 在 Reception / S1 阶段享有优先申请位</td><td style="{TD}">普通申请池约 5–8% 录取率。兄姐/校友优先 + EDB 2026/27 学年 70% 非本地比例收紧，使香港护照无 CNR 申请者机会非常低。</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ Harrow HK</b></td><td style="{TD}">Capital Certificate 约港币 330 万（二级市场可全部转售）</td><td style="{TD}">优先申请位</td><td style="{TD}">屯门地理位置使需求略低 — 仍有空位。不购买 Certificate 的机会：中等，但显著低于持有者。</td></tr>
    <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ HKIS</b></td><td style="{TD}">家庭债权港币 300 万 / 企业港币 500 万（<b>不可转售</b>；15 年后按面值退还）</td><td style="{TD}">优先申请位</td><td style="{TD}">普通申请池约 3–5% 录取率（针对无兄姐/校友优先的香港护照申请者）。香港最严格的不可转售债权 — 资金锁定 15 年。</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ GSIS</b>（英语流）</td><td style="{TD}">Infrastructure Debenture 港币 600 万</td><td style="{TD}">"首选录取优先权"</td><td style="{TD}">不购买债权：普通申请池，优先级较低 + 非本地比例收紧。EIS 英语流比 GIS 德语流竞争略缓但仍需高分（IB 平均 41.0）。</td></tr>
    <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ YCIS</b></td><td style="{TD}">债权自港币 200 万起（可转售）</td><td style="{TD}">优先申请位</td><td style="{TD}">YCIS 知名度不及 CIS/HKIS — 不购买债权的机会中等但仍受影响。协同教学双语模式是主要卖点。</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ CDNIS</b>（债权路径）</td><td style="{TD}">仅二级市场约港币 220 万（学校已不再发行新债权）</td><td style="{TD}">优先申请位</td><td style="{TD}">不购买债权：仅需港币 80K 预订金。CDNIS 普通申请池竞争激烈，但合适背景（双语班、内地背景）仍可争取。</td></tr>
  </table>
  <p style="{MUTED};margin-top:8px;"><b>脚注：</b>"优先所需资本"是进入优先申请层级的前期成本。"不购买"的估算来自招生顾问与家长反馈 — 请向各校核实。<b style="color:{C_CAVEAT};">2026/27 学年的关键因素是 EDB 70% 非本地学生比例收紧</b>（见洞察 #4）— 它使所有顶尖国际学校的香港护照普通申请池机会都受影响，与是否购买资本无关。申请前请充分了解。</p>
</div>

<h2 style="{H2}">核心洞察 — 研究的真实结论</h2>
<table style="{TBL}">
  <tr>
    <th style="{TH};width:6%;">序号</th>
    <th style="{TH}">洞察</th>
  </tr>
  <tr>
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">1</td>
    <td style="{TD}"><b>2026 年的证据强力验证了您反对应试教育的立场。</b>METR（AI 完成任务的时长每约 7 个月翻倍）+ Brynjolfsson "矿井金丝雀"研究（22–25 岁青年在 AI 暴露行业的相对就业下降 13%）共同证实：以"标准考试第一名"为目标，正是在优化 AI 正在快速商品化的能力。</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">2</td>
    <td style="{TD}"><b>符合我们目标的课程排序：</b>A-Level + 高等数学 + EPQ ≈ IB DP（在优秀学校）≈ AP Capstone（香港仅 HKIS / AIS 提供）> DSE+IB 双轨 > 纯 DSE。</td>
  </tr>
  <tr>
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">3</td>
    <td style="{TD}"><b>DSS（直资）的价值差距真实存在。</b>SPCC 以平均 42.1 分位居 2025 年香港 IB 榜首，年费约港币 16 万 · GTC 年费仅港币 8.8 万即达 40.04 / 56% 超 40 分 — 成果可与国际学校媲美甚至更优，费用却远低。</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">4</td>
    <td style="{TD}"><b>在顶尖国际学校，香港护照如今反而是<i>劣势</i>而非优势。</b>EDB（教育局）2026/27 学年的 70% 非本地学生比例收紧 — 2025/26 学年有八家学校（包括 ESF）未达标。ESF 个人提名权港币 50 万是香港最便宜的优先入学杠杆。</td>
  </tr>
  <tr>
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">5</td>
    <td style="{TD}"><b>普通话母语是优势，而非补救对象。</b>能将其转化为复利优势的学校：ISF（70/30）、CIS（50/50）、VSA、CDNIS 双语班、YCIS 协同教学、SIS、SPCC。AIS HK 不会复利化普通话 — 在那里普通话只是每周 3–5 小时的专项科目。</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">6</td>
    <td style="{TD}"><b>进入内地大学不只一条途径，而是三条。</b>鉴于我们将内地大学视为可选项，IB 或 A-Level 都能通过国际本科招生保留可行（虽规模较小）的路径 — 无需为此倾斜课程到 DSE。</td>
  </tr>
</table>

<h2 style="{H2}">行动时间表（2.5 岁女孩）</h2>
<table style="{TBL}">
  <tr>
    <th style="{TH};width:14%;">年份</th>
    <th style="{TH};width:10%;">年龄</th>
    <th style="{TH}">行动</th>
  </tr>
  <tr>
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2026（现在）</td>
    <td style="{TD}">2.5–3 岁</td>
    <td style="{TD}"><b style="color:{C_DANGER};">紧急：</b>ESF K2 申请 2026 年 9 月开放，对应 AY2027/28 入学（按 ESF 12 月 31 日截止，她确实符合资格）。若名单中有 ESF 学校，<b>申请前购买 ESF 个人提名权港币 50 万</b>。继续就读 Tutor Time。<b>参访 4–6 所目标学校</b>。（注：CDNIS 2026 年 10 月 / SIS 2026 年 9 月截止日针对 AY2027/28 入学 = 2022 年 9 月之前出生的孩子 — <u>不是</u>她的年龄层。）</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2027</td>
    <td style="{TD}">3–4 岁</td>
    <td style="{TD}"><b>VSA Y1 申请窗口</b>（约 2027 年 2 月，对应 2028/29 学年入学）。其他直通车国际学校 K2/Reception 阶段申请：HKA、Stamford、Malvern、Carmel。</td>
  </tr>
  <tr>
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2028</td>
    <td style="{TD}">4–5 岁</td>
    <td style="{TD}"><b>ISF、SPCC、GTC、ESF 的 P1/Y1 申请开放。</b>继续培养英语 → 至 P1 入学时约 50/50。如选直资路线，启动 DSS feeder 策略。</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2029</td>
    <td style="{TD}">5–6 岁</td>
    <td style="{TD}"><b>P1 入学</b>所选小学，对应 2029/30 学年。通知约 2029 年春季。</td>
  </tr>
  <tr>
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2030</td>
    <td style="{TD}">6–7 岁</td>
    <td style="{TD}">P1 课程进行中（或若已在 K2 阶段进入直通车则继续就读）。</td>
  </tr>
</table>
<p style="{MUTED};margin-top:6px;">
按出生日期（2023 年 9 月中）的战略定位：未来 4 个月内<b>唯一</b>需采取的行动是 <b>ESF K2 申请（2026 年 9 月）</b>对应 AY2027/28 入学 — 之前需先购买个人提名权港币 50 万。
随后是 <b>2027 年 9–10 月主要 K2/Reception 申请潮</b>，针对直通车国际学校（ISF FY、VSA Y1、CDNIS EY1、SIS Prep、RCHK、HKA、Stamford、Carmel、Malvern）的 AY2028/29 入学。
<b>然后是 2028 年 9 月 P1 申请潮</b>，针对顶尖 DSS（SPCC、GTC、DGS）的 AY2029/30 入学。
考虑到普通话主导，<b>ISF FY 在 AY2028/29 是唯一最具优势的定位</b>。
</p>

<h2 style="{H2}">12 年总成本估算（数量级）</h2>
<table style="{TBL}">
  <tr>
    <th style="{TH}">学校</th>
    <th style="{TH}">年均 × 12</th>
    <th style="{TH}">资本费 / 债权</th>
    <th style="{TH}">总额估算（港币）</th>
    <th style="{TH}">是否在上限内</th>
  </tr>
  <tr><td style="{TD}"><b>GTC</b>（NSS→IBDP）</td><td style="{TD}">港币 70K × 12 = 港币 0.84M</td><td style="{TD}">无</td><td style="{TD}"><b>港币 0.84M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>SPCC</b>（DSE→IB 本地）</td><td style="{TD}">港币 130K × 12 = 港币 1.56M</td><td style="{TD}">无</td><td style="{TD}"><b>港币 1.56M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr><td style="{TD}"><b>VSA</b></td><td style="{TD}">港币 180K × 12 = 港币 2.16M</td><td style="{TD}">温和一次性</td><td style="{TD}"><b>约港币 2.2M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>RCHK</b>（无 INR）</td><td style="{TD}">港币 170K × 12 = 港币 2.04M</td><td style="{TD}">NCL 港币 50K</td><td style="{TD}"><b>约港币 2.1M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr><td style="{TD}"><b>RCHK + INR</b>（享优先）</td><td style="{TD}">港币 170K × 12 = 港币 2.04M</td><td style="{TD}">+港币 500K INR</td><td style="{TD}"><b>约港币 2.55M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>AIS HK</b></td><td style="{TD}">港币 200K × 12 = 港币 2.4M</td><td style="{TD}">港币 12K × 12 = 港币 0.144M</td><td style="{TD}"><b>约港币 2.55M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr><td style="{TD}"><b>ISF</b>（年度资本费）</td><td style="{TD}">港币 200K × 12 = 港币 2.4M</td><td style="{TD}">港币 40K × 12 = 港币 0.48M</td><td style="{TD}"><b>港币 2.88M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>HKA</b></td><td style="{TD}">港币 190K × 12 = 港币 2.28M</td><td style="{TD}">家庭债权港币 630K（部分可退；请核实）</td><td style="{TD}"><b>约港币 2.9M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ CDNIS</b>（债权路径）</td><td style="{TD}">港币 226K × 12 = 港币 2.7M</td><td style="{TD}">二级市场债权约港币 220 万</td><td style="{TD}"><b>约港币 4.9M</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">超出上限</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ Harrow HK</b></td><td style="{TD}">港币 185K × 12 = 港币 2.22M</td><td style="{TD}">Capital Certificate 约港币 330 万（可转售）</td><td style="{TD}"><b>约港币 5.5M</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">超出上限</span></td></tr>
  <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ YCIS</b></td><td style="{TD}">港币 210K × 12 = 港币 2.52M</td><td style="{TD}">债权约港币 200 万（可转售）</td><td style="{TD}"><b>约港币 4.5M+</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">超出上限</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ HKIS</b></td><td style="{TD}">港币 265K × 12 = 港币 3.18M</td><td style="{TD}">债权港币 300–500 万（不可转售）</td><td style="{TD}"><b>港币 600 万+</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">超出上限</span></td></tr>
  <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ GSIS</b>（英语流）</td><td style="{TD}">港币 170K × 12 = 港币 2.04M</td><td style="{TD}">Infrastructure Debenture 港币 600 万</td><td style="{TD}"><b>港币 800 万+</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">超出上限</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ CIS 直接申请</b></td><td style="{TD}">港币 235K × 12 = 港币 2.82M</td><td style="{TD}">CNR 港币 1500 万</td><td style="{TD}"><b>港币 1700 万+</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">超出上限</span></td></tr>
</table>
<p style="{MUTED};margin-top:6px;">数字为按当前费用估算的<i>数量级</i>；可退还债权部分可收回；未计算手足折扣。承诺前请向各校核实。</p>

<p style="margin:14px 0 6px 0;"><b>债权上限内的成本效益前沿</b>：</p>
<ul style="margin:0 0 0 18px;padding:0;">
  <li><b>GTC 总成本约港币 84 万</b> — 若可接受 TKO 通勤，每分 IB 的性价比无可匹敌</li>
  <li><b>SPCC 约港币 156 万</b> — 香港顶尖 IB 成绩，中等成本</li>
  <li><b>VSA 约港币 220 万</b> · <b>RCHK 约港币 210 万</b> — 双语 IB Continuum，中等成本</li>
  <li><b>ISF 约港币 288 万</b> — 高级成本，香港最佳普通话沉浸式教学</li>
  <li><b>AIS HK 约港币 255 万</b> — 在上限内，但适配度为第三梯队（STEM 上限 + 普通话稀释）</li>
</ul>

<h2 style="{H2}">下一步行动</h2>
<ol style="margin:6px 0 6px 18px;padding:0;">
  <li><b style="color:{C_DANGER};">紧急（未来 5 个月内）：</b>申请 CDNIS EY1（截止 2026-10-02）与 SIS HK Prep Years（截止 2026-09-30）。确认孩子的确切出生日期以核实年龄层匹配。</li>
  <li><b>决定方向</b>：直通车国际学校 K2（CDNIS / SIS） vs 2028 年的 P1 阶段集中申请（SPCC、GTC、DGS）</li>
  <li><b>未来 3 个月内参访</b>：ISF + SPCC + GTC + VSA</li>
  <li><b>购买 ESF 个人提名权港币 50 万</b>（若名单含 ESF 学校）— 香港最便宜的优先入学杠杆</li>
  <li><b>在家继续培养英语</b> — 至 K3 入学时争取约 50/50</li>
  <li><b>参访后重新评分</b>：在 <code>04-evaluation/shortlist.md</code> 中更新</li>
</ol>

<div style="margin-top:24px;padding:14px;background:{C_TBL_HDR};border-radius:8px;{MUTED}">
  完整资料库见
  <a style="{LINK}" href="https://github.com/astronvc/school-picker">github.com/astronvc/school-picker</a>。
  详细各校截止日见 <code>04-evaluation/application-windows.md</code>，
  AIS HK 深度评估见 <code>02-schools/american-international-school.md</code>。
  <br>
  由 tools/send_summary_email.py 生成 · {TODAY}
</div>

</div>
</body>
</html>
"""


# ---------- send ----------

def send_email(subject, html, password, lang_label):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8").encode()
    msg["From"] = SENDER
    msg["To"] = RECIPIENT
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER, password)
        server.send_message(msg)
    print(f"  Sent {lang_label} ({len(html):,} chars HTML) to {RECIPIENT}")


def main():
    if os.environ.get("DRY_RUN"):
        for fname, html in [("dry_run_en.html", build_en_html()),
                            ("dry_run_zh.html", build_zh_html())]:
            with open(fname, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"DRY_RUN: wrote {fname} ({len(html):,} chars).")
        print("Open in a browser to preview.")
        return

    password = os.environ.get("GMAIL_APP_PASSWORD") or CFG.get("GMAIL_APP_PASSWORD")
    if not password:
        sys.exit(
            "No GMAIL_APP_PASSWORD found.\n"
            "Set it in ~/.config/send_email.yml as:\n"
            "    GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx\n"
            "    GMAIL_SENDER=your.address@gmail.com\n"
            "    GMAIL_TO=recipient@gmail.com\n"
            "Or pass via env: GMAIL_APP_PASSWORD='xxxx xxxx xxxx xxxx' python3 tools/send_summary_email.py\n"
            "Get an app password at https://myaccount.google.com/apppasswords\n"
            "(2-Step Verification must be enabled on the Google account)."
        )
    password = password.replace(" ", "")

    print(f"Sending 2 emails from {SENDER} to {RECIPIENT}...")
    send_email(SUBJECT_EN, build_en_html(), password, "EN")
    send_email(SUBJECT_ZH, build_zh_html(), password, "ZH")
    print("Done.")


if __name__ == "__main__":
    main()
