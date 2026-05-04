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

This version (2026-05-04 v3) integrates VERIFIED primary-source data from
04-evaluation/application-windows-verified.md. Earlier framings of cohort
fit and ISF entry levels were corrected.
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

SUBJECT_EN = f"HK School Picker — Verified Summary v3 ({TODAY})"
SUBJECT_ZH = f"香港选校 — 核实数据总结 v3（{TODAY}）"

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

WRAP = (f"max-width:780px;margin:0 auto;padding:24px;background:{C_BG};"
        f"color:{C_TEXT};{FONT}line-height:1.55;font-size:14px;")

CARD = (f"background:{C_CARD};border:1px solid {C_BORDER};border-radius:8px;"
        "padding:18px 20px;margin:14px 0;")

URGENT_CARD = (f"background:#fef2f2;border:1px solid {C_DANGER};border-left:4px solid {C_DANGER};"
               "border-radius:8px;padding:18px 20px;margin:14px 0;")

FEEDER_CARD = (f"background:#f0fdf4;border:1px solid {C_BEST};border-left:4px solid {C_BEST};"
               "border-radius:8px;padding:18px 20px;margin:14px 0;")

H1 = (f"color:{C_PRIMARY};margin:0 0 6px 0;font-size:24px;font-weight:700;"
      f"letter-spacing:-0.01em;")

H2 = (f"color:{C_PRIMARY};margin:32px 0 12px 0;font-size:18px;font-weight:600;"
      f"border-bottom:2px solid {C_PRIMARY};padding-bottom:6px;")

H2_DANGER = (f"color:{C_DANGER};margin:32px 0 12px 0;font-size:18px;font-weight:700;"
             f"border-bottom:2px solid {C_DANGER};padding-bottom:6px;")

H2_BEST = (f"color:{C_BEST};margin:32px 0 12px 0;font-size:18px;font-weight:700;"
           f"border-bottom:2px solid {C_BEST};padding-bottom:6px;")

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


# ============================================================================
# ENGLISH content
# ============================================================================

def build_en_html():
    fld = {
        "curriculum": "Curriculum",
        "location": "Location",
        "fees": "Annual tuition (2025/26)",
        "capital": "Capital / debenture",
        "ib": "2025 IB outcome",
        "mandarin": "Mandarin",
        "entry": "Entry levels",
        "cohort": "Daughter's cohort (DOB mid-Sep 2023)",
        "app_window": "Application window",
        "apply": "Apply at",
        "feeder": "Feeder",
    }
    why_lbl, caveat_lbl = "Why", "Caveats"

    isf = school_card(
        PILL_BEST, "TIER A — top fit",
        "The ISF Academy",
        [
            (fld["curriculum"], "IB MYP + DP; <b>70% Mandarin / 30% English</b> Foundation Year through G4"),
            (fld["location"], "Cyberport, Pokfulam (HK Island, west)"),
            (fld["entry"], "<b>Foundation Year only</b> (no Pre-Reception — earlier email was wrong). FY = local K3 / Reception equivalent."),
            (fld["cohort"], "Sep–Dec dual-cohort flex: <b>FY AY2028/29</b> (apply ~Aug 1 – Sep 11, 2027) <b>OR FY AY2029/30</b> (apply ~Aug 2028)"),
            (fld["fees"], "FY–G5 HK$240,320 · G6–10 HK$279,210 · G11–12 HK$303,530 · App fee HK$1,000"),
            (fld["capital"], "<b>ACL HK$40K/yr</b> — within cap (12 yrs ≈ HK$480K). Capital Note ~HK$4.3M secondary market = above cap, but exempts ACL + admissions priority."),
            (fld["ib"], "Avg 38.6, 51% over 40, 1 perfect 45"),
            (fld["mandarin"], "<b>Deepest authentic Mandarin immersion in HK</b> — perfect linguistic fit"),
            (fld["feeder"], "<b>ISF Pre-School (Kennedy Town, 97 Belcher's St — NOT Pokfulam)</b>: HK$152,790 HD + HK$15K ACL. Feeder strength = WEAK unless Capital Note holder."),
            (fld["apply"], f'<a style="{LINK}" href="https://admissions.isf.edu.hk">admissions.isf.edu.hk</a> · Open Day 2026-08-29'),
        ],
        why_lbl,
        "Single best-aligned school in HK for a Mandarin-dominant girl. Bilingual + IB + Chinese-virtues ethos. Annual Capital Levy avoids the big-debenture trap entirely.",
        caveat_lbl,
        "Not absolute top STEM; Mandarin dilutes in upper years; FY intake competitive. ISF Pre-School only marginally helps (no formal priority).",
    )

    spcc = school_card(
        PILL_BEST, "TIER A — top fit",
        "St Paul's Co-educational College (SPCC) — Primary + Secondary",
        [
            (fld["curriculum"], "DSE + IB DP <b>parallel</b> from S5 (DSS dual-track)"),
            (fld["location"], "MacDonnell Road (Secondary, Mid-Levels) · Wong Chuk Hang (Primary)"),
            (fld["entry"], "<b>P1 only</b> (no K-stream). Through-train to Secondary."),
            (fld["cohort"], "<b>P1 AY2029/30</b> (born Sep 1, 2022 – Dec 31, 2023; daughter at back of cohort) OR P1 AY2030/31 (front of cohort)"),
            (fld["fees"], "P1–P2 ~HK$77,800 (DSE) · IB local ~HK$160K · IB non-local ~HK$201K"),
            (fld["capital"], "<b>None published</b> ✓ for primary. Verify with admissions@spcc.edu.hk."),
            (fld["ib"], "<b>Avg 42.1 — #1 in HK 2025</b>"),
            (fld["mandarin"], "English-medium with strong Putonghua-Chinese; substantial mainland-heritage cohort"),
            (fld["feeder"], "<b>Kindergarten Nomination Scheme (FD Scheme)</b>: ≤5% of P1 places open to ANY KG Head — <b>Tutor Time Dorset Head can nominate</b>. No additional cost. Worth asking Tutor Time directly."),
            (fld["app_window"], "<b>2028-09-01 to 2028-09-05 (4-day window!)</b> for AY2029/30 P1. AY2027/28 expected ~2026-09-01 to 2026-09-05."),
            (fld["apply"], f'<a style="{LINK}" href="https://www.spcc.edu.hk/admissions/local-admissions/primary/p1">spcc.edu.hk/admissions/local-admissions/primary/p1</a>'),
        ],
        why_lbl,
        "Top academic ceiling in HK at fraction of international cost. No debenture, mainland-heritage friendly, central. Kindergarten Nomination Scheme is a low-cost lever — Tutor Time Dorset Head can nominate.",
        caveat_lbl,
        "S1 ratio ~20:1; competitive at all entries. 4-day P1 window is unforgiving. Successful nomination requires Tutor Time agreement that daughter is exceptional.",
    )

    vsa = school_card(
        PILL_BEST, "TIER A — top fit",
        "Victoria Shanghai Academy (VSA)",
        [
            (fld["curriculum"], "IB Continuum (PYP, MYP, DP); bilingual English + Putonghua primary"),
            (fld["location"], "Shum Wan, Aberdeen (HK Island, south)"),
            (fld["entry"], "<b>Y1 only main entry</b> (5y8m by Aug = Dec 1 cutoff). Y7 secondary entry."),
            (fld["cohort"], "<b>Y1 AY2029/30</b> (born by Dec 2023 → daughter eligible). NOT eligible AY2028/29."),
            (fld["fees"], "Y1–Y5 PYP HK$181,200 · Y6 HK$200,700 · Y7–8 HK$203,700 · Y9–10 HK$205,400 · DP HK$255,600 · App fee HK$2,000"),
            (fld["capital"], "<b>Capital Levy HK$60K (one-off, partial refund)</b> ✓ within cap. Individual Debenture HK$3M = above cap (but skips Round 1)."),
            (fld["ib"], "Avg 37.6 (5 perfect scorers in 2025)"),
            (fld["mandarin"], "Strong bilingual model — among the best for HK families wanting authentic Putonghua"),
            (fld["feeder"], f'<b style="color:{C_BEST};">Victoria Kindergarten = STRONGEST verified feeder in HK</b>: ~170 graduates/yr → VSA out of ~150 places. Switch from Tutor Time NOW for K1 AY2026/27 (born 2023). VK fees ~HK$80–110K/yr. <b>This is the highest-leverage move available</b> for VSA admission.'),
            (fld["app_window"], "<b>~Sep 2027 – early Feb 2028</b> for Y1 AY2029/30. AY2027/28 deadline already passed (2026-02-05)."),
            (fld["apply"], f'<a style="{LINK}" href="https://admissions.vsa.edu.hk/application_index_v2.php">admissions.vsa.edu.hk</a>'),
        ],
        why_lbl,
        "Bilingual IB Continuum at moderate cost. Mainland-heritage friendly. Victoria Kindergarten feeder gives extraordinary admission edge.",
        caveat_lbl,
        "Aberdeen commute from Quarry Bay (verify). Y1 application is for AY2029/30 only — NOT 2028/29 as previously stated. To use VK feeder, must switch from Tutor Time NOW.",
    )

    gtc = school_card(
        PILL_INFO, "TIER A — strong",
        "G.T. (Ellen Yeung) College",
        [
            (fld["curriculum"], "Local NSS (DSE) + IB DP from senior years (DSS through-train)"),
            (fld["location"], "Tiu Keng Leng, Tseung Kwan O"),
            (fld["entry"], "<b>P1 only main entry</b> (also S5 IBDP entry option)"),
            (fld["cohort"], "<b>P1 AY2029/30</b> (born by Dec 31, 2023 → daughter eligible)"),
            (fld["fees"], "DSE P1 <b>HK$35,310</b> (cheapest in shortlist) · IBDP HK$88,550 · App fee HK$200"),
            (fld["capital"], "<b>None</b> ✓"),
            (fld["ib"], "<b>Avg 40.04, 56% over 40</b> — exceptional outcome at this fee point"),
            (fld["mandarin"], "EMI with strong Chinese; mainland-heritage friendly"),
            (fld["feeder"], "<b>None</b> — no kindergarten feeder. Direct P1 application only."),
            (fld["app_window"], "<b>~early May – early June 2028</b> for AY2029/30 P1. AY2027/28 expected May–June 2026 (open soon)."),
            (fld["apply"], f'<a style="{LINK}" href="https://admission.gtschool.hk">admission.gtschool.hk</a> · pri-tko@gtcollege.edu.hk'),
        ],
        why_lbl,
        "World-class IB outcomes at fraction of international cost. Gifted-pedagogy maps cleanly to anti-rote, research-leaning preference. No debenture.",
        caveat_lbl,
        "TKO commute from HK Island Eastern is real friction. Through-train means committing early. No KG feeder = no early-entry strategy.",
    )

    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>HK School Picker — Verified Summary v3</title></head>
<body style="margin:0;padding:0;background:{C_BG};">
<div style="{WRAP}">

<div style="{CARD}">
  <h1 style="{H1}">HK School Picker — Verified Summary <span style="font-weight:400;color:{C_MUTED};">v3</span></h1>
  <div style="{MUTED}">For: girl, DOB mid-Sep 2023 · HK passport · mainland heritage · Mandarin-dominant
  · debenture cap HK$1M · mainland-uni optional</div>
  <div style="{MUTED};margin-top:6px;">
    Source repo:
    <a style="{LINK}" href="https://github.com/astronvc/school-picker">github.com/astronvc/school-picker</a>
    · Generated {TODAY}
  </div>
  <div style="{MUTED};margin-top:6px;color:{C_DANGER};font-size:12px;">
    <b>v3 corrections from earlier emails</b>: ISF entry is FY (not Pre-Reception); SIS/CDNIS/VSA/Carmel/HKA/AIS dates verified from primary sources;
    feeder programs (Victoria Kindergarten, ESF Class A Debenture, SPCC Nomination Scheme) made explicit. See <code>04-evaluation/application-windows-verified.md</code> for full primary-source detail.
  </div>
