# CampusBridge AI

*Opportunities should have no language barrier.*

## Live App

🚀 **Try CampusBridge AI:** https://campusbridge-ai.streamlit.app/

## The Problem

Students don't always miss opportunities because they lack talent. Sometimes
they miss them because they don't understand the information quickly enough.
Internships, hackathons, scholarships, fellowships, and university notices are
often long, poorly structured, spread across WhatsApp/email/websites, and
written in unfamiliar or formal language — leaving students unsure whether
they even qualify.

## The Solution

CampusBridge AI turns a pasted opportunity notice into a structured,
student-friendly action card: what it is, who can apply, the deadline, what's
required, and what to do next — with eligibility checking, multilingual
explanation, and notice-grounded Q&A on top.

## What It Does

- **Analyzes** opportunity notices into structured action cards
- **Checks eligibility** against a student's profile, without inventing requirements
- **Explains** opportunities naturally in English, Telugu, Hindi, Gujarati, or Tamil
- **Answers questions** grounded only in the original notice — never hallucinated
- **Saves** opportunities for later reference

## Demo

Click **Try Demo** in the app to instantly load the Iris Hacks IV announcement
itself and analyze it — a self-referential demo that shows the whole pipeline
in under 30 seconds.

## How It Works

```
User
  |
  v
Streamlit UI
  |
  v
CampusBridge Processing (services/)
  |
  v
Featherless LLM (deepseek-ai/DeepSeek-V3.2)
  |
  v
Structured Analysis (JSON)
  |
  v
Eligibility / Translation / Q&A
```

## Tech Stack

- **Python**
- **Streamlit** — UI
- **Featherless.ai** — LLM inference (OpenAI-compatible API)
- **SQLite** — saved opportunities

## AI Safety / Reliability

- The analyzer is instructed to **never invent** eligibility, deadlines,
  prizes, requirements, fees, or benefits — anything not stated is marked
  "Not specified" or listed under missing information.
- Eligibility verdicts default to **UNCERTAIN** rather than guessing when
  profile information is incomplete.
- Q&A answers only from the original notice — if the answer isn't there, it
  says so explicitly instead of hallucinating.
- Every AI call is wrapped with friendly error handling for auth failures,
  gated models, rate limits, timeouts, and cold-model 503s — the app never
  crashes or shows a raw stack trace.

## Challenges We Faced

**Challenge 1: Preventing the model from filling missing eligibility
requirements with assumptions.**
Solved with structured JSON extraction, explicit uncertainty handling in the
prompt, and a required `missing_information` field in the schema.

**Challenge 2: LLM responses aren't always perfectly formatted JSON.**
Solved with a safe parser that strips markdown code fences and falls back to
extracting the outermost `{...}` object before giving up.

**Challenge 3: Streamlit reruns can trigger unnecessary inference calls.**
Solved by storing analysis, eligibility, and Q&A results in `st.session_state`
so the UI only calls the AI when the user explicitly requests it.

## Future Scope

- PDF/image notice understanding (OCR)
- WhatsApp / Telegram / email integration
- University dashboards and personalized opportunity feeds
- Calendar reminders for deadlines
- Verified opportunity sources
- Voice interface

## Local Setup

```bash
git clone https://github.com/HariSetti9/campusbridge-ai.git
cd campusbridge-ai
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then fill in FEATHERLESS_API_KEY
streamlit run app.py
```

## Deployment (Streamlit Community Cloud)

1. Push this repo to GitHub (public).
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → point to `app.py`.
3. Under **Advanced settings → Secrets**, add:
   ```
   FEATHERLESS_API_KEY = "your-key-here"
   FEATHERLESS_MODEL = "deepseek-ai/DeepSeek-V3.2"
   ```
4. Deploy.

## Team

**Hari Setti** — Developer

---

CampusBridge provides AI-assisted guidance. Always verify final eligibility
and deadlines with the official organizer.
