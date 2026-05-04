# Research changelog

A reverse-chronological log of substantive updates to the knowledge base.

Format: `YYYY-MM-DD — <area> — <what changed and why>`. Cite sources where possible.

---

## 2026-05-04 — initial build

- Created repo structure (00-criteria → 06-sources)
- Drafted `00-criteria/our-needs.md` from user's stated priorities and constraints
- Built initial curriculum deep-dives in `01-curricula/`: IB, AP, A-Level, DSE, IGCSE, plus comparison matrix and future-skills analysis
- Built initial school landscape in `02-schools/`: international, ESF, DSS, private independent, local
- Built `03-admissions/hk-passport-mainland-parents.md` covering eligibility, debenture/nomination, language, POA mechanics
- Built `04-evaluation/scorecard-template.md` and an initial `shortlist.md`
- Sources gathered into `06-sources/`

Method: Web research May 2026. Verify time-sensitive items (fees, admissions criteria, exam syllabi) against primary sources before acting.

## 2026-05-04 — future-skills analysis added

- Wrote `01-curricula/future-skills-analysis.md`: evidence-based analysis of skills likely to be valuable in the 2035–2050 economy, with implications for HK K-12 curriculum and school-selection criteria. Anchored in WEF Future of Jobs 2025, OECD Skills Outlook 2025, McKinsey GenAI work, Stanford 2026 AI Index, METR time-horizon series, Anthropic Economic Index, PwC AI Jobs Barometer, and 2025–26 admissions / labour-market reporting. Validates and extends the family's existing priors on math/physics depth, independent thinking, and research approach.

## 2026-05-04 — synthesis pass (key-insights + scored shortlist)

- Wrote `04-evaluation/key-insights.md`: distilled the 4 research deep-dives into 10 actionable takeaways covering future-skills evidence, curriculum hierarchy, mainland JAS one-way door, EDB 70% non-local rule tightening for 2026/27, the DSS arbitrage opportunity (SPCC top IB at HK$160K vs CIS at HK$266K + HK$15M nomination), bilingual immersion mapping, school-visit signal/red-flag list, cost economics, and decision posture.
- Wrote `04-evaluation/shortlist.md`: tiered candidate list (Tier A: SPCC, ISF, DBS-IB, CIS; Tier B: VSA, SIS, Harrow, GTC, CDNIS, GSIS; Tier C: Malvern, RCHK, Discovery College, HKIS, SSC, YCIS) with scorecard ratings against the 10 dimensions in `04-evaluation/scorecard-template.md` and 10 open questions for the family to resolve.
- All synthesis cross-references the deep files in `01-curricula/`, `02-schools/`, and `03-admissions/`.

## 2026-05-04 — personalized to family answers

- Updated `00-criteria/our-needs.md` with family answers: girl, 2.5 yrs, currently at Tutor Time Dorset, ~70/30 Mandarin/English, debenture cap HK$1M, mainland-uni optional, mild religious preference, neutral on boarding. Open: geography + university destination bias.
- Wrote `01-curricula/mainland-university-paths.md`: clarifies the three different paths (JAS via DSE, 港澳台华侨联招, international undergraduate admissions). User asked if mainland JAS = 华侨联考 — they're separate schemes; either way, since mainland is optional for the family, no need to bias curriculum toward DSE.
- **Re-personalized `04-evaluation/shortlist.md`**: applied filters (girl, debenture <HK$1M, mainland optional). Removed: DBS (boys), CIS direct (CNR HK$15M), HKIS (HK$3–5M debenture), Harrow (HK$11M+), GSIS (HK$6M), YCIS (HK$2M+). Tier A becomes: **SPCC, ISF Academy, VSA, GTC**. Added "Action timeline for a 2.5 year old girl" with year-by-year decisions: 2026 visits + ESF Individual Nomination Right purchase if applicable; 2027 K2/Reception applications at thru-train internationals; 2029 P1 applications at top DSS. Suggested visit list (4 must-visit + 2 strong + 2 optional). Open questions narrowed to geography + uni destination bias.

## 2026-05-04 — application-windows research + AIS HK deep eval + bilingual email tool