</div>

<h2 style="{H2_DANGER}"><span style="{PILL_URGENT}">URGENT</span> &nbsp; Verified deadlines (next 18 months)</h2>
<div style="{URGENT_CARD}">
  <p style="margin:0 0 8px 0;">Verified from primary-source admission pages. Daughter (DOB mid-Sep 2023) is eligible at <b>multiple entry points and cohort years</b> — three feasible Y1/P1 entry years total: AY2028/29 (ESF), AY2029/30 (ISF/SPCC/VSA/GT), AY2030/31 (Aug-31 cutoff schools).</p>

  <p style="margin:14px 0 6px 0;"><b style="color:{C_DANGER};">Hard deadlines in next 5 months:</b></p>
  <table style="{TBL}">
    <tr>
      <th style="{TH};width:14%;">Deadline</th>
      <th style="{TH};width:14%;">School</th>
      <th style="{TH};width:30%;">Entry · Cohort</th>
      <th style="{TH}">Capital · Notes</th>
    </tr>
    <tr><td style="{TD}"><b style="color:{C_DANGER};">2026-09-30</b></td><td style="{TD}"><b>SIS HK</b></td><td style="{TD}">PY1 (age 3) · AY2027/28 — daughter prime cohort</td><td style="{TD}">Personal Debenture HK$200K ✓ · ACL HK$20K/yr ✓ · App fee HK$2,800</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_DANGER};">2026-10-02</b></td><td style="{TD}"><b>CDNIS</b></td><td style="{TD}">EY1 (age 3) · AY2027/28 — daughter at front of cohort</td><td style="{TD}">Reservation HK$80K ✓ · ACL HK$43K/yr ✓ (debenture HK$2.2M secondary above cap)</td></tr>
    <tr><td style="{TD}"><b style="color:{C_DANGER};">2026-10-10</b></td><td style="{TD}"><b>Harrow HK</b></td><td style="{TD}">Nursery · AY2027/28</td><td style="{TD}">App fee HK$1,500. Note Capital Cert HK$3.3M = above cap (still apply if want option)</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_DANGER};">2026-11-30</b></td><td style="{TD}"><b>CDNIS</b></td><td style="{TD}">Nursery (age 2) — ALT path · AY2027/28</td><td style="{TD}">Daughter on older edge; Nursery has no capital levy/debenture requirement</td></tr>
  </table>

  <p style="margin:14px 0 6px 0;"><b>Rolling — apply NOW (no fixed deadline):</b></p>
  <table style="{TBL}">
    <tr>
      <th style="{TH};width:14%;">School</th>
      <th style="{TH};width:30%;">Entry · Cohort</th>
      <th style="{TH}">Capital · Notes</th>
    </tr>
    <tr><td style="{TD}"><b>AIS HK</b></td><td style="{TD}">EC1 (age 3 HD) · AY2027/28</td><td style="{TD}"><b>NO debenture</b> · ACL HK$12K/yr (cheapest int'l) ✓ · Reservation HK$25K · First-come-first-served</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>HKA</b></td><td style="{TD}">Pre-K1 (age 3) · AY2026/27</td><td style="{TD}">Family Debenture HK$630K ✓ OR ACL HK$32K/yr ✓ — but <b>HKA stops issuing new debentures Jan 1, 2026</b>; secondary market only after</td></tr>
    <tr><td style="{TD}"><b>Carmel</b></td><td style="{TD}">Nursery · AY2026/27 (Oct 31 cutoff — daughter eligible)</td><td style="{TD}"><b>NO debenture, NO ACL</b> at Elementary ✓ · Open to non-Jewish (Elsa High explicit)</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>NAIS HK</b></td><td style="{TD}">Nursery · AY2027/28 (apply by Dec 2026 recommended)</td><td style="{TD}">CEF HK$100K + ACL HK$35K/yr ✓ within cap</td></tr>
    <tr><td style="{TD}"><b>Malvern Pre-School</b></td><td style="{TD}">Pre-Nursery (age 2–3) · AY2026/27</td><td style="{TD}">Within cap. Implied (not published) priority into Malvern College Prep 1.</td></tr>
  </table>

  <p style="margin:14px 0 6px 0;"><b>2027 (apply ~12–16 months out):</b></p>
  <table style="{TBL}">
    <tr>
      <th style="{TH};width:18%;">Window</th>
      <th style="{TH};width:14%;">School</th>
      <th style="{TH}">Entry · Cohort · Notes</th>
    </tr>
    <tr><td style="{TD}"><b>~Aug 1 – Sep 11, 2027</b></td><td style="{TD}"><b>ISF Academy</b></td><td style="{TD}">Foundation Year · AY2028/29 (daughter back-of-cohort under Sep–Dec dual flex)</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>2027-09-01 to 2027-09-30</b></td><td style="{TD}"><b>ESF</b></td><td style="{TD}">Y1 Reception · AY2028/29 — <b>daughter's prime ESF window</b>. Buy <b>INR HK$500K BEFORE 2027-09-01</b> for priority interview. Standard ESF + RCHK (HK$400K INR) + Discovery College (HK$400K INR) all use this window.</td></tr>
    <tr><td style="{TD}"><b>~Sep 2027 – early Feb 2028</b></td><td style="{TD}"><b>VSA</b></td><td style="{TD}">Y1 Reception · AY2029/30 (daughter eligible per Dec 1 cutoff)</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>~Sep 2027 – Oct 2027</b></td><td style="{TD}"><b>CIS</b></td><td style="{TD}">Reception · AY2028/29 (NOT AY2027/28 per Aug 31 cutoff). Above-cap nomination economics — see Above Cap section.</td></tr>
  </table>

  <p style="margin:14px 0 6px 0;"><b>2028 (apply ~24 months out):</b></p>
  <table style="{TBL}">
    <tr>
      <th style="{TH};width:24%;">Window</th>
      <th style="{TH};width:14%;">School</th>
      <th style="{TH}">Entry · Cohort · Notes</th>
    </tr>
    <tr><td style="{TD}"><b>~early May – early Jun 2028</b></td><td style="{TD}"><b>GTC</b></td><td style="{TD}">P1 · AY2029/30 (cheapest in shortlist at HK$35K/yr)</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>~mid-Aug 2028 (10-day window)</b></td><td style="{TD}"><b>DGJS → DGS</b></td><td style="{TD}">P1 · AY2029/30 (girls only — fits daughter). DGJS is exclusive feeder for DGS Secondary.</td></tr>
    <tr><td style="{TD}"><b>2028-09-01 to 2028-09-05 (4-day window!)</b></td><td style="{TD}"><b>SPCC Primary</b></td><td style="{TD}">P1 · AY2029/30. Apply via <b>Kindergarten Nomination Scheme</b> through Tutor Time Dorset Head if SPCC agrees daughter exceptional.</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>~Aug 2028</b></td><td style="{TD}"><b>ISF Academy</b></td><td style="{TD}">FY · AY2029/30 (alternative to AY2028/29 under Sep–Dec dual flex)</td></tr>
    <tr><td style="{TD}"><b>2028-09-01 to 2028-09-30</b></td><td style="{TD}"><b>ESF</b></td><td style="{TD}">Y1 · AY2029/30 (alternative to AY2028/29)</td></tr>
  </table>
</div>

<h2 style="{H2_BEST}">Feeder programs that materially help</h2>
<div style="{FEEDER_CARD}">
  <p style="margin:0 0 8px 0;">If you want to maximize admission odds at a specific top school, these feeders are the highest-leverage moves available. <b>Some require action this year.</b></p>

  <table style="{TBL}">
    <tr>
      <th style="{TH};width:24%;">Feeder → Main school</th>
      <th style="{TH};width:14%;">Strength</th>
      <th style="{TH};width:18%;">Cost (within HK$1M cap?)</th>
      <th style="{TH}">Action timing</th>
    </tr>
    <tr><td style="{TD}"><b>Victoria Kindergarten → VSA</b></td><td style="{TD}"><span style="{PILL_BEST}">STRONGEST</span></td><td style="{TD}">VK fees ~HK$80–110K/yr ✓</td><td style="{TD}"><b>Switch from Tutor Time NOW</b> for K1 AY2026/27 (born 2023). ~170 VK graduates/yr → VSA Y1 (out of ~150 VSA places). This is the single most effective feeder in HK for VSA.</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>SPCC Kindergarten Nomination Scheme</b></td><td style="{TD}"><span style="{PILL_INFO}">OPEN</span></td><td style="{TD}">No additional cost ✓</td><td style="{TD}">Open to ANY Kindergarten Head — <b>Tutor Time Dorset Head can nominate daughter</b>. Submit nomination form during 4-day P1 window (Sep 2028 for AY2029/30). Ask Tutor Time Dorset directly whether they will nominate.</td></tr>
    <tr><td style="{TD}"><b>ESF Class A Debenture (K1) → INR (Y1)</b></td><td style="{TD}"><span style="{PILL_INFO}">STRONG</span></td><td style="{TD}">HK$500K ✓</td><td style="{TD}"><b>K1 AY2026/27 closed Sep 2025</b>; late waitlist only — daughter's K1 window is closed. <b>Skip to INR HK$500K for Y1 AY2028/29</b> — apply Sep 2027.</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>DGJS → DGS</b> (girls only)</td><td style="{TD}"><span style="{PILL_BEST}">EXCLUSIVE</span></td><td style="{TD}">DGJS HK$79K/yr ✓ · No debenture</td><td style="{TD}">DGJS is DGS Secondary's exclusive feeder. Apply DGJS P1 mid-Aug 2028 for AY2029/30.</td></tr>
    <tr><td style="{TD}"><b>CDNIS Nursery → EY1</b></td><td style="{TD}"><span style="{PILL_INFO}">INTERNAL</span></td><td style="{TD}">Nursery: no capital req ✓ · EY1+: ACL HK$43K/yr ✓</td><td style="{TD}">Apply Nursery AY2027/28 by 2026-11-30 for internal continuity priority into EY1.</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>Carmel ELC → Carmel Elementary → Elsa High</b></td><td style="{TD}"><span style="{PILL_INFO}">INTERNAL</span></td><td style="{TD}">No debenture, no ACL at Elementary ✓</td><td style="{TD}">Direct progression. Apply Nursery AY2026/27 (rolling, Oct 31 cutoff). Open to non-Jewish.</td></tr>
    <tr><td style="{TD}"><b>HKA Pre-K → through-train</b></td><td style="{TD}"><span style="{PILL_INFO}">INTERNAL</span></td><td style="{TD}">Family Debenture HK$630K ✓ OR ACL HK$32K/yr ✓</td><td style="{TD}">Apply Pre-K1 AY2026/27 (rolling). Buy debenture before Jan 1, 2026 (deadline already missed — secondary only).</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>Malvern Pre-School → Malvern College</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">IMPLIED</span></td><td style="{TD}">Within cap (verify exact)</td><td style="{TD}">Apply Pre-Nursery AY2026/27 (rolling). Implied priority but not formally published.</td></tr>
    <tr><td style="{TD}"><b>ISF Pre-School → ISF Academy</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">WEAK</span></td><td style="{TD}">HK$15K/yr ACL ✓ (HK$152K tuition)</td><td style="{TD}">No formal priority unless Capital Note holder. Pre-School is in <b>Kennedy Town</b> (97 Belcher's St — earlier "Pokfulam" was wrong).</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>DPS → DBS</b></td><td style="{TD}"><span style="{PILL_OUT}">ENDED 2010</span></td><td style="{TD}">n/a</td><td style="{TD}">Not relevant for daughter (DBS is boys-only anyway). Formal feeder relationship ended 2010.</td></tr>
  </table>
</div>

<h2 style="{H2}">Family snapshot</h2>
<table style="{TBL}">
  <tr><td style="{TH}">Child</td><td style="{TD}">Girl, <b>DOB mid-Sep 2023</b>, currently at Tutor Time Dorset (Quarry Bay area, ~50/50 EN/CN at school)</td></tr>
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

<h2 style="{H2}">Tier A — top-fit candidates</h2>
{isf}
{spcc}
{vsa}
{gtc}

<h2 style="{H2}">American International School (AIS HK) — independent evaluation</h2>
<div style="{CARD}">
  <div style="margin-bottom:8px;"><span style="{PILL_CAVEAT}">TIER C — backup / fit-dependent</span></div>
  <h3 style="{H3}">American International School Hong Kong (125 Waterloo Road, Kowloon Tong)</h3>
  <p style="margin:6px 0 10px 0;{MUTED}">Independent verdict, past the "not academic" reputation. Full eval at <code>02-schools/american-international-school.md</code>. Capital structure verified: NO debenture.</p>
  <table style="{TBL}">
    <tr><td style="{TH};width:28%;">Curriculum</td><td style="{TD}">US standards-based + AP (incl. AP Capstone — Seminar + Research). WASC-accredited; founded 1986.</td></tr>
    <tr><td style="{TH}">Entry levels</td><td style="{TD}">EC1 (age 3 HD), EC2 (age 4 FD), G1 Junior (age 5), G1+, ... G12</td></tr>
    <tr><td style="{TH}">Daughter's cohort</td><td style="{TD}"><b>EC1 AY2027/28</b> (rolling — apply now). Also eligible EC2 AY2028/29, G1 Junior AY2029/30, G1 AY2030/31.</td></tr>
    <tr><td style="{TH}">Annual tuition</td><td style="{TD}">EC HD HK$97K · EC FD–G1 Junior HK$146.8K · G1–4 HK$152.8K · G5–8 HK$164.4K · G9–12 HK$180.4K</td></tr>
    <tr><td style="{TH}">Capital / debenture</td><td style="{TD}"><b>NO debenture</b> ✓✓ — ACL HK$12K/yr (1st child) — among the lowest in HK · Reservation HK$25K · App fee HK$1,500</td></tr>
    <tr><td style="{TH}">Application</td><td style="{TD}">Rolling first-come — easy entry, low friction. Verified at <a style="{LINK}" href="https://ais.openapply.com/">ais.openapply.com</a></td></tr>
  </table>
  <p style="margin:10px 0 4px 0;"><b style="color:{C_BEST};">"Not academic" verdict —</b>
  partially accurate but mischaracterized. AIS is not weak, but not top-tier either.
  AP results sit ~10pp behind HKIS (85% scoring 3+ in 2022 vs HKIS 95% scoring 3+ in 2024–25);
  no documented MIT / Stanford / Princeton / CMU placements 2023–25
  while HKIS, ISF, ICS, CIS all show such. Documented placements: UC Berkeley, UCLA, NYU, Cornell, Northwestern, BU, occasional Columbia / Oxford.</p>
  <p style="margin:8px 0 4px 0;"><b style="color:{C_DANGER};">Decisive against for our family:</b><br>
  (1) <b>STEM ceiling is the load-bearing gap.</b> AIS publishes AP Calc BC + AP Physics 2 (algebra-based) as ceiling.
  <b>No AP Physics C, no Multivariable, no Linear Algebra, no Differential Equations.</b>
  HKIS publishes all of these.<br>
  (2) <b>Mandarin treated as specialist subject</b> (3–5 hr/week, ability-grouped) — <i>not</i> a content medium.
  Will plateau a Mandarin-dominant child rather than compound the asset.</p>
  <p style="margin:8px 0 0 0;"><b style="color:{C_BEST};">Decisive for (case for keeping on list):</b>
  no debenture (HK$12K/yr capital levy), rolling first-come admissions, AP Capstone is a real research program, secular co-ed, Kowloon Tong MTR-served.
  <b>Use as low-friction backup</b> while applying to Tier A.</p>
</div>

<h2 style="{H2}">Tier B / C (compact)</h2>
<table style="{TBL}">
  <tr>
    <th style="{TH}">Tier</th>
    <th style="{TH}">School</th>
    <th style="{TH}">Curriculum · Location</th>
    <th style="{TH}">Annual fee · Capital (verified)</th>
    <th style="{TH}">Daughter's cohort</th>
  </tr>
  <tr><td style="{TD}">B</td><td style="{TD}">Singapore Intl School (SIS HK)</td><td style="{TD}">Singapore + IB · Aberdeen</td><td style="{TD}">PY HK$103K · Pers Debenture HK$200K ✓</td><td style="{TD}"><b>PY1 AY2027/28</b> (open NOW)</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">B</td><td style="{TD}">CDNIS</td><td style="{TD}">IB Continuum · Aberdeen</td><td style="{TD}">EY1 HK$161K · ACL HK$43K/yr ✓</td><td style="{TD}"><b>EY1 AY2027/28</b> (deadline Oct 2)</td></tr>
  <tr><td style="{TD}">B</td><td style="{TD}">PLKCKY</td><td style="{TD}">IB · Sham Shui Po</td><td style="{TD}">Verify with school · ✓</td><td style="{TD}">P1 ~AY2029/30</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">B</td><td style="{TD}">St Stephen's College (SSCPS/SSC)</td><td style="{TD}">IB or DSE · Stanley · boarding option</td><td style="{TD}">SSCPS HK$94K · ✓</td><td style="{TD}">G1 AY2029/30 (apply ~Jun 2028)</td></tr>
  <tr><td style="{TD}">B</td><td style="{TD}">DGJS → DGS (girls)</td><td style="{TD}">DSE + A-Level · Jordan</td><td style="{TD}">DGJS HK$79K · ✓</td><td style="{TD}"><b>P1 AY2029/30</b> (apply mid-Aug 2028)</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">C</td><td style="{TD}">AIS HK (American)</td><td style="{TD}">US + AP + AP Capstone · Kowloon Tong</td><td style="{TD}">~HK$150K · ACL HK$12K/yr ✓ · NO debenture</td><td style="{TD}">EC1 AY2027/28 (rolling)</td></tr>
  <tr><td style="{TD}">C</td><td style="{TD}">Malvern College HK</td><td style="{TD}">IB Continuum · Tai Po</td><td style="{TD}">Prep HK$199K · ACL HK$42K/yr ✓ · INR price NA</td><td style="{TD}">Prep 1 AY2030/31 (or via Pre-School AY2026/27)</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">C</td><td style="{TD}">HKA (Hong Kong Academy)</td><td style="{TD}">IB Continuum · Sai Kung</td><td style="{TD}">Pre-K HK$119K; K-G5 HK$229K · Family Deb HK$630K ✓ or ACL HK$32K/yr ✓</td><td style="{TD}">Pre-K1 AY2026/27 (rolling)</td></tr>
  <tr><td style="{TD}">C</td><td style="{TD}">ESF RCHK</td><td style="{TD}">IB Continuum · Ma On Shan</td><td style="{TD}">Y1 HK$154K · INR HK$400K ✓ + NCL HK$38K + Building Levy HK$50K</td><td style="{TD}"><b>Y1 AY2028/29</b> (apply Sep 2027)</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">C</td><td style="{TD}">ESF Discovery College</td><td style="{TD}">IB Continuum · Discovery Bay</td><td style="{TD}">Y1 HK$170K · INR HK$400K ✓ + Building Levy HK$8K/yr</td><td style="{TD}"><b>Y1 AY2028/29</b> (apply Sep 2027)</td></tr>
  <tr><td style="{TD}">C</td><td style="{TD}">Carmel School (Elsa High)</td><td style="{TD}">IB Continuum · Mid-Levels/SKW</td><td style="{TD}">Nursery HK$114K · K-G5 HK$203K · NO debenture, NO ACL ✓</td><td style="{TD}">Nursery AY2026/27 (rolling, Oct 31 cutoff)</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">C</td><td style="{TD}">Stamford American (SAIS)</td><td style="{TD}">IB DP · Ho Man Tin / WKL HS</td><td style="{TD}">Pre-Primary HK$220K · CapLevy HK$150K one-off ✓ OR Debenture HK$500K ✓</td><td style="{TD}">Pre-Primary AY2029/30 (NO K-stage; daughter must wait)</td></tr>
  <tr><td style="{TD}">C</td><td style="{TD}">AISHK (Australian)</td><td style="{TD}">HSC or IB · Kowloon Tong · Jan–Dec calendar</td><td style="{TD}">Reception HK$156K · Debenture HK$120K ✓</td><td style="{TD}">Reception ~Jan 2028 entry</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">C</td><td style="{TD}">NAIS HK</td><td style="{TD}">IB DP · Lam Tin / Kwun Tong</td><td style="{TD}">Nursery onwards · CEF HK$100K + ACL HK$35K/yr ✓</td><td style="{TD}">Nursery AY2027/28 (rolling)</td></tr>
  <tr><td style="{TD}">C</td><td style="{TD}">Kellett School</td><td style="{TD}">UK · Pok Fu Lam / Kowloon Bay</td><td style="{TD}">ACL HK$40K/yr ✓ — debentures HK$1M+ above cap</td><td style="{TD}">Reception AY2028/29 — currently FULL waitlist</td></tr>
</table>

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
    <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ CIS</b></td><td style="{TD}">CNR HK$15M direct · HK$1.1–1.5M secondary market</td><td style="{TD}">Corporate Nomination Right gives priority application slot at Reception / S1</td><td style="{TD}">General-pool acceptance ~5–8%. Daughter cohort = Reception AY2028/29 (NOT 2027/28 per Aug 31 cutoff).</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ Harrow HK</b></td><td style="{TD}">Capital Certificate ~HK$3.3M (fully resellable on secondary market)</td><td style="{TD}">Priority application slot</td><td style="{TD}">Tuen Mun location reduces demand somewhat. Nursery AY2027/28 deadline 2026-10-10.</td></tr>
    <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ HKIS</b></td><td style="{TD}">Family Debenture HK$3M / Corporate HK$5M (<b>no resale</b>; par refund after 15 years)</td><td style="{TD}">Priority application slot</td><td style="{TD}">~3–5% general-pool acceptance. R1 AY2028/29 (rolling).</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ GSIS</b> (English stream)</td><td style="{TD}">Standard Debenture HK$500K (within cap!) OR Infrastructure Debenture HK$6M</td><td style="{TD}">Standard Debenture qualifies; Infrastructure gets "First Admissions Priority"</td><td style="{TD}">Y01 AY2030/31 only for daughter (highly selective).</td></tr>
    <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ YCIS</b></td><td style="{TD}">Debenture from HK$2M (resellable)</td><td style="{TD}">Priority application slot</td><td style="{TD}">Less prestige-driven than CIS/HKIS — non-debenture chance moderate.</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ CDNIS</b> (debenture path)</td><td style="{TD}">Secondary-market only ~HK$2.2M (school not issuing new)</td><td style="{TD}">Priority + ACL exemption</td><td style="{TD}">CDNIS general pool: HK$80K reservation + HK$43K/yr ACL within cap. Debenture optional.</td></tr>
  </table>
  <p style="{MUTED};margin-top:8px;"><b>Decisive 2026/27 factor:</b> EDB 70% non-local quota tightening (see Insight #4) reduces HK-passport general-pool chance at every premier international school regardless of capital.</p>
</div>

<h2 style="{H2}">Key insights — what the research actually says</h2>
<table style="{TBL}">
  <tr>
    <th style="{TH};width:6%;">#</th>
    <th style="{TH}">Insight</th>
  </tr>
  <tr>
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">1</td>
    <td style="{TD}"><b>2026 evidence sharply validates anti-rote bias.</b> METR (AI task-horizon doubling every ~7 mo) + Brynjolfsson "Canaries" study (13% relative employment decline for 22–25 yos in AI-exposed jobs) confirm: optimizing for "rank #1 on the standardised exam" optimizes for the skill being commoditized in real time.</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">2</td>
    <td style="{TD}"><b>Curriculum hierarchy:</b> A-Level + Further Maths + EPQ ≈ IB DP (strong school) ≈ AP Capstone (only HKIS / AIS HK in HK) > dual-track DSE+IB > pure DSE.</td>
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
    <td style="{TD}"><b>Mandarin-native is an asset.</b> Schools that compound it: ISF (70/30), CIS (50/50), VSA, CDNIS bilingual track, YCIS, SIS, SPCC. AIS HK does NOT compound (Mandarin = 3–5 hr/wk specialist).</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">6</td>
    <td style="{TD}"><b>Three feasible Y1 entry years for daughter:</b> AY2028/29 (ESF, calendar-year cutoff), AY2029/30 (ISF/SPCC/VSA/GT, Sep–Dec dual flex), AY2030/31 (Aug-31 cutoff schools). The "right" answer depends on which school AND whether you want her to be among the youngest or oldest in cohort.</td>
  </tr>
</table>

<h2 style="{H2}">Action timeline (girl, DOB mid-Sep 2023)</h2>
<table style="{TBL}">
  <tr>
    <th style="{TH};width:14%;">Year</th>
    <th style="{TH};width:10%;">Age</th>
    <th style="{TH}">Action</th>
  </tr>
  <tr>
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2026 (now)</td>
    <td style="{TD}">2.5–3</td>
    <td style="{TD}">
      <b style="color:{C_DANGER};">URGENT (next 5 mo):</b> Apply <b>SIS PY1 (Sep 30)</b>, <b>CDNIS EY1 (Oct 2)</b>, <b>Harrow Nursery (Oct 10)</b>, <b>CDNIS Nursery (Nov 30)</b>.
      <b>Rolling apply NOW</b>: AIS HK EC1, NAIS Nursery, HKA Pre-K, Carmel Nursery, Malvern Pre-N.
      <b>Strategic decision</b>: switch from Tutor Time to <b>Victoria Kindergarten K1 AY2026/27</b> (born 2023 cohort) for STRONGEST feeder to VSA?
      <b>Visit</b> ISF + SPCC + VSA + GTC + AIS HK in next 3 months.
    </td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2027</td>
    <td style="{TD}">3–4</td>
    <td style="{TD}">
      <b>Aug 1 – Sep 11</b>: Apply ISF FY for AY2028/29.
      <b>Sep 1 – Sep 30</b>: Apply ESF Y1 + INR HK$500K (purchase BEFORE Sep 1) for AY2028/29; also RCHK + Discovery College Y1 (HK$400K INR each).
      <b>Sep – early Feb 2028</b>: Apply VSA Y1 for AY2029/30.
      <b>Sep – Oct</b>: Apply CIS Reception for AY2028/29 (above debenture cap caveat).
    </td>
  </tr>
  <tr>
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2028</td>
    <td style="{TD}">4–5</td>
    <td style="{TD}">
      <b>~early May – early Jun</b>: Apply GTC P1 for AY2029/30.
      <b>~mid-Aug (10-day window)</b>: Apply DGJS P1 for AY2029/30.
      <b>Sep 1 – Sep 5 (4-day window!)</b>: Apply SPCC Primary P1 for AY2029/30 — submit Tutor Time Dorset Head's nomination if approved.
      <b>~Aug</b>: Apply ISF FY AY2029/30 alternative.
      <b>Sep 1 – Sep 30</b>: Apply ESF Y1 AY2029/30 alternative.
    </td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2029</td>
    <td style="{TD}">5–6</td>
    <td style="{TD}">P1/Y1 entry at chosen school for AY2029/30 (most schools). Notifications spring 2029.</td>
  </tr>
  <tr>
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2030</td>
    <td style="{TD}">6–7</td>
    <td style="{TD}">P1/Y1 entry at AY2030/31 schools (CDNIS Prep, Malvern Prep 1, CIS, Harrow, etc.) — last common entry year for Aug-31 cutoff schools.</td>
  </tr>
</table>

<h2 style="{H2}">Estimated 12-year cost (rough order of magnitude)</h2>
<table style="{TBL}">
  <tr>
    <th style="{TH}">School</th>
    <th style="{TH}">Annual avg × 12</th>
    <th style="{TH}">Capital / debenture</th>
    <th style="{TH}">Total est. (HK$)</th>
    <th style="{TH}">Within cap?</th>
  </tr>
  <tr><td style="{TD}"><b>GTC</b> (DSE→IBDP)</td><td style="{TD}">HK$70K × 12 = HK$0.84M</td><td style="{TD}">None</td><td style="{TD}"><b>HK$0.84M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>SPCC</b> (DSE→IB local)</td><td style="{TD}">HK$130K × 12 = HK$1.56M</td><td style="{TD}">None</td><td style="{TD}"><b>HK$1.56M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr><td style="{TD}"><b>VSA</b> (no debenture)</td><td style="{TD}">HK$200K × 12 = HK$2.4M</td><td style="{TD}">HK$60K Capital Levy</td><td style="{TD}"><b>~HK$2.5M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>RCHK</b> (no INR)</td><td style="{TD}">HK$170K × 12 = HK$2.04M</td><td style="{TD}">HK$50K Building Levy + HK$38K NCL</td><td style="{TD}"><b>~HK$2.13M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr><td style="{TD}"><b>RCHK + INR</b> (priority)</td><td style="{TD}">HK$170K × 12 = HK$2.04M</td><td style="{TD}">+HK$400K INR</td><td style="{TD}"><b>~HK$2.5M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>AIS HK</b></td><td style="{TD}">HK$160K × 12 = HK$1.92M</td><td style="{TD}">HK$12K × 12 = HK$0.144M</td><td style="{TD}"><b>~HK$2.06M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr><td style="{TD}"><b>HKA</b> (Family Debenture)</td><td style="{TD}">HK$210K × 12 = HK$2.52M</td><td style="{TD}">HK$630K (refundable; verify)</td><td style="{TD}"><b>~HK$3.15M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>SIS HK</b></td><td style="{TD}">HK$190K × 12 = HK$2.28M</td><td style="{TD}">Personal Debenture HK$200K + Entry HK$13K</td><td style="{TD}"><b>~HK$2.5M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr><td style="{TD}"><b>CDNIS</b> (no debenture)</td><td style="{TD}">HK$220K × 12 = HK$2.64M</td><td style="{TD}">HK$80K Reservation + HK$12.5K Entry + HK$43K × 12 ACL = HK$609K</td><td style="{TD}"><b>~HK$3.25M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>ISF</b> (Annual ACL)</td><td style="{TD}">HK$270K × 12 = HK$3.24M</td><td style="{TD}">HK$40K × 12 = HK$0.48M</td><td style="{TD}"><b>HK$3.72M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr><td style="{TD}"><b>Carmel</b> (Elementary→Elsa)</td><td style="{TD}">HK$190K × 12 = HK$2.28M</td><td style="{TD}">HK$18.5K/yr ACL at G6+ only ≈ HK$130K</td><td style="{TD}"><b>~HK$2.4M</b></td><td style="{TD}"><span style="{PILL_BEST}">YES</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ HKIS</b></td><td style="{TD}">HK$265K × 12 = HK$3.18M</td><td style="{TD}">HK$3–5M debenture (no resale)</td><td style="{TD}"><b>HK$6M+</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">OVER CAP</span></td></tr>
  <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ CIS direct</b></td><td style="{TD}">HK$235K × 12 = HK$2.82M</td><td style="{TD}">HK$15M CNR</td><td style="{TD}"><b>HK$17M+</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">OVER CAP</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ Harrow HK</b></td><td style="{TD}">HK$185K × 12 = HK$2.22M</td><td style="{TD}">Capital Cert ~HK$3.3M (resellable)</td><td style="{TD}"><b>~HK$5.5M</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">OVER CAP</span></td></tr>
</table>
<p style="{MUTED};margin-top:6px;">Order-of-magnitude using current fee snapshots; refundable debentures partially recoverable; sibling discounts not applied. Verify with each school before committing.</p>

<p style="margin:14px 0 6px 0;"><b>Cost-efficient frontier within debenture cap</b>:</p>
<ul style="margin:0 0 0 18px;padding:0;">
  <li><b>GTC ~HK$0.84M</b> — hardest to beat on $/IB-point if TKO commute works</li>
  <li><b>SPCC ~HK$1.56M</b> — top IB outcomes in HK at moderate cost</li>
  <li><b>AIS HK ~HK$2.06M</b> — within cap but Tier C on fit (STEM ceiling + Mandarin dilution)</li>
  <li><b>RCHK ~HK$2.13M / +INR ~HK$2.5M</b> · <b>Carmel ~HK$2.4M</b> · <b>SIS HK ~HK$2.5M</b> · <b>VSA ~HK$2.5M</b> — bilingual IB, mid-cost</li>
  <li><b>HKA ~HK$3.15M</b> · <b>CDNIS ~HK$3.25M</b> · <b>ISF ~HK$3.72M</b> — premium tier within cap</li>
</ul>

<h2 style="{H2}">Next steps</h2>
<ol style="margin:6px 0 6px 18px;padding:0;">
  <li><b style="color:{C_DANGER};">URGENT (next 4 mo):</b> Submit applications to SIS PY1 (Sep 30), CDNIS EY1 (Oct 2), Harrow Nursery (Oct 10), CDNIS Nursery (Nov 30). Plus rolling: AIS HK, NAIS, HKA, Carmel, Malvern Pre-N.</li>
  <li><b>Strategic decision NOW</b>: switch from Tutor Time to Victoria Kindergarten K1 AY2026/27 if VSA is a top target (strongest feeder in HK).</li>
  <li><b>Ask Tutor Time Dorset Head</b> whether they will nominate daughter for SPCC Kindergarten Nomination Scheme (≤5% of P1 places).</li>
  <li><b>Visit</b> ISF + SPCC + VSA + GTC + AIS HK in next 3 months.</li>
  <li><b>Sep 2027</b>: Buy ESF Individual Nomination Right HK$500K BEFORE Sep 1; apply ESF Y1 + RCHK + Discovery College for AY2028/29; apply ISF FY for AY2028/29; apply VSA Y1 for AY2029/30.</li>
  <li><b>Sep 2028</b>: Apply SPCC P1, GTC P1, DGJS P1, ISF FY (AY2029/30), ESF Y1 (AY2029/30) for AY2029/30.</li>
  <li><b>Continue English exposure at home</b> — aim ~50/50 by K2.</li>
</ol>

<div style="margin-top:24px;padding:14px;background:{C_TBL_HDR};border-radius:8px;{MUTED}">
  Full knowledge base lives at
  <a style="{LINK}" href="https://github.com/astronvc/school-picker">github.com/astronvc/school-picker</a>.
  Verified per-school detail in <code>04-evaluation/application-windows-verified.md</code> (1,233 lines, primary-source pass).
  AIS HK deep eval in <code>02-schools/american-international-school.md</code>.
  <br>
  Generated by tools/send_summary_email.py · {TODAY}
</div>

</div>
</body>
</html>
"""


# ============================================================================
# 中文 (Mandarin / Simplified Chinese) content
# ============================================================================

def build_zh_html():
    fld = {
        "curriculum": "课程",
        "location": "位置",
        "fees": "年学费 (2025/26)",
        "capital": "资本费 / 债权",
        "ib": "2025 IB 成绩",
        "mandarin": "普通话项目",
        "entry": "入学级别",
        "cohort": "孩子年龄层（生于 2023 年 9 月中）",
        "app_window": "申请窗口",
        "apply": "申请链接",
        "feeder": "feeder（衔接）",
    }
    why_lbl, caveat_lbl = "优势", "注意事项"

    isf = school_card(
        PILL_BEST, "第一梯队 — 最佳匹配",
        "弘立书院 The ISF Academy",
        [
            (fld["curriculum"], "IB MYP + DP；Foundation Year 至 G4 阶段 <b>70%普通话 / 30%英语</b>"),
            (fld["location"], "数码港，薄扶林（港岛西）"),
            (fld["entry"], "<b>仅 Foundation Year 入学</b>（没有 Pre-Reception — 之前邮件有误）。FY = 本地 K3 / Reception 等同。"),
            (fld["cohort"], "9–12 月双年级灵活：<b>FY AY2028/29</b>（约 2027 年 8 月 1 日 – 9 月 11 日申请）<b>或 FY AY2029/30</b>（约 2028 年 8 月申请）"),
            (fld["fees"], "FY–G5 港币 240,320 · G6–10 港币 279,210 · G11–12 港币 303,530 · 申请费港币 1,000"),
            (fld["capital"], "<b>ACL 港币 40K/年</b> — 在上限内（12 年约 港币 480K）。Capital Note 二级市场约港币 430 万 = 超出上限，但免 ACL + 优先录取。"),
            (fld["ib"], "平均 38.6，51% 超 40 分，1 人满分 45"),
            (fld["mandarin"], "<b>香港最深入的真正普通话沉浸式教学</b> — 完美的语言契合"),
            (fld["feeder"], "<b>ISF Pre-School（坚尼地城，卑路乍街 97 号 — 不是薄扶林）</b>：港币 152,790 半日 + 港币 15K ACL。Feeder 强度 = 弱，除非持有 Capital Note。"),
            (fld["apply"], f'<a style="{LINK}" href="https://admissions.isf.edu.hk">admissions.isf.edu.hk</a> · 开放日 2026-08-29'),
        ],
        why_lbl,
        "香港最契合普通话主导女孩的学校。双语 + IB + 中华美德。年度资本费完全避开了大额债权陷阱。",
        caveat_lbl,
        "并非顶尖 STEM；高年级中文比例下降；FY 招生竞争激烈。ISF Pre-School 仅边际帮助（无正式优先权）。",
    )

    spcc = school_card(
        PILL_BEST, "第一梯队 — 最佳匹配",
        "圣保罗男女中学 SPCC — 小学 + 中学",
        [
            (fld["curriculum"], "DSE + IB DP <b>双轨并行</b>，自 S5 选择（DSS 直资双轨）"),
            (fld["location"], "麦当奴道（中学，半山）· 黄竹坑（小学）"),
            (fld["entry"], "<b>仅 P1 入学</b>（无 K 阶段）。直通车至中学。"),
            (fld["cohort"], "<b>P1 AY2029/30</b>（2022-09-01 至 2023-12-31 出生；女儿在该年龄层较年幼一边）或 P1 AY2030/31（较年长一边）"),
            (fld["fees"], "P1–P2 约港币 77,800（DSE）· IB 本地约港币 160K · IB 非本地约港币 201K"),
            (fld["capital"], "<b>未公开</b> ✓ 小学。请向 admissions@spcc.edu.hk 核实。"),
            (fld["ib"], "<b>平均 42.1 — 2025 年香港第一</b>"),
            (fld["mandarin"], "英语为教学语言，配合扎实的普通话/中文；具相当数量的内地背景学生群体"),
            (fld["feeder"], "<b>幼稚园提名计划（FD Scheme）</b>：≤5% 的 P1 名额开放给任何幼稚园校长 — <b>Tutor Time Dorset 校长可提名</b>。无额外费用。值得直接询问 Tutor Time。"),
            (fld["app_window"], "<b>2028-09-01 至 2028-09-05（仅 4 天窗口！）</b>对应 AY2029/30 P1。AY2027/28 预计约 2026-09-01 至 2026-09-05。"),
            (fld["apply"], f'<a style="{LINK}" href="https://www.spcc.edu.hk/admissions/local-admissions/primary/p1">spcc.edu.hk/admissions/local-admissions/primary/p1</a>'),
        ],
        why_lbl,
        "香港顶尖学术成绩，费用却仅为国际学校的零头。无债权、对内地背景家庭友好、地理位置中心。幼稚园提名计划是低成本杠杆 — Tutor Time Dorset 校长可提名。",
        caveat_lbl,
        "S1 录取比例约 20:1；各入学口都竞争激烈。4 天 P1 窗口不容失误。提名成功需 Tutor Time 同意女儿出色。",
    )

    vsa = school_card(
        PILL_BEST, "第一梯队 — 最佳匹配",
        "维多利亚（上海）学校 VSA",
        [
            (fld["curriculum"], "IB Continuum（PYP, MYP, DP）；小学阶段英语 + 普通话双语"),
            (fld["location"], "深湾，香港仔（港岛南）"),
            (fld["entry"], "<b>仅 Y1 主入学口</b>（要求 8 月时满 5 岁 8 个月 = 12 月 1 日截止）。Y7 中学入学。"),
            (fld["cohort"], "<b>Y1 AY2029/30</b>（2023 年 12 月 1 日前出生 → 女儿符合）。<b>不</b>符合 AY2028/29。"),
            (fld["fees"], "Y1–Y5 PYP 港币 181,200 · Y6 港币 200,700 · Y7–8 港币 203,700 · Y9–10 港币 205,400 · DP 港币 255,600 · 申请费港币 2,000"),
            (fld["capital"], "<b>资本费港币 60K（一次性，部分可退）</b> ✓ 在上限内。个人债权港币 300 万 = 超出上限（但免第 1 轮面试）。"),
            (fld["ib"], "平均 37.6（2025 年 5 名满分）"),
            (fld["mandarin"], "强双语模型 — 是香港追求真正普通话教育家庭的首选之一"),
            (fld["feeder"], f'<b style="color:{C_BEST};">维多利亚幼稚园 = 香港最强已验证 feeder</b>：每年约 170 名毕业生 → VSA Y1（共约 150 个 VSA 名额）。<b>现在</b>从 Tutor Time 转 K1 AY2026/27（2023 年生）。VK 学费约港币 80–110K/年。<b>这是 VSA 入学最高效的杠杆</b>。'),
            (fld["app_window"], "<b>约 2027 年 9 月 – 2028 年 2 月初</b>对应 Y1 AY2029/30。AY2027/28 截止日已过（2026-02-05）。"),
            (fld["apply"], f'<a style="{LINK}" href="https://admissions.vsa.edu.hk/application_index_v2.php">admissions.vsa.edu.hk</a>'),
        ],
        why_lbl,
        "中等成本的双语 IB Continuum。对内地背景家庭友好。维多利亚幼稚园 feeder 给予非凡的入学优势。",
        caveat_lbl,
        "香港仔通勤可能不适合鲗鱼涌一带（请确认）。Y1 申请仅对应 AY2029/30 — 不是之前说的 2028/29。要使用 VK feeder，<b>现在</b>就要转校。",
    )

    gtc = school_card(
        PILL_INFO, "第一梯队 — 强势选项",
        "优才（杨殷有娣）书院 GTC",
        [
            (fld["curriculum"], "本地 NSS（DSE）+ 高年级 IB DP（DSS 直通车）"),
            (fld["location"], "调景岭，将军澳"),
            (fld["entry"], "<b>仅 P1 主入学口</b>（也有 S5 IBDP 入学）"),
            (fld["cohort"], "<b>P1 AY2029/30</b>（2023 年 12 月 31 日前出生 → 女儿符合）"),
            (fld["fees"], "DSE P1 <b>港币 35,310</b>（名单中最便宜）· IBDP 港币 88,550 · 申请费港币 200"),
            (fld["capital"], "<b>无</b> ✓"),
            (fld["ib"], "<b>平均 40.04，56% 超 40 分</b> — 在此费用水平堪称卓越"),
            (fld["mandarin"], "英语为教学语言，配以扎实中文；对内地背景家庭友好"),
            (fld["feeder"], "<b>无</b> — 没有幼稚园 feeder。仅 P1 直接申请。"),
            (fld["app_window"], "<b>约 2028 年 5 月初 – 6 月初</b>对应 AY2029/30 P1。AY2027/28 预计 2026 年 5–6 月（即将开放）。"),
            (fld["apply"], f'<a style="{LINK}" href="https://admission.gtschool.hk">admission.gtschool.hk</a> · pri-tko@gtcollege.edu.hk'),
        ],
        why_lbl,
        "以国际学校零头的费用，达到世界一流的 IB 成绩。资优教育法与「反应试、研究导向」理念高度契合。无债权。",
        caveat_lbl,
        "TKO 通勤从港岛东偏远。直通车意味着早期承诺。无 KG feeder = 无早期入学策略。",
    )

    return f"""<!doctype html>
<html lang="zh-Hans">
<head><meta charset="utf-8"><title>香港选校 — 核实数据总结 v3</title></head>
<body style="margin:0;padding:0;background:{C_BG};">
<div style="{WRAP}">

<div style="{CARD}">
  <h1 style="{H1}">香港选校 — 核实数据总结 <span style="font-weight:400;color:{C_MUTED};">v3</span></h1>
  <div style="{MUTED}">适合：女孩，生于 2023 年 9 月中 · 香港护照 · 内地背景 · 普通话为主
  · 资本/债权上限港币 100 万 · 内地大学非主选</div>
  <div style="{MUTED};margin-top:6px;">
    资料库：
    <a style="{LINK}" href="https://github.com/astronvc/school-picker">github.com/astronvc/school-picker</a>
    · 生成于 {TODAY}
  </div>
  <div style="{MUTED};margin-top:6px;color:{C_DANGER};font-size:12px;">
    <b>v3 相对早期邮件的更正</b>：ISF 入学是 FY（不是 Pre-Reception）；SIS/CDNIS/VSA/Carmel/HKA/AIS 日期已从一手来源核实；
    feeder 项目（维多利亚幼稚园、ESF Class A 债权、SPCC 提名计划）已明确列出。完整一手来源详见 <code>04-evaluation/application-windows-verified.md</code>。
  </div>
</div>

<h2 style="{H2_DANGER}"><span style="{PILL_URGENT}">紧急</span> &nbsp; 已核实截止日（未来 18 个月）</h2>
<div style="{URGENT_CARD}">
  <p style="margin:0 0 8px 0;">数据从一手招生页面核实。女儿（生于 2023 年 9 月中）在<b>多个入学口和年级年</b>都符合资格 — 共有三个可行的 Y1/P1 入学年：AY2028/29（ESF）、AY2029/30（ISF/SPCC/VSA/GT）、AY2030/31（Aug-31 截止学校）。</p>

  <p style="margin:14px 0 6px 0;"><b style="color:{C_DANGER};">未来 5 个月内硬截止日：</b></p>
  <table style="{TBL}">
    <tr>
      <th style="{TH};width:14%;">截止日</th>
      <th style="{TH};width:14%;">学校</th>
      <th style="{TH};width:30%;">入学 · 年级年</th>
      <th style="{TH}">资本 · 备注</th>
    </tr>
    <tr><td style="{TD}"><b style="color:{C_DANGER};">2026-09-30</b></td><td style="{TD}"><b>SIS HK</b></td><td style="{TD}">PY1（3 岁）· AY2027/28 — 女儿主要年龄层</td><td style="{TD}">个人债权港币 200K ✓ · ACL 港币 20K/年 ✓ · 申请费港币 2,800</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_DANGER};">2026-10-02</b></td><td style="{TD}"><b>CDNIS</b></td><td style="{TD}">EY1（3 岁）· AY2027/28 — 女儿在年龄层较年长一边</td><td style="{TD}">预订金港币 80K ✓ · ACL 港币 43K/年 ✓（债权港币 220 万二级超出上限）</td></tr>
    <tr><td style="{TD}"><b style="color:{C_DANGER};">2026-10-10</b></td><td style="{TD}"><b>Harrow HK</b></td><td style="{TD}">Nursery · AY2027/28</td><td style="{TD}">申请费港币 1,500。注意 Capital Cert 港币 330 万 = 超出上限</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_DANGER};">2026-11-30</b></td><td style="{TD}"><b>CDNIS</b></td><td style="{TD}">Nursery（2 岁）— 替代路径 · AY2027/28</td><td style="{TD}">女儿在该年龄层较年长一边；Nursery 无资本费/债权要求</td></tr>
  </table>

  <p style="margin:14px 0 6px 0;"><b>滚动 — 现在就申请（无固定截止日）：</b></p>
  <table style="{TBL}">
    <tr>
      <th style="{TH};width:14%;">学校</th>
      <th style="{TH};width:30%;">入学 · 年级年</th>
      <th style="{TH}">资本 · 备注</th>
    </tr>
    <tr><td style="{TD}"><b>AIS HK</b></td><td style="{TD}">EC1（3 岁半日）· AY2027/28</td><td style="{TD}"><b>无债权</b> · ACL 港币 12K/年（最便宜的国际学校资本结构）✓ · 预订金港币 25K · 先到先得</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>HKA</b></td><td style="{TD}">Pre-K1（3 岁）· AY2026/27</td><td style="{TD}">家庭债权港币 630K ✓ 或 ACL 港币 32K/年 ✓ — 但 <b>HKA 自 2026 年 1 月 1 日起不再发行新债权</b></td></tr>
    <tr><td style="{TD}"><b>Carmel</b></td><td style="{TD}">Nursery · AY2026/27（10 月 31 日截止 — 女儿符合）</td><td style="{TD}"><b>无债权，小学无 ACL</b> ✓ · 接受非犹太家庭（Elsa 高中明确）</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>NAIS HK</b></td><td style="{TD}">Nursery · AY2027/28（建议 2026 年 12 月前申请）</td><td style="{TD}">CEF 港币 100K + ACL 港币 35K/年 ✓ 在上限内</td></tr>
    <tr><td style="{TD}"><b>Malvern Pre-School</b></td><td style="{TD}">Pre-Nursery（2–3 岁）· AY2026/27</td><td style="{TD}">在上限内。隐含（未公布）的 Malvern College Prep 1 优先权。</td></tr>
  </table>

  <p style="margin:14px 0 6px 0;"><b>2027 年（约 12–16 个月后申请）：</b></p>
  <table style="{TBL}">
    <tr>
      <th style="{TH};width:18%;">窗口</th>
      <th style="{TH};width:14%;">学校</th>
      <th style="{TH}">入学 · 年级年 · 备注</th>
    </tr>
    <tr><td style="{TD}"><b>约 2027-08-01 至 09-11</b></td><td style="{TD}"><b>ISF Academy</b></td><td style="{TD}">Foundation Year · AY2028/29（女儿在 9–12 月双层灵活下处于较年幼一边）</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>2027-09-01 至 2027-09-30</b></td><td style="{TD}"><b>ESF</b></td><td style="{TD}">Y1 Reception · AY2028/29 — <b>女儿主要 ESF 窗口</b>。<b>2027-09-01 前购买 INR 港币 50 万</b>享优先面试。标准 ESF + RCHK（INR 港币 40 万）+ Discovery College（INR 港币 40 万）都用此窗口。</td></tr>
    <tr><td style="{TD}"><b>约 2027 年 9 月 – 2028 年 2 月初</b></td><td style="{TD}"><b>VSA</b></td><td style="{TD}">Y1 Reception · AY2029/30（按 12 月 1 日截止女儿符合）</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>约 2027 年 9–10 月</b></td><td style="{TD}"><b>CIS</b></td><td style="{TD}">Reception · AY2028/29（不是 AY2027/28，按 8 月 31 日截止）。超出债权上限 — 详见超出上限部分。</td></tr>
  </table>

  <p style="margin:14px 0 6px 0;"><b>2028 年（约 24 个月后申请）：</b></p>
  <table style="{TBL}">
    <tr>
      <th style="{TH};width:24%;">窗口</th>
      <th style="{TH};width:14%;">学校</th>
      <th style="{TH}">入学 · 年级年 · 备注</th>
    </tr>
    <tr><td style="{TD}"><b>约 2028 年 5 月初 – 6 月初</b></td><td style="{TD}"><b>GTC</b></td><td style="{TD}">P1 · AY2029/30（名单中最便宜，港币 35K/年）</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>约 2028 年 8 月中（10 天窗口）</b></td><td style="{TD}"><b>DGJS → DGS</b></td><td style="{TD}">P1 · AY2029/30（仅女生 — 适合女儿）。DGJS 是 DGS 中学的独家 feeder。</td></tr>
    <tr><td style="{TD}"><b>2028-09-01 至 2028-09-05（仅 4 天窗口！）</b></td><td style="{TD}"><b>SPCC Primary</b></td><td style="{TD}">P1 · AY2029/30。如经批准，通过 <b>幼稚园提名计划</b> 由 Tutor Time Dorset 校长提名。</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>约 2028 年 8 月</b></td><td style="{TD}"><b>ISF Academy</b></td><td style="{TD}">FY · AY2029/30（AY2028/29 的替代选择，按 9–12 月双层灵活）</td></tr>
    <tr><td style="{TD}"><b>2028-09-01 至 2028-09-30</b></td><td style="{TD}"><b>ESF</b></td><td style="{TD}">Y1 · AY2029/30（AY2028/29 的替代）</td></tr>
  </table>
