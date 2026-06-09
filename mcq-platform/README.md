# MCQ / Online Test Platform

An AI-generated MCQ bank for intense MCQ practice and daily concept-clarity drills, stored in a database and hosted as a **Cloudflare project**. Students access it online, take tests, and get their results.

## Layout

```
mcq-platform/
├── question-generation/   ← AI pipeline that generates MCQs from concepts/syllabus
├── database/              ← DBMS schema, migrations, seed data
└── cloudflare-app/        ← hosted test-taking app (Workers / Pages / D1)
```

## Notes

- Source of truth for concepts/topics is the `syllabus-engine/` output — generation should pull from there.
- This is an online app, not book content; keep it self-contained here.
- Per repo rules: no binaries in git; commit code, schema, and config only.
