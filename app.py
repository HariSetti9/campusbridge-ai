"""
CampusBridge AI — Opportunities should have no language barrier.
Built for Iris Hacks IV.

Run with: streamlit run app.py
"""

import html
import json

import streamlit as st

from config import APP_NAME, APP_TAGLINE, SUPPORTED_LANGUAGES
from data.sample_notice import SAMPLE_NOTICE
from database.db import (
    init_db, save_opportunity, list_saved_opportunities, delete_opportunity,
)
from services.ai_service import AIServiceError
from services.analyzer import analyze_notice
from services.eligibility import check_eligibility, estimate_fit
from services.qa import ask_about_notice
from services.translator import explain_in_language
from utils.parsers import ParseError
from utils.validators import validate_notice_text, validate_question

EXPLAIN_LANGUAGES = ["Simple English"] + SUPPORTED_LANGUAGES

QA_EXAMPLE_QUESTIONS = [
    "Can I participate?",
    "What do I need to submit?",
    "Is this online?",
    "Is there any fee?",
    "When is the deadline?",
    "What should I do first?",
]

# ---------- Page config & styling ----------
st.set_page_config(page_title=APP_NAME, page_icon="🌉", layout="centered")

init_db()

CUSTOM_CSS = """
<style>
    .block-container { padding-top: 2.2rem; max-width: 880px; }
    h1, h2, h3, h4 { letter-spacing: -0.01em; }
    .cb-hero-title { font-size: 2.1rem; font-weight: 700; margin-bottom: 0.1rem; }
    .cb-hero-tagline { font-size: 1.05rem; color: #6b7280; margin-bottom: 0.3rem; }
    .cb-hero-desc { font-size: 0.98rem; color: #374151; margin-bottom: 0.5rem; }
    .cb-feature-line { font-size: 0.85rem; color: #6366f1; font-weight: 600; margin-bottom: 1.3rem; }
    .cb-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .cb-card h4 {
        margin-top: 0;
        margin-bottom: 0.5rem;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #6366f1;
    }
    .cb-mini-card {
        background: #f9fafb;
        border: 1px solid #eef0f3;
        border-radius: 12px;
        padding: 0.7rem 0.9rem;
        text-align: center;
    }
    .cb-mini-card .label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #9ca3af;
        margin-bottom: 0.15rem;
    }
    .cb-mini-card .value { font-size: 0.95rem; font-weight: 600; color: #111827; }
    .cb-badge {
        display: inline-block;
        background: #eef2ff;
        color: #4338ca;
        border-radius: 999px;
        padding: 0.15rem 0.7rem;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 0.4rem;
    }
    .cb-trust-card {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 12px;
        padding: 0.7rem 1rem;
        font-size: 0.85rem;
        color: #166534;
        margin: 0.8rem 0;
    }
    .cb-next-card {
        background: #fafafa;
        border: 1px dashed #d1d5db;
        border-radius: 12px;
        padding: 0.8rem 1rem;
        margin-top: 1rem;
    }
    .cb-verdict-eligible { color: #15803d; font-weight: 700; }
    .cb-verdict-uncertain { color: #b45309; font-weight: 700; }
    .cb-verdict-not { color: #b91c1c; font-weight: 700; }
    .cb-fit-strong { color: #15803d; font-weight: 700; }
    .cb-fit-moderate { color: #b45309; font-weight: 700; }
    .cb-fit-weak { color: #b91c1c; font-weight: 700; }
    .cb-disclaimer {
        font-size: 0.82rem;
        color: #9ca3af;
        border-top: 1px solid #f0f0f0;
        margin-top: 1.5rem;
        padding-top: 0.8rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def esc(value) -> str:
    """Escape any value before inserting it into raw HTML."""
    if value is None:
        return ""
    return html.escape(str(value))


def esc_list_items(items) -> str:
    return "".join(f"<li>{esc(item)}</li>" for item in (items or []))


def verdict_class(verdict: str) -> str:
    v = (verdict or "").upper()
    if "NOT ELIGIBLE" in v:
        return "cb-verdict-not"
    if "ELIGIBLE" in v and "NOT" not in v:
        return "cb-verdict-eligible"
    return "cb-verdict-uncertain"


def fit_class(fit: str) -> str:
    f = (fit or "").upper()
    if "STRONG" in f:
        return "cb-fit-strong"
    if "WEAK" in f:
        return "cb-fit-weak"
    return "cb-fit-moderate"


# ---------- Session state defaults ----------
for key, default in [
    ("notice_input", ""),
    ("opportunity", None),
    ("eligibility_result", None),
    ("eligibility_profile", None),
    ("fit_result", None),
    ("qa_history", []),
    ("pending_question", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ---------- Header ----------
st.markdown(f'<div class="cb-hero-title">🌉 {esc(APP_NAME)}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="cb-hero-tagline">{esc(APP_TAGLINE)}</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="cb-hero-desc">Turn any internship, hackathon, scholarship or '
    'university notice into eligibility, deadlines and clear next actions — in seconds.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="cb-feature-line">Understand opportunities &nbsp;•&nbsp; '
    'Check eligibility &nbsp;•&nbsp; Explain in your language &nbsp;•&nbsp; Ask questions</div>',
    unsafe_allow_html=True,
)

tab_analyze, tab_eligibility, tab_qa, tab_saved, tab_about = st.tabs(
    ["📄 Analyze", "✅ Eligibility", "💬 Ask CampusBridge", "📌 Saved", "ℹ️ About"]
)

# ================= ANALYZE TAB =================
with tab_analyze:
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Try Demo", use_container_width=True):
            # Must set the WIDGET's own key (notice_input) before the widget is
            # instantiated this run — setting a differently-named state var here
            # does not update an already-rendered text_area's visible value.
            st.session_state.notice_input = SAMPLE_NOTICE
            st.session_state.opportunity = None
            st.session_state.eligibility_result = None
            st.session_state.fit_result = None
            st.session_state.qa_history = []

    st.text_area(
        "Paste an opportunity notice here...",
        height=220,
        key="notice_input",
    )
    notice_text = st.session_state.notice_input

    analyze_clicked = st.button("Analyze Opportunity", type="primary")

    if analyze_clicked:
        error = validate_notice_text(notice_text)
        if error:
            st.warning(error)
        else:
            with st.spinner("CampusBridge is reading the opportunity..."):
                try:
                    opportunity = analyze_notice(notice_text)
                    st.session_state.opportunity = opportunity
                    st.session_state.eligibility_result = None
                    st.session_state.fit_result = None
                    st.session_state.qa_history = []
                except (AIServiceError, ParseError) as e:
                    st.error(f"CampusBridge couldn't analyze this notice right now. {e}")
                except Exception:
                    st.error("CampusBridge couldn't analyze this notice right now. Please try again.")

    opp = st.session_state.opportunity
    if opp:
        st.markdown("---")
        badge_type = opp.get("opportunity_type") or "Opportunity"
        st.markdown(f'<span class="cb-badge">{esc(badge_type.upper())}</span>', unsafe_allow_html=True)
        st.subheader(opp.get("title") or "Not specified")
        if opp.get("organization") and opp["organization"] != "Not specified":
            st.caption(opp["organization"])
        if opp.get("summary"):
            st.write(opp["summary"])

        # Compact quick-fact cards
        quick_facts = [
            ("Deadline", opp.get("deadline")),
            ("Mode", opp.get("mode")),
            ("Location", opp.get("location")),
            ("Cost", opp.get("cost")),
        ]
        quick_facts = [(label, val) for label, val in quick_facts if val and val != "Not specified"]
        if quick_facts:
            cols = st.columns(len(quick_facts))
            for col, (label, val) in zip(cols, quick_facts):
                with col:
                    st.markdown(
                        f'<div class="cb-mini-card"><div class="label">{esc(label)}</div>'
                        f'<div class="value">{esc(val)}</div></div>',
                        unsafe_allow_html=True,
                    )

        st.markdown(
            '<div class="cb-trust-card">🛡️ <b>Grounded Analysis</b> — CampusBridge only '
            "extracts information supported by the notice and marks missing details "
            "instead of guessing.</div>",
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f'<div class="cb-card"><h4>Who Can Participate</h4><ul>'
                f'{esc_list_items(opp.get("eligibility")) or "<li>Not specified</li>"}</ul></div>',
                unsafe_allow_html=True,
            )
            what_you_need = (opp.get("required_documents") or []) + (opp.get("skills_or_requirements") or [])
            st.markdown(
                f'<div class="cb-card"><h4>What You Need</h4><ul>'
                f'{esc_list_items(what_you_need) or "<li>Not specified</li>"}</ul></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="cb-card"><h4>Benefits</h4><ul>'
                f'{esc_list_items(opp.get("prize_or_benefits")) or "<li>Not specified</li>"}</ul></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div class="cb-card"><h4>What To Submit</h4><ul>'
                f'{esc_list_items(opp.get("submission_requirements")) or "<li>Not specified</li>"}</ul></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="cb-card"><h4>Important Dates</h4><ul>'
                f'{esc_list_items(opp.get("important_dates")) or "<li>Not specified</li>"}</ul></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="cb-card"><h4>Next Actions</h4><ol>'
                f'{esc_list_items(opp.get("next_actions")) or "<li>Not specified</li>"}</ol></div>',
                unsafe_allow_html=True,
            )

        need_to_verify = (opp.get("missing_information") or []) + (opp.get("warnings") or [])
        if need_to_verify:
            st.markdown(
                f'<div class="cb-card"><h4>Need to Verify</h4><ul>'
                f'{esc_list_items(need_to_verify)}</ul></div>',
                unsafe_allow_html=True,
            )

        st.markdown("#### Explain in your language")
        lang_col, btn_col = st.columns([3, 1])
        with lang_col:
            language = st.selectbox("Language", EXPLAIN_LANGUAGES, key="lang_select")
        with btn_col:
            st.write("")
            explain_clicked = st.button("Explain", key="explain_btn")

        if explain_clicked:
            simple_mode = (language == "Simple English")
            target_lang = "English" if simple_mode else language
            with st.spinner("Preparing a student-friendly explanation..."):
                try:
                    explanation = explain_in_language(opp, target_lang, simple_mode)
                    with st.container(border=True):
                        st.markdown(explanation)
                except AIServiceError as e:
                    st.error(str(e))

        if st.button("💾 Save this opportunity"):
            try:
                save_opportunity(opp, notice_text)
                st.success("Saved.")
            except Exception as e:
                st.error(f"Couldn't save this opportunity right now. ({e})")

        st.markdown(
            '<div class="cb-next-card">👉 <b>What\'s next?</b><br>'
            "Head to <b>✅ Eligibility</b> to check if you personally qualify, "
            "<b>💬 Ask CampusBridge</b> to ask a specific question, or use the "
            "language selector above to explain this notice in your language.</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="cb-disclaimer">CampusBridge provides AI-assisted guidance. '
            "Always verify final eligibility and deadlines with the official organizer.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("Paste a notice above (or click **Try Demo**) and hit **Analyze Opportunity** to get started.")

# ================= ELIGIBILITY TAB =================
with tab_eligibility:
    opp = st.session_state.opportunity
    if not opp:
        st.info("Analyze an opportunity in the **📄 Analyze** tab first.")
    else:
        st.write(f"Checking your fit for: **{opp.get('title', 'this opportunity')}**")
        with st.form("profile_form"):
            c1, c2 = st.columns(2)
            with c1:
                age = st.number_input("Age", min_value=10, max_value=100, value=20)
                country = st.text_input("Country", value="")
                education_level = st.selectbox(
                    "Education Level",
                    ["High School", "Undergraduate", "Postgraduate", "PhD", "Other"],
                )
                degree = st.text_input("Degree (e.g. B.Tech)", value="")
            with c2:
                field = st.text_input("Field / Major (e.g. Computer Science)", value="")
                year_of_study = st.text_input("Year of Study (e.g. 3rd year)", value="")
                cgpa = st.text_input("CGPA (optional)", value="")
                skills = st.text_area("Skills (comma-separated)", value="", height=68)
                experience = st.text_area("Relevant experience (optional)", value="", height=68)
            submitted = st.form_submit_button("Check My Eligibility", type="primary")

        if submitted:
            profile = {
                "age": age,
                "country": country,
                "education_level": education_level,
                "degree": degree,
                "field_or_major": field,
                "year_of_study": year_of_study,
                "cgpa": cgpa,
                "skills": [s.strip() for s in skills.split(",") if s.strip()],
                "experience": experience,
            }
            st.session_state.eligibility_profile = profile
            st.session_state.fit_result = None
            with st.spinner("Checking the stated requirements..."):
                try:
                    result = check_eligibility(opp, profile)
                    st.session_state.eligibility_result = result
                except (AIServiceError, ParseError) as e:
                    st.error(str(e))

        result = st.session_state.eligibility_result
        if result:
            st.markdown("---")
            vclass = verdict_class(result.get("verdict", ""))
            st.markdown(
                f'<div class="cb-card"><h4>Eligibility Result</h4>'
                f'<span class="{vclass}">{esc(result.get("verdict", "UNCERTAIN"))}</span> '
                f'&nbsp;·&nbsp; Confidence: {esc(result.get("confidence", "Low"))}</div>',
                unsafe_allow_html=True,
            )
            st.markdown("**Requirement Comparison**")
            for req in result.get("requirements", []):
                status = req.get("status", "UNKNOWN")
                icon = {"MATCH": "✅", "NO MATCH": "❌"}.get(status, "❓")
                st.markdown(f"{icon} **{req.get('requirement', '')}** — {status}  \n{req.get('reason', '')}")

            missing = result.get("missing_information") or []
            if missing:
                st.markdown("**Missing information:**")
                for m in missing:
                    st.markdown(f"- {m}")

            st.markdown(f"**Recommended action:** {result.get('recommended_action', '')}")
            st.markdown(
                '<div class="cb-disclaimer">CampusBridge provides AI-assisted guidance. '
                "Always verify final eligibility with the official organizer.</div>",
                unsafe_allow_html=True,
            )

            st.markdown("---")
            st.markdown("#### AI Opportunity Fit Estimate")
            if st.button("Get Fit Estimate"):
                with st.spinner("Estimating fit..."):
                    try:
                        fit = estimate_fit(opp, st.session_state.eligibility_profile, result)
                        st.session_state.fit_result = fit
                    except (AIServiceError, ParseError) as e:
                        st.error(str(e))

            fit = st.session_state.fit_result
            if fit:
                fclass = fit_class(fit.get("overall_fit", ""))
                st.markdown(
                    f'<div class="cb-card"><span class="{fclass}" style="font-size:1.1rem;">'
                    f'{esc(fit.get("overall_fit", "Moderate Fit"))}</span></div>',
                    unsafe_allow_html=True,
                )
                fcols = st.columns(4)
                dims = [
                    ("Eligibility", fit.get("eligibility_match")),
                    ("Skills Match", fit.get("skills_match")),
                    ("Experience", fit.get("experience_alignment")),
                    ("Readiness", fit.get("readiness")),
                ]
                for col, (label, val) in zip(fcols, dims):
                    with col:
                        st.markdown(
                            f'<div class="cb-mini-card"><div class="label">{esc(label)}</div>'
                            f'<div class="value">{esc(val)}</div></div>',
                            unsafe_allow_html=True,
                        )
                st.markdown(f"**Recommendation:** {fit.get('recommendation', '')}")
                st.markdown(
                    '<div class="cb-disclaimer">AI-generated heuristic guidance — not an '
                    "official acceptance probability.</div>",
                    unsafe_allow_html=True,
                )

# ================= Q&A TAB =================
with tab_qa:
    opp = st.session_state.opportunity
    if not opp:
        st.info("Analyze an opportunity in the **📄 Analyze** tab first.")
    else:
        st.write(f"Ask anything about: **{opp.get('title', 'this opportunity')}**")

        st.caption("Try a quick question:")
        chip_cols = st.columns(3)
        for i, q in enumerate(QA_EXAMPLE_QUESTIONS):
            with chip_cols[i % 3]:
                if st.button(q, key=f"chip_{i}", use_container_width=True):
                    st.session_state.pending_question = q

        question = st.text_input(
            "Your question",
            value=st.session_state.pending_question or "",
            key="qa_input",
            placeholder="e.g. Can first-year students participate?",
        )
        ask_clicked = st.button("Ask", key="qa_ask_btn")

        if ask_clicked:
            error = validate_question(question)
            if error:
                st.warning(error)
            else:
                with st.spinner("Looking through the notice..."):
                    try:
                        answer = ask_about_notice(st.session_state.notice_input, opp, question)
                        st.session_state.qa_history.append({"question": question, "answer": answer})
                        st.session_state.pending_question = None
                        st.rerun()
                    except AIServiceError as e:
                        st.error(str(e))

        for entry in reversed(st.session_state.qa_history):
            with st.container(border=True):
                st.markdown(f"**You:** {entry['question']}")
                st.markdown(f"**CampusBridge:** {entry['answer']}")

# ================= SAVED TAB =================
with tab_saved:
    st.caption(
        "Saved locally via SQLite for this session/deployment — not guaranteed to "
        "persist across a Streamlit Cloud restart."
    )
    try:
        saved = list_saved_opportunities()
    except Exception as e:
        saved = []
        st.error(f"Couldn't load saved opportunities right now. ({e})")

    if not saved:
        st.info("No saved opportunities yet. Analyze one and click **Save this opportunity**.")
    else:
        for row in saved:
            with st.container(border=True):
                st.markdown(f"**{esc(row['title'])}**")
                st.caption(esc(row["organization"]))
                st.write(f"Type: {row['opportunity_type']} · Deadline: {row['deadline']}")
                if row.get("summary"):
                    st.write(row["summary"])
                if st.button("Delete", key=f"del_{row['id']}"):
                    try:
                        delete_opportunity(row["id"])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Couldn't delete this entry right now. ({e})")

# ================= ABOUT TAB =================
with tab_about:
    st.markdown(f"""
### {APP_NAME}
*{APP_TAGLINE}*

Students constantly receive internships, hackathons, scholarships, fellowships,
placement notices, competitions, workshops, and university circulars — often
too long, poorly structured, or written in unfamiliar language.

**CampusBridge AI** turns any opportunity notice into a structured, actionable
summary: what it is, whether you're eligible, what's required, when it's due,
and what to do next — in your own language.

**What it does:**
- Analyzes opportunity notices into structured action cards
- Checks personal eligibility against stated requirements
- Explains opportunities in Simple English, Telugu, Hindi, Gujarati, or Tamil
- Answers notice-grounded questions
- Gives a qualitative AI Opportunity Fit Estimate
- Saves opportunities for later

**Built with:** Python, Streamlit, SQLite, and Featherless.ai for LLM inference.

CampusBridge provides AI-assisted guidance. Always verify final eligibility and
deadlines with the official organizer.
""")