</div>

<h2 style="{H2_BEST}">显著提升入学概率的 feeder 项目</h2>
<div style="{FEEDER_CARD}">
  <p style="margin:0 0 8px 0;">如要最大化某顶尖学校的入学机会，这些 feeder 是可用的最高杠杆。<b>有些需要今年内行动。</b></p>

  <table style="{TBL}">
    <tr>
      <th style="{TH};width:24%;">Feeder → 主校</th>
      <th style="{TH};width:14%;">强度</th>
      <th style="{TH};width:18%;">成本（在港币 100 万上限内？）</th>
      <th style="{TH}">行动时机</th>
    </tr>
    <tr><td style="{TD}"><b>维多利亚幼稚园 → VSA</b></td><td style="{TD}"><span style="{PILL_BEST}">最强</span></td><td style="{TD}">VK 学费约港币 80–110K/年 ✓</td><td style="{TD}"><b>现在</b>从 Tutor Time 转 K1 AY2026/27（2023 年生）。每年约 170 名 VK 毕业生 → VSA Y1（共约 150 个 VSA 名额）。这是香港 VSA 入学最有效的 feeder。</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>SPCC 幼稚园提名计划</b></td><td style="{TD}"><span style="{PILL_INFO}">开放</span></td><td style="{TD}">无额外费用 ✓</td><td style="{TD}">开放给任何幼稚园校长 — <b>Tutor Time Dorset 校长可提名女儿</b>。在 4 天 P1 窗口期间提交提名表（2028 年 9 月对应 AY2029/30）。直接询问 Tutor Time Dorset 是否会提名。</td></tr>
    <tr><td style="{TD}"><b>ESF Class A 债权（K1）→ INR（Y1）</b></td><td style="{TD}"><span style="{PILL_INFO}">强</span></td><td style="{TD}">港币 50 万 ✓</td><td style="{TD}"><b>K1 AY2026/27 已于 2025 年 9 月截止</b>；仅候补名单 — 女儿 K1 窗口已关闭。<b>跳到 INR 港币 50 万对应 Y1 AY2028/29</b> — 2027 年 9 月申请。</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>DGJS → DGS</b>（仅女生）</td><td style="{TD}"><span style="{PILL_BEST}">独家</span></td><td style="{TD}">DGJS 港币 79K/年 ✓ · 无债权</td><td style="{TD}">DGJS 是 DGS 中学的独家 feeder。2028 年 8 月中申请 DGJS P1 对应 AY2029/30。</td></tr>
    <tr><td style="{TD}"><b>CDNIS Nursery → EY1</b></td><td style="{TD}"><span style="{PILL_INFO}">内部</span></td><td style="{TD}">Nursery：无资本要求 ✓ · EY1+：ACL 港币 43K/年 ✓</td><td style="{TD}">2026-11-30 前申请 Nursery AY2027/28，享 EY1 内部连续优先权。</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>Carmel ELC → Carmel 小学 → Elsa High</b></td><td style="{TD}"><span style="{PILL_INFO}">内部</span></td><td style="{TD}">小学无债权、无 ACL ✓</td><td style="{TD}">直接升学。Nursery AY2026/27 申请（滚动，10 月 31 日截止）。接受非犹太家庭。</td></tr>
    <tr><td style="{TD}"><b>HKA Pre-K → 直通车</b></td><td style="{TD}"><span style="{PILL_INFO}">内部</span></td><td style="{TD}">家庭债权港币 630K ✓ 或 ACL 港币 32K/年 ✓</td><td style="{TD}">Pre-K1 AY2026/27 申请（滚动）。债权须 2026 年 1 月 1 日前购买（已过 — 仅二级市场）。</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>Malvern Pre-School → Malvern College</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">隐含</span></td><td style="{TD}">在上限内（请核实）</td><td style="{TD}">Pre-Nursery AY2026/27 申请（滚动）。隐含优先权但未正式公布。</td></tr>
    <tr><td style="{TD}"><b>ISF Pre-School → ISF Academy</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">弱</span></td><td style="{TD}">ACL 港币 15K/年 ✓（学费港币 152K）</td><td style="{TD}">无正式优先权除非持有 Capital Note。Pre-School 在 <b>坚尼地城</b>（卑路乍街 97 号 — 之前说"薄扶林"是错的）。</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>DPS → DBS</b></td><td style="{TD}"><span style="{PILL_OUT}">2010 已结束</span></td><td style="{TD}">不适用</td><td style="{TD}">对女儿不适用（DBS 仅招男生）。正式 feeder 关系于 2010 年结束。</td></tr>
  </table>
