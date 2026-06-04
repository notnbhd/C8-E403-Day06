# [PROJECT NAME]

[SHORT DEMO DESCRIPTION]

This repository is a minimal Streamlit + Supabase demo scaffold suitable for demos, prototypes, or hackathons.

Quick start (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit .env to add your Supabase URL and KEY
streamlit run app.py
```

Files of interest:
- `app.py` — main Streamlit entrypoint and simple multipage router.
- `config/settings.py` — loads `.env` and exposes config values.
- `services/supabase_client.py` — small wrapper for Supabase client usage.
- `pages/` — UI pages (Main, Upload, Results, Config).
- `.env.example` — example env file for Supabase credentials.

Extend notes:
- Keep pages small and import processing logic from `helpers/` or `services/`.
- Use `prompts/` for AI prompts and `assets/` for images/static files.
# hevy-chatbot