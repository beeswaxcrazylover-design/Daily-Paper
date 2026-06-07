# Security Notes

Do not commit local credentials or personal research data.

Ignored by default:

- `embodied_ai_paper_system/.env`
- virtual environments
- generated logs
- Semantic Scholar candidate caches
- recommendation history
- local landmark paper database
- Obsidian vault files
- downloaded PDFs

Before pushing to GitHub, run:

```powershell
git status --short --ignored
git grep -n -E "sk-[A-Za-z0-9_-]{10,}|DEEPSEEK_API_KEY\s*=\s*[^\s#].+|SEMANTIC_SCHOLAR_API_KEY\s*=\s*[^\s#].+"
```

Only `.env.example` and documentation placeholders should mention environment
variable names. Real API keys must stay in the ignored `.env` file.