</div>

<h2 style="{H2}">家庭概况</h2>
<table style="{TBL}">
  <tr><td style="{TH}">孩子</td><td style="{TD}">女孩，<b>生于 2023 年 9 月中</b>，目前就读 Tutor Time Dorset（鲗鱼涌一带，校内英语/中文约 50/50）</td></tr>
  <tr><td style="{TH}">家庭语言</td><td style="{TD}">在家约 70% 普通话 / 30% 英语 — 普通话为主</td></tr>
  <tr><td style="{TH}">国籍</td><td style="{TD}">香港护照（孩子）；父母来自中国内地</td></tr>
  <tr><td style="{TH}">教育理念</td><td style="{TD}">重视学术 + 自信 + 竞争力 — <b>反对</b>做题/考试/填鸭式；崇尚独立思考 + 研究方法 + STEM 深度</td></tr>
  <tr><td style="{TH}">年学费</td><td style="{TD}">不限</td></tr>
  <tr><td style="{TH}">资本费/债权上限</td><td style="{TD}"><b>港币 1,000,000</b></td></tr>
  <tr><td style="{TH}">内地大学</td><td style="{TD}">可选（非主要）</td></tr>
  <tr><td style="{TH}">宗教取向</td><td style="{TD}">略有偏好，但非强约束</td></tr>
  <tr><td style="{TH}">寄宿</td><td style="{TD}">不优先不排除</td></tr>
