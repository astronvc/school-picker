# Hong Kong School Picker

A private knowledge base for evaluating K-12 schooling options in Hong Kong, built and updated collaboratively with Claude.

## Family context

- Child: Hong Kong passport holder
- Parents: from mainland China
- Looking for: strong academics + confidence + competitive edge, **without** 做题 / 考试 / 填鸭式教育
- Want: independent thinking, research approach, strong math & physics fundamentals
- Lens: 发展眼光 — what will be most valuable in 10–20 years

## Structure

```
00-criteria/         — our needs, evaluation framework
01-curricula/        — IB / AP / A-Level / DSE / IGCSE / others + comparisons
02-schools/          — by school type: international, ESF, DSS, private, local
03-admissions/       — difficulty by passport / parental background / language
04-evaluation/       — scorecards, comparison matrices, shortlist
05-research-log/     — changelog of updates with dates and source notes
06-sources/          — raw clippings, primary documents, links
```

## How to update

This is a living knowledge base. When new info arrives:

1. Update the relevant file under `01-` to `04-`
2. Add an entry to `05-research-log/changelog.md` with date and what changed
3. Commit with a short, dated message and push

## Working with Claude

In any new Claude session in this directory, Claude will read `CLAUDE.md` to load project context and conventions. Ask Claude to:

- "Update the curriculum comparison with [new info]"
- "Add school X to the evaluation"
- "Re-score the shortlist given [new criterion]"
- "Research [topic] and add to the knowledge base"

## Provenance

Built initially via deep web research and curriculum analysis (May 2026). Always verify time-sensitive items (admissions criteria, fee schedules, government policy) against primary sources before acting on them.
