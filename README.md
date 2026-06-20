# AI Code Reviewer

A Streamlit tool that sends code to **Gemini 3 Flash Preview** and returns
detailed, senior-developer-style feedback: bugs, inefficiencies, best
practices, security issues, and concrete suggested fixes.

## Setup

```bash
pip install -r requirements.txt
```

## Provide your API key (one-time setup, no more pasting)

Copy the example file and fill in your real key:

```bash
cp .env.example .env
```

Then edit `.env` so it contains:

```
GEMINI_API_KEY=your-actual-key-here
```

The app loads this automatically on startup via `python-dotenv`. `.env` is
already listed in `.gitignore`, so it won't get committed or shared by
accident.

You can still override the key for a single session from the sidebar
("Override key for this session") without touching the file.

### Optional: protect a deployed app with an access code

If you deploy this somewhere public, anyone with the link can use it and
spend your API quota. To require a shared code before the app is usable,
set `ACCESS_CODE` (in `.env` locally, or as a secret on your hosting
platform). Leave it blank/unset to disable the gate.

## Deploying for free (Streamlit Community Cloud)

1. Push this repo to GitHub (`.env` stays out of it thanks to `.gitignore`).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub, click **New app**, and select this repo, branch, and `app.py`.
3. Before deploying, open **Advanced settings → Secrets** and paste:
   ```toml
   GEMINI_API_KEY = "your-actual-key-here"
   ACCESS_CODE = "pick-a-code-if-you-want-the-gate"
   ```
   Root-level secrets here are automatically available as environment
   variables, so no code changes are needed.
4. Click **Deploy**. You'll get a `https://your-app.streamlit.app` URL.

## Run

```bash
streamlit run app.py
```

Then open the local URL Streamlit prints (usually http://localhost:8501).

## Using it

1. Paste code into the text box, or upload a source file.
2. Pick the language (auto-detected from file extension if you upload).
3. Optionally describe what the code is supposed to do — this gives the
   model context and improves the review.
4. Choose focus areas (bugs, performance, style, security, readability) in
   the sidebar.
5. Click **Review my code**. The feedback streams in as Markdown, with a
   severity-tagged bug list, a suggested-fixes section, and an overall score.
6. Download any review as a `.md` file, or revisit past reviews from this
   session in the "Past reviews" section at the bottom.

## Notes

- `thinking_level: high` (default) gives more thorough reviews but is
  slower; switch to `low` for quick sanity checks on short snippets.
- The model name is fixed to `gemini-3-flash-preview` per your request. If
  Google deprecates/renames this preview model, update `MODEL_NAME` in
  `app.py`.
- This calls the public Gemini API directly from your machine — no data is
  sent anywhere else.