</table>

<h2 style="{H2}">第一梯队 — 最佳匹配候选</h2>
{isf}
{spcc}
{vsa}
{gtc}

<h2 style="{H2}">美国国际学校（AIS HK）— 独立评估</h2>
<div style="{CARD}">
  <div style="margin-bottom:8px;"><span style="{PILL_CAVEAT}">第三梯队 — 备选/视情况而定</span></div>
  <h3 style="{H3}">美国国际学校 American International School Hong Kong（窝打老道 125 号，九龙塘）</h3>
  <p style="margin:6px 0 10px 0;{MUTED}">独立结论，超越「不够学术」的口碑。完整评估在 <code>02-schools/american-international-school.md</code>。资本结构已核实：无债权。</p>
  <table style="{TBL}">
    <tr><td style="{TH};width:28%;">课程</td><td style="{TD}">美国课标 + AP（含 AP Capstone：Seminar + Research）。WASC 认证；1986 年创立。</td></tr>
    <tr><td style="{TH}">入学级别</td><td style="{TD}">EC1（3 岁半日），EC2（4 岁全日），G1 Junior（5 岁），G1+，... G12</td></tr>
    <tr><td style="{TH}">女儿年龄层</td><td style="{TD}"><b>EC1 AY2027/28</b>（滚动 — 现在申请）。也符合 EC2 AY2028/29，G1 Junior AY2029/30，G1 AY2030/31。</td></tr>
    <tr><td style="{TH}">年学费</td><td style="{TD}">EC HD 港币 97K · EC FD–G1 Junior 港币 146.8K · G1–4 港币 152.8K · G5–8 港币 164.4K · G9–12 港币 180.4K</td></tr>
    <tr><td style="{TH}">资本费/债权</td><td style="{TD}"><b>无债权</b> ✓✓ — ACL 港币 12K/年（第一胎）— 香港最低之一 · 预订金港币 25K · 申请费港币 1,500</td></tr>
    <tr><td style="{TH}">申请</td><td style="{TD}">滚动先到先得 — 入学容易、阻力小。已核实 <a style="{LINK}" href="https://ais.openapply.com/">ais.openapply.com</a></td></tr>
  </table>
  <p style="margin:10px 0 4px 0;"><b style="color:{C_BEST};">「不够学术」的结论 —</b>
  部分属实但被误读。AIS 并非弱校，但也不属顶尖。AP 成绩约比 HKIS 落后 10 个百分点
  （AIS 2022 年 85% 得 3+ 分 vs HKIS 2024–25 年 95% 得 3+ 分）；
  2023–25 窗口期未见 MIT/斯坦福/普林斯顿/CMU 录取记录，而 HKIS、ISF、ICS、CIS 均有此类记录。
  有据可查的录取包括 UC Berkeley、UCLA、NYU、Cornell、Northwestern、BU，偶有 Columbia / Oxford。</p>
  <p style="margin:8px 0 4px 0;"><b style="color:{C_DANGER};">不适合我们家庭的关键原因：</b><br>
  (1) <b>STEM 上限是核心短板。</b>AIS 公开课程上限为 AP Calc BC + AP Physics 2（代数版）。
  <b>没有 AP Physics C、没有多变量微积分、没有线性代数、没有微分方程。</b>HKIS 全部都有。<br>
  (2) <b>普通话作为专项科目</b>（每周 3–5 小时，按能力分组）— 而非内容媒介。
  对普通话主导的孩子，会让母语优势停滞，而不是复利化。</p>
  <p style="margin:8px 0 0 0;"><b style="color:{C_BEST};">保留在名单的理由：</b>
  无债权（港币 12K/年资本费）、滚动先到先得招生、AP Capstone 是真正的研究项目、非宗教、男女合校、九龙塘地铁直达。
  <b>可作为申请第一梯队时的低阻力备选</b>。</p>