- New file `04-evaluation/application-windows.md`: per-school exact admissions calendars researched (CDNIS, SPCC, ISF, VSA, GTC, SIS, ESF including INR purchase). **Surfaced critical urgent dates**: CDNIS EY1 deadline 2026-10-02 and SIS Prep Years deadline 2026-09-30 are the only K2-equivalent slots accepting at child's age cohort for AY2027/28; all other Tier A schools target P1/Y1 entry only (apply Sep 2028 for AY2029/30 entry). Flagged need for child's exact DOB to confirm age cohort fit.
- New file `02-schools/american-international-school.md` (~430 lines): independent deep evaluation of AIS HK per family request to investigate past the "not academic" reputation. Verdict: **Tier C — backup only**. AP results ~10pp behind HKIS; no documented MIT/Stanford/Princeton/CMU placements 2023–25. Decisive against for this family: (1) STEM ceiling caps at AP Calc BC + AP Physics 2 (no Physics C, no Multivariable, no Linear Algebra); (2) Mandarin is 3–5 hr/wk specialist subject (won't compound a Mandarin-dominant child). Decisive for keeping: no debenture, rolling admissions, AP Capstone is real research, MTR-served — useful low-friction backup.
- Updated `04-evaluation/shortlist.md`: added URGENT section at top with CDNIS/SIS deadlines + DOB requirement; added C10 AIS HK with full holistic verdict; replaced "Removed by constraints" table with **"Above debenture cap — apply with realistic caveat"** section listing CIS / Harrow / HKIS / GSIS / YCIS / CDNIS-with-debenture, each with capital-required, what-it-buys, and realistic-without-it columns. Corrected Harrow figure (Capital Certificate ~HK$3.3M resellable, not HK$11M+).
- New file `tools/send_summary_email.py`: **bilingual** Python SMTP script sending TWO rich-HTML emails (English + Simplified Chinese) from pureteabee@gmail.com to itself. Color-coded tables for the 3 mainland-uni paths, 4 Tier A schools (with application windows + apply links), AIS HK independent eval, Tier B/C portfolio, "above debenture cap" section with caveats, 6 key insights, year-by-year action timeline, and 12-year cost summary. Run with `GMAIL_APP_PASSWORD='xxxx xxxx xxxx xxxx' python3 tools/send_summary_email.py`. Supports `DRY_RUN=1` to render to local HTML files instead. Added `dry_run_*.html` to .gitignore.

## 2026-05-04 — Carmel School deep profile

- New file `02-schools/carmel-school-deep-profile.md` (~330 lines): full evidence-based investigation of Holly Rofé ELC + Carmel Elementary + Elsa High School against the family's specific situation.
- **Major finding (deal-breaker for our family at ELC/Elementary stages)**: Carmel's published admissions priority bands 1–5 are restricted to Jewish-affiliated applicants; **non-Jewish families are admissible only at Elsa High School (G6+, age ~11)**, via the International Stream. Confirmed against Carmel admissions page, JNS interview with Principal Friedmann, and Sassy Mama HK profile. Earlier shortlist note ("non-Jewish students accepted ~30% intake at HS") was directionally right for Elsa High but missed that ELC + Elementary are closed to non-Jewish families entirely.
- **Religious depth**: Carmel describes itself explicitly as "Modern Orthodox" + "strong commitment to Zionism." Hebrew + Jewish Studies are core for all students from age 3. Heavier religious overlay than ICS/HKIS. The family's "mild religious preference" criterion likely does not anticipate this level.
- **2025 IB DP results**: avg 38.1 (some sources 38.2), 43% ≥ 40, 100% pass, 14 graduates, 60+ uni offers across 6 countries (Duke, Columbia, McGill, Toronto, Edinburgh, Michigan, CUHK Med). Historical: 4 perfect 45s across 13 cohorts. Un-streamed (every student takes full DP), which makes the average more impressive than peer-school numbers.
- **STEM**: real Robotics Lab + Makerspace + FIRST Robotics championship participation. **Math AI HL is NOT offered** (only AA HL/SL + AI SL). For very small cohorts (~14 grads/yr), individual subjects may have ≤5 students.
- **Mandarin**: NOT bilingual immersion. Putonghua is one of three additional languages (alongside Hebrew, French) at Elementary; native-speaker Chinese A available at DP for bilingual diploma; "Advanced Mandarin for native Chinese speakers" available in Elsa High International Stream. Less Mandarin-strong than ISF / VSA / CIS / CDNIS.
- **Fees verified**: ELC HK$84,500/yr; Nursery/Pre-K HK$114,000; K–G5 HK$202,600; Elsa Main HK$202,600; Elsa International HK$237,370; Capital Levy G6–12 only HK$18,520/yr; **NO debenture, NO Elementary capital levy**. Total well within HK$1M cap.
- **Leadership transition Aug 2027**: Principal Rachel Friedmann (15+ years) being succeeded; Search Associates running recruitment. Real culture-shift risk for a small school.
- **Recommendation**: remove from active shortlist for ELC/Elementary entry — not available to this family. Keep as a possible 2031–32 revisit if the family by then values small-warm-school feel for Grade 6.
- Sources: Carmel.edu.hk (multiple pages), JNS, Times of Israel, Lookstein job posting, Sassy Mama, WhichSchoolAdvisor, EDB, IBO, international-schools-database.com.
