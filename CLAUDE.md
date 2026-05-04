# CLAUDE.md — instructions for Claude sessions in this repo

## What this repo is

A private knowledge base for evaluating Hong Kong K-12 school options for a specific family:

- **Child**: HK passport holder
- **Parents**: from mainland China
- **Philosophy**: strong academic + confidence + competitive — but explicitly against 做题、考试、填鸭式教育. Wants independent thinking, research approach, strong math & physics.
- **Lens**: 发展眼光 — anticipate skills valuable in 2035–2050

## Repo structure

See `README.md`. Briefly: criteria → curricula → schools → admissions → evaluation → research log → sources.

## Conventions

- **Cite sources.** Every factual claim about a school, fee, admissions stat, or policy should link to a source (school site, EDB, IB.org, news article). Mark unverified claims as `[unverified]`.
- **Date everything.** Top of each substantive file: `Last updated: YYYY-MM-DD`. When updating, change the date.
- **Distinguish marketing from evidence.** Schools claim a lot; cross-check with university destinations, IB results, alumni outcomes, parent forum (BabyKingdom, GeoExpat) chatter.
- **Both Western and Chinese university paths.** The child has options for HK universities, US/UK universities, and via the Joint Programme to mainland universities (清北 included). Don't optimize only for one path.
- **No emoji unless asked.** Plain markdown.

## Update workflow

When the user asks to update knowledge:

1. Read `05-research-log/changelog.md` for prior updates
2. Make the change in the relevant file(s)
3. Append a dated entry to `changelog.md`
4. `git add -A && git commit -m "<short dated message>" && git push`

## Scoring rubric (see 04-evaluation/)

The shortlist uses a multi-criteria score. When evaluating a new school, score it against the same criteria so it's comparable.

## Things that are *not* in scope

- Pre-school / nursery (this is K-12)
- Boarding outside Hong Kong (a separate repo if user wants)
- Tutorial centres