</div>

<h2 style="{H2}">第二/三梯队（紧凑）</h2>
<table style="{TBL}">
  <tr>
    <th style="{TH}">梯队</th>
    <th style="{TH}">学校</th>
    <th style="{TH}">课程·位置</th>
    <th style="{TH}">年费·资本（已核实）</th>
    <th style="{TH}">女儿年龄层</th>
  </tr>
  <tr><td style="{TD}">B</td><td style="{TD}">新加坡国际学校 (SIS HK)</td><td style="{TD}">新加坡 + IB · 香港仔</td><td style="{TD}">PY 港币 103K · 个人债权港币 200K ✓</td><td style="{TD}"><b>PY1 AY2027/28</b>（现在开放）</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">B</td><td style="{TD}">加拿大国际学校 (CDNIS)</td><td style="{TD}">IB Continuum · 香港仔</td><td style="{TD}">EY1 港币 161K · ACL 港币 43K/年 ✓</td><td style="{TD}"><b>EY1 AY2027/28</b>（10 月 2 日截止）</td></tr>
  <tr><td style="{TD}">B</td><td style="{TD}">保良局蔡继有学校 (PLKCKY)</td><td style="{TD}">IB · 深水埗</td><td style="{TD}">请向学校核实 · ✓</td><td style="{TD}">P1 约 AY2029/30</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">B</td><td style="{TD}">圣士提反书院 (SSCPS/SSC)</td><td style="{TD}">IB 或 DSE · 赤柱 · 含寄宿选项</td><td style="{TD}">SSCPS 港币 94K · ✓</td><td style="{TD}">G1 AY2029/30（约 2028 年 6 月申请）</td></tr>
  <tr><td style="{TD}">B</td><td style="{TD}">DGJS → DGS（女生）</td><td style="{TD}">DSE + A-Level · 佐敦</td><td style="{TD}">DGJS 港币 79K · ✓</td><td style="{TD}"><b>P1 AY2029/30</b>（2028 年 8 月中申请）</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">C</td><td style="{TD}">美国国际学校 AIS HK</td><td style="{TD}">美国课标 + AP + AP Capstone · 九龙塘</td><td style="{TD}">约港币 150K · ACL 港币 12K/年 ✓ · 无债权</td><td style="{TD}">EC1 AY2027/28（滚动）</td></tr>
  <tr><td style="{TD}">C</td><td style="{TD}">墨尔文国际学校 Malvern HK</td><td style="{TD}">IB Continuum · 大埔</td><td style="{TD}">Prep 港币 199K · ACL 港币 42K/年 ✓ · INR 价格未公布</td><td style="{TD}">Prep 1 AY2030/31（或经 Pre-School AY2026/27）</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">C</td><td style="{TD}">香港学堂 HKA</td><td style="{TD}">IB Continuum · 西贡</td><td style="{TD}">Pre-K 港币 119K；K-G5 港币 229K · 家庭债权港币 630K ✓ 或 ACL 港币 32K/年 ✓</td><td style="{TD}">Pre-K1 AY2026/27（滚动）</td></tr>
  <tr><td style="{TD}">C</td><td style="{TD}">ESF RCHK</td><td style="{TD}">IB Continuum · 马鞍山</td><td style="{TD}">Y1 港币 154K · INR 港币 400K ✓ + NCL 港币 38K + 建筑费港币 50K</td><td style="{TD}"><b>Y1 AY2028/29</b>（2027 年 9 月申请）</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">C</td><td style="{TD}">ESF Discovery College</td><td style="{TD}">IB Continuum · 愉景湾</td><td style="{TD}">Y1 港币 170K · INR 港币 400K ✓ + 建筑费港币 8K/年</td><td style="{TD}"><b>Y1 AY2028/29</b>（2027 年 9 月申请）</td></tr>
  <tr><td style="{TD}">C</td><td style="{TD}">嘉米利学校 Carmel</td><td style="{TD}">IB Continuum · 半山/筲箕湾</td><td style="{TD}">Nursery 港币 114K · K-G5 港币 203K · 无债权、无 ACL ✓</td><td style="{TD}">Nursery AY2026/27（滚动，10 月 31 日截止）</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">C</td><td style="{TD}">史丹福美国学校 Stamford</td><td style="{TD}">IB DP · 何文田 / 西九</td><td style="{TD}">Pre-Primary 港币 220K · 资本费港币 150K 一次性 ✓ 或债权港币 500K ✓</td><td style="{TD}">Pre-Primary AY2029/30（无 K 阶段；女儿须等待）</td></tr>
  <tr><td style="{TD}">C</td><td style="{TD}">澳洲国际学校 AISHK</td><td style="{TD}">HSC 或 IB · 九龙塘 · 1–12 月学年</td><td style="{TD}">Reception 港币 156K · 债权港币 120K ✓</td><td style="{TD}">Reception 约 2028 年 1 月入学</td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}">C</td><td style="{TD}">NAIS HK</td><td style="{TD}">IB DP · 蓝田 / 观塘</td><td style="{TD}">Nursery 起 · CEF 港币 100K + ACL 港币 35K/年 ✓</td><td style="{TD}">Nursery AY2027/28（滚动）</td></tr>
  <tr><td style="{TD}">C</td><td style="{TD}">凯莉山书院 Kellett</td><td style="{TD}">英国 · 薄扶林 / 九龙湾</td><td style="{TD}">ACL 港币 40K/年 ✓ — 债权港币 100 万+ 超出上限</td><td style="{TD}">Reception AY2028/29 — 目前候补满</td></tr>
</table>

<h2 style="{H2}"><span style="color:{C_CAVEAT};">⚠</span> 超出债权上限 — 申请须有现实预期</h2>
<div style="{CARD};border-left:4px solid {C_CAVEAT};">
  <p style="margin:0 0 8px 0;">这些学校<b>都接受不购买债权的申请</b>—但若不支付资本优先费用，实际录取概率会大幅降低。</p>
  <table style="{TBL}">
    <tr>
      <th style="{TH};width:18%;">学校</th>
      <th style="{TH};width:24%;">优先所需资本</th>
      <th style="{TH};width:28%;">购买后享有</th>
      <th style="{TH}">不购买 — 现实概率</th>
    </tr>
    <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ CIS</b></td><td style="{TD}">CNR 港币 1500 万直接申请 · 港币 110–150 万二级市场</td><td style="{TD}">Reception / S1 阶段优先申请位</td><td style="{TD}">普通申请池约 5–8% 录取率。女儿年龄层 = Reception AY2028/29（不是 2027/28）。</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ Harrow HK</b></td><td style="{TD}">Capital Certificate 约港币 330 万（可转售）</td><td style="{TD}">优先申请位</td><td style="{TD}">屯门地理位置使需求略低。Nursery AY2027/28 截止 2026-10-10。</td></tr>
    <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ HKIS</b></td><td style="{TD}">家庭债权港币 300 万 / 企业港币 500 万（不可转售）</td><td style="{TD}">优先申请位</td><td style="{TD}">普通申请池约 3–5% 录取率。R1 AY2028/29（滚动）。</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ GSIS</b>（英语流）</td><td style="{TD}">标准债权港币 50 万（在上限内！）或 Infrastructure 港币 600 万</td><td style="{TD}">标准债权符合资格；Infrastructure 享「首选录取优先权」</td><td style="{TD}">Y01 AY2030/31 仅适用于女儿（高度选择性）。</td></tr>
    <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ YCIS</b></td><td style="{TD}">债权自港币 200 万起（可转售）</td><td style="{TD}">优先申请位</td><td style="{TD}">知名度不及 CIS/HKIS — 不购买债权机会中等。</td></tr>
    <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ CDNIS</b>（债权路径）</td><td style="{TD}">仅二级市场约港币 220 万（学校已不再发行新债权）</td><td style="{TD}">优先 + ACL 豁免</td><td style="{TD}">CDNIS 普通池：港币 80K 预订 + 港币 43K/年 ACL 在上限内。债权可选。</td></tr>
  </table>
</div>

<h2 style="{H2}">核心洞察 — 研究的真实结论</h2>
<table style="{TBL}">
  <tr>
    <th style="{TH};width:6%;">序号</th>
    <th style="{TH}">洞察</th>
  </tr>
  <tr>
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">1</td>
    <td style="{TD}"><b>2026 年的证据强力验证反对应试教育的立场。</b>METR + Brynjolfsson 「矿井金丝雀」研究证实：以「标准考试第一名」为目标，正是在优化 AI 正在快速商品化的能力。</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">2</td>
    <td style="{TD}"><b>课程排序：</b>A-Level + 高等数学 + EPQ ≈ IB DP（在优秀学校）≈ AP Capstone（香港仅 HKIS / AIS HK 提供）> DSE+IB 双轨 > 纯 DSE。</td>
  </tr>
  <tr>
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">3</td>
    <td style="{TD}"><b>DSS（直资）的价值差距真实存在。</b>SPCC 2025 IB 平均 42.1 分位居香港榜首，年费约港币 16 万 · GTC 年费仅港币 8.8 万即达 40.04 / 56% 超 40 分。</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">4</td>
    <td style="{TD}"><b>香港护照如今在顶尖国际学校反而是劣势。</b>EDB 2026/27 学年 70% 非本地比例收紧。ESF 个人提名权港币 50 万是香港最便宜的优先入学杠杆。</td>
  </tr>
  <tr>
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">5</td>
    <td style="{TD}"><b>普通话母语是优势。</b>能将其转化为复利优势的学校：ISF（70/30）、CIS（50/50）、VSA、CDNIS 双语班、YCIS、SIS、SPCC。AIS HK 不会复利化普通话。</td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};color:{C_PRIMARY};font-weight:700;">6</td>
    <td style="{TD}"><b>女儿有三个可行的 Y1 入学年</b>：AY2028/29（ESF，按自然年截止）、AY2029/30（ISF/SPCC/VSA/GT，9–12 月双层灵活）、AY2030/31（Aug-31 截止学校）。「正确」答案取决于哪所学校以及希望她是同届中较年长还是较年幼。</td>
  </tr>
</table>

<h2 style="{H2}">行动时间表（女孩，生于 2023 年 9 月中）</h2>
<table style="{TBL}">
  <tr>
    <th style="{TH};width:14%;">年份</th>
    <th style="{TH};width:10%;">年龄</th>
    <th style="{TH}">行动</th>
  </tr>
  <tr>
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2026（现在）</td>
    <td style="{TD}">2.5–3 岁</td>
    <td style="{TD}">
      <b style="color:{C_DANGER};">紧急（未来 5 个月）：</b>申请 <b>SIS PY1（9 月 30 日）</b>、<b>CDNIS EY1（10 月 2 日）</b>、<b>Harrow Nursery（10 月 10 日）</b>、<b>CDNIS Nursery（11 月 30 日）</b>。
      <b>滚动现在申请</b>：AIS HK EC1、NAIS Nursery、HKA Pre-K、Carmel Nursery、Malvern Pre-N。
      <b>战略决策</b>：是否从 Tutor Time 转 <b>维多利亚幼稚园 K1 AY2026/27</b>（2023 年生年龄层）以获得 VSA 最强 feeder？
      <b>未来 3 个月内参访</b> ISF + SPCC + VSA + GTC + AIS HK。
    </td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2027</td>
    <td style="{TD}">3–4 岁</td>
    <td style="{TD}">
      <b>8 月 1 日 – 9 月 11 日</b>：申请 ISF FY 对应 AY2028/29。
      <b>9 月 1 日 – 9 月 30 日</b>：申请 ESF Y1 + INR 港币 50 万（9 月 1 日前购买）对应 AY2028/29；同时 RCHK + Discovery College Y1（每个 INR 港币 40 万）。
      <b>9 月 – 2028 年 2 月初</b>：申请 VSA Y1 对应 AY2029/30。
      <b>9–10 月</b>：申请 CIS Reception 对应 AY2028/29（超出债权上限的注意事项）。
    </td>
  </tr>
  <tr>
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2028</td>
    <td style="{TD}">4–5 岁</td>
    <td style="{TD}">
      <b>约 5 月初 – 6 月初</b>：申请 GTC P1 对应 AY2029/30。
      <b>约 8 月中（10 天窗口）</b>：申请 DGJS P1 对应 AY2029/30。
      <b>9 月 1 日 – 9 月 5 日（仅 4 天窗口！）</b>：申请 SPCC Primary P1 对应 AY2029/30 — 如经批准则提交 Tutor Time Dorset 校长的提名。
      <b>约 8 月</b>：申请 ISF FY AY2029/30 替代。
      <b>9 月 1 日 – 9 月 30 日</b>：申请 ESF Y1 AY2029/30 替代。
    </td>
  </tr>
  <tr style="background:{C_TBL_ALT};">
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2029</td>
    <td style="{TD}">5–6 岁</td>
    <td style="{TD}">在所选学校 P1/Y1 入学，对应 AY2029/30（多数学校）。通知约 2029 年春季。</td>
  </tr>
  <tr>
    <td style="{TD};font-weight:700;color:{C_PRIMARY};">2030</td>
    <td style="{TD}">6–7 岁</td>
    <td style="{TD}">在 AY2030/31 学校 P1/Y1 入学（CDNIS Prep、Malvern Prep 1、CIS、Harrow 等）— Aug-31 截止学校的最后常见入学年。</td>
  </tr>
</table>

<h2 style="{H2}">12 年总成本估算（数量级）</h2>
<table style="{TBL}">
  <tr>
    <th style="{TH}">学校</th>
    <th style="{TH}">年均 × 12</th>
    <th style="{TH}">资本费 / 债权</th>
    <th style="{TH}">总额估算（港币）</th>
    <th style="{TH}">是否在上限内</th>
  </tr>
  <tr><td style="{TD}"><b>GTC</b>（DSE→IBDP）</td><td style="{TD}">港币 70K × 12 = 港币 0.84M</td><td style="{TD}">无</td><td style="{TD}"><b>港币 0.84M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>SPCC</b>（DSE→IB 本地）</td><td style="{TD}">港币 130K × 12 = 港币 1.56M</td><td style="{TD}">无</td><td style="{TD}"><b>港币 1.56M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr><td style="{TD}"><b>VSA</b>（无债权）</td><td style="{TD}">港币 200K × 12 = 港币 2.4M</td><td style="{TD}">资本费港币 60K</td><td style="{TD}"><b>约港币 2.5M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>RCHK</b>（无 INR）</td><td style="{TD}">港币 170K × 12 = 港币 2.04M</td><td style="{TD}">建筑费港币 50K + NCL 港币 38K</td><td style="{TD}"><b>约港币 2.13M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr><td style="{TD}"><b>RCHK + INR</b>（享优先）</td><td style="{TD}">港币 170K × 12 = 港币 2.04M</td><td style="{TD}">+港币 400K INR</td><td style="{TD}"><b>约港币 2.5M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>AIS HK</b></td><td style="{TD}">港币 160K × 12 = 港币 1.92M</td><td style="{TD}">港币 12K × 12 = 港币 0.144M</td><td style="{TD}"><b>约港币 2.06M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr><td style="{TD}"><b>HKA</b>（家庭债权）</td><td style="{TD}">港币 210K × 12 = 港币 2.52M</td><td style="{TD}">港币 630K（可退；请核实）</td><td style="{TD}"><b>约港币 3.15M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>SIS HK</b></td><td style="{TD}">港币 190K × 12 = 港币 2.28M</td><td style="{TD}">个人债权港币 200K + 入学费港币 13K</td><td style="{TD}"><b>约港币 2.5M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr><td style="{TD}"><b>CDNIS</b>（无债权）</td><td style="{TD}">港币 220K × 12 = 港币 2.64M</td><td style="{TD}">港币 80K 预订 + 港币 12.5K 入学 + 港币 43K × 12 ACL = 港币 609K</td><td style="{TD}"><b>约港币 3.25M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b>ISF</b>（年度 ACL）</td><td style="{TD}">港币 270K × 12 = 港币 3.24M</td><td style="{TD}">港币 40K × 12 = 港币 0.48M</td><td style="{TD}"><b>港币 3.72M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr><td style="{TD}"><b>Carmel</b>（小学→Elsa）</td><td style="{TD}">港币 190K × 12 = 港币 2.28M</td><td style="{TD}">仅 G6+ 港币 18.5K/年 ACL ≈ 港币 130K</td><td style="{TD}"><b>约港币 2.4M</b></td><td style="{TD}"><span style="{PILL_BEST}">是</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ HKIS</b></td><td style="{TD}">港币 265K × 12 = 港币 3.18M</td><td style="{TD}">债权港币 300–500 万（不可转售）</td><td style="{TD}"><b>港币 600 万+</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">超出上限</span></td></tr>
  <tr><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ CIS 直接申请</b></td><td style="{TD}">港币 235K × 12 = 港币 2.82M</td><td style="{TD}">CNR 港币 1500 万</td><td style="{TD}"><b>港币 1700 万+</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">超出上限</span></td></tr>
  <tr style="background:{C_TBL_ALT};"><td style="{TD}"><b style="color:{C_CAVEAT};">⚠ Harrow HK</b></td><td style="{TD}">港币 185K × 12 = 港币 2.22M</td><td style="{TD}">Capital Cert 约港币 330 万（可转售）</td><td style="{TD}"><b>约港币 5.5M</b></td><td style="{TD}"><span style="{PILL_CAVEAT}">超出上限</span></td></tr>
</table>
<p style="{MUTED};margin-top:6px;">数字为按当前费用估算的<i>数量级</i>；可退还债权部分可收回；未计算手足折扣。承诺前请向各校核实。</p>

<p style="margin:14px 0 6px 0;"><b>债权上限内的成本效益前沿</b>：</p>
<ul style="margin:0 0 0 18px;padding:0;">
  <li><b>GTC 约港币 84 万</b> — 若可接受 TKO 通勤，每分 IB 的性价比无可匹敌</li>
  <li><b>SPCC 约港币 156 万</b> — 香港顶尖 IB 成绩，中等成本</li>
  <li><b>AIS HK 约港币 206 万</b> — 在上限内，但适配度为第三梯队（STEM 上限 + 普通话稀释）</li>
  <li><b>RCHK 约港币 213 万 / +INR 约港币 250 万</b> · <b>Carmel 约港币 240 万</b> · <b>SIS HK 约港币 250 万</b> · <b>VSA 约港币 250 万</b> — 双语 IB，中等成本</li>
  <li><b>HKA 约港币 315 万</b> · <b>CDNIS 约港币 325 万</b> · <b>ISF 约港币 372 万</b> — 上限内的高级层</li>
</ul>

<h2 style="{H2}">下一步行动</h2>
<ol style="margin:6px 0 6px 18px;padding:0;">
  <li><b style="color:{C_DANGER};">紧急（未来 4 个月内）：</b>提交申请 SIS PY1（9 月 30 日）、CDNIS EY1（10 月 2 日）、Harrow Nursery（10 月 10 日）、CDNIS Nursery（11 月 30 日）。同时滚动：AIS HK、NAIS、HKA、Carmel、Malvern Pre-N。</li>
  <li><b>现在的战略决策</b>：如 VSA 是首选，是否从 Tutor Time 转维多利亚幼稚园 K1 AY2026/27（香港最强 feeder）。</li>
  <li><b>询问 Tutor Time Dorset 校长</b>是否会就 SPCC 幼稚园提名计划（≤5% 的 P1 名额）提名女儿。</li>
  <li><b>未来 3 个月内参访</b> ISF + SPCC + VSA + GTC + AIS HK。</li>
  <li><b>2027 年 9 月</b>：9 月 1 日前购买 ESF 个人提名权港币 50 万；申请 ESF Y1 + RCHK + Discovery College 对应 AY2028/29；申请 ISF FY 对应 AY2028/29；申请 VSA Y1 对应 AY2029/30。</li>
  <li><b>2028 年 9 月</b>：申请 SPCC P1、GTC P1、DGJS P1、ISF FY（AY2029/30）、ESF Y1（AY2029/30）对应 AY2029/30。</li>
  <li><b>在家继续培养英语</b> — 至 K2 时争取约 50/50。</li>
</ol>

<div style="margin-top:24px;padding:14px;background:{C_TBL_HDR};border-radius:8px;{MUTED}">
  完整资料库见
  <a style="{LINK}" href="https://github.com/astronvc/school-picker">github.com/astronvc/school-picker</a>。
  各校已核实详情见 <code>04-evaluation/application-windows-verified.md</code>（1,233 行，一手来源核实）。
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
