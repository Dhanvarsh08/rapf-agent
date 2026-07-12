
import streamlit as st
from fpdf import FPDF
import io
from datetime import datetime
import pandas as pd
import re
import time
import json
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(
    page_title="RAPF - Requirements Analyser",
    page_icon="📋",
    layout="wide"
)

st.title("RAPF - Requirements-Aware Prompting Framework")
st.markdown("""
Paste your software requirements below. RAPF will check if they\'re ready to build — or flag what needs fixing first.  
👈 **Are you new here? Check out the sidebar to learn how it works.**
""")

st.sidebar.markdown("""
# 📋 RAPF
### Requirements-Aware Prompting Framework
---
""")

st.sidebar.markdown("""
> *Ever asked an LLM to implement a vague requirement and got confidently wrong code back?*  
> **That's the problem RAPF solves.**
""")

st.sidebar.markdown("""
---
### 🔍 How it works

RAPF checks if a requirement is **ready to build** — or still needs work.

When a requirement is vague or incomplete, handing it to a developer just produces 
confidently wrong code. RAPF catches that **before** implementation begins.

Instead of guessing, the LLM generates a **structured defect report** — telling you 
exactly what's missing, ambiguous, or untestable. Fix the requirement first, 
then build.

Think of it as a **quality gate**: pass → implement, fail → report.
""")

st.sidebar.markdown("""
---
### 📊 Quality Checks (ISO 29148)

Each requirement is scored **1–5** on four dimensions:

| | Attribute | What it asks |
|---|---|---|
| **U** | Unambiguity | Is it clear? Could it mean two things? |
| **C** | Completeness | Does it have everything a developer needs? |
| **V** | Verifiability | Can you write a test for it? |
| **S** | Consistency | Does it contradict itself? |

Score **4 or 5** = ready to build. Below 4 = needs work first.
""")

st.sidebar.markdown("""
---
### ⚡ Policy Directives

🟢 **U≥4 AND V≥4** → `IMPLEMENT`  
The LLM writes code.

🔴 **Otherwise** → `REPORT_ONLY`  
The LLM writes a defect report.
""")

st.sidebar.markdown("""
---
### 💡 Why it matters

Most LLMs will attempt to implement *any* requirement — even ones that are 
too vague to build correctly.

RAPF stops that. It catches bad requirements **before** they waste 
developer time, and tells you exactly what to fix.
""")

st.sidebar.markdown("""
---
### 👩‍💻 Built by
**Dhanvarshinie Rajan**  
M.Sc. Software Engineering & Management  
Chalmers & University of Gothenburg · 2026  
[🌐 Portfolio](https://dhanvarshinie.lovable.app/)
""")

def generate_html_report(results_df, run_mode):
    """Generate a clean HTML report explaining what RAPF did."""

    total = len(results_df)
    implement = int(results_df["Exec Flag"].sum()) if "Exec Flag" in results_df.columns else 0
    report_only = total - implement
    diagnostic = int((results_df["RAPF Behaviour"] == "Diagnostic").sum()) if "RAPF Behaviour" in results_df.columns else 0
    implementation_count = int((results_df["RAPF Behaviour"] == "Implementation").sum()) if "RAPF Behaviour" in results_df.columns else 0
    generated_at = datetime.now().strftime("%d %B %Y, %H:%M")

    rows_html = ""
    for i, row in results_df.iterrows():
        behaviour = str(row.get("RAPF Behaviour", "Unknown"))
        policy = str(row.get("Policy", "Unknown"))
        req = str(row.get("Requirement", ""))
        u = row.get("U", "?")
        c = row.get("C", "?")
        v = row.get("V", "?")
        s = row.get("S", "?")
        arch = str(row.get("Archetype", "?"))
        what = str(row.get("What happened?", ""))
        output = str(row.get("RAPF Output", ""))[:600]

        if behaviour == "Diagnostic":
            badge_color = "#dc3545"
            badge_text = "DEFECT REPORT"
            card_border = "#dc3545"
        else:
            badge_color = "#28a745"
            badge_text = "IMPLEMENTED"
            card_border = "#28a745"

        rows_html += f"""
        <div style="border-left: 4px solid {card_border}; background: #f8f9fa; padding: 16px; margin-bottom: 16px; border-radius: 4px;">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                <span style="background:{badge_color}; color:white; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:bold;">{badge_text}</span>
                <span style="font-weight:600; font-size:14px;">{req}</span>
            </div>
            <div style="display:flex; gap:12px; margin-bottom:8px; flex-wrap:wrap;">
                <span style="background:#e9ecef; padding:3px 8px; border-radius:4px; font-size:12px;"><b>U</b> {u}</span>
                <span style="background:#e9ecef; padding:3px 8px; border-radius:4px; font-size:12px;"><b>C</b> {c}</span>
                <span style="background:#e9ecef; padding:3px 8px; border-radius:4px; font-size:12px;"><b>V</b> {v}</span>
                <span style="background:#e9ecef; padding:3px 8px; border-radius:4px; font-size:12px;"><b>S</b> {s}</span>
                <span style="background:#e9ecef; padding:3px 8px; border-radius:4px; font-size:12px;">Archetype: {arch}</span>
                <span style="background:#e9ecef; padding:3px 8px; border-radius:4px; font-size:12px;">Policy: {policy}</span>
            </div>
            <div style="font-size:13px; color:#555; font-style:italic; margin-bottom:8px;">{what}</div>
            <details>
                <summary style="cursor:pointer; font-size:13px; color:#1a4f7a; font-weight:600;">View LLM Output</summary>
                <pre style="background:#fff; border:1px solid #dee2e6; padding:12px; border-radius:4px; font-size:12px; white-space:pre-wrap; margin-top:8px;">{output}</pre>
            </details>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAPF Requirements Analysis Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 40px 20px; color: #212529; }}
        h1 {{ color: #1a4f7a; border-bottom: 3px solid #1a4f7a; padding-bottom: 12px; }}
        h2 {{ color: #1a4f7a; margin-top: 32px; }}
        .subtitle {{ color: #6c757d; font-size: 14px; margin-top: -8px; margin-bottom: 24px; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin: 16px 0; }}
        .summary-card {{ background: #f0f4f8; border-radius: 8px; padding: 16px; text-align: center; }}
        .summary-card .number {{ font-size: 32px; font-weight: bold; color: #1a4f7a; }}
        .summary-card .label {{ font-size: 12px; color: #6c757d; margin-top: 4px; }}
        .attr-table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
        .attr-table th {{ background: #1a4f7a; color: white; padding: 8px 12px; text-align: left; }}
        .attr-table td {{ padding: 8px 12px; border-bottom: 1px solid #dee2e6; }}
        .attr-table tr:nth-child(even) {{ background: #f8f9fa; }}
        .footer {{ margin-top: 40px; padding-top: 16px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; text-align: center; }}
    </style>
</head>
<body>
    <h1>RAPF Requirements Analysis Report</h1>
    <div class="subtitle">Generated: {generated_at} &nbsp;|&nbsp; Requirements-Aware Prompting Framework &nbsp;|&nbsp; Chalmers & University of Gothenburg</div>

    <h2>What is RAPF?</h2>
    <p>RAPF (Requirements-Aware Prompting Framework) checks whether software requirements are ready to implement. Instead of blindly asking an LLM to build something from a vague requirement, RAPF first grades each requirement on four ISO/IEC/IEEE 29148 quality attributes, then either implements it or generates a defect report explaining what needs to be fixed first.</p>

    <h2>How It Works</h2>
    <ol>
        <li>Each requirement is graded on four quality dimensions (U, C, V, S) scored 1-5.</li>
        <li>A compiled-constraints prompt is built dynamically from those scores.</li>
        <li>If U&ge;4 AND V&ge;4: policy = <b>IMPLEMENT</b> (LLM writes Python code).</li>
        <li>Otherwise: policy = <b>REPORT_ONLY</b> (LLM writes a structured defect report).</li>
        <li>Output is classified: Implementation, Diagnostic, Assumption, Refusal, or Other.</li>
    </ol>

    <h2>Quality Attributes (ISO/IEC/IEEE 29148)</h2>
    <table class="attr-table">
        <tr><th>Score</th><th>Attribute</th><th>What it checks</th></tr>
        <tr><td><b>U</b></td><td>Unambiguity</td><td>Is it clear? Can it only be interpreted one way?</td></tr>
        <tr><td><b>C</b></td><td>Completeness</td><td>Does it contain everything a developer needs?</td></tr>
        <tr><td><b>V</b></td><td>Verifiability</td><td>Can it be tested or measured objectively?</td></tr>
        <tr><td><b>S</b></td><td>Consistency</td><td>Does it contradict itself or other requirements?</td></tr>
    </table>
    <p>Score <b>4 or 5</b> = ready to build. Below 4 = needs work before implementation.</p>

    <h2>Analysis Summary</h2>
    <div class="summary-grid">
        <div class="summary-card"><div class="number">{total}</div><div class="label">Total Analyzed</div></div>
        <div class="summary-card"><div class="number">{implement}</div><div class="label">IMPLEMENT</div></div>
        <div class="summary-card"><div class="number">{report_only}</div><div class="label">REPORT_ONLY</div></div>
        <div class="summary-card"><div class="number">{implementation_count}</div><div class="label">Implemented</div></div>
        <div class="summary-card"><div class="number">{diagnostic}</div><div class="label">Defect Reports</div></div>
    </div>

    <h2>Individual Requirement Results</h2>
    {rows_html}

    <div class="footer">
        Generated by RAPF-Agent &nbsp;|&nbsp; Built by <b>Dhanvarshinie Rajan</b> &nbsp;|&nbsp;
        M.Sc. Software Engineering and Management &nbsp;|&nbsp;
        Chalmers University of Technology &amp; University of Gothenburg 2026 &nbsp;|&nbsp;
        <a href="https://dhanvarshinie.lovable.app/">Portfolio</a>
    </div>
</body>
</html>"""

    return html

def preprocess_requirement(req_text):
    """
    Clean requirement text before grading:
    1. Strip section numbers (e.g. 7.3.4, 3.2.1.a)
    2. Warn if requirement is too long
    Returns cleaned text.
    """
    import re
    # Strip leading section numbers like "7.3.4", "3.2.1.a", "REQ-001"
    cleaned = re.sub(r"^[\d]+[\d\.\-a-zA-Z]*\s+", "", req_text.strip())
    # Also strip formats like "FR-01:", "REQ001:"
    cleaned = re.sub(r"^[A-Z]{1,5}[-_]?\d+[:\.\s]+", "", cleaned)
    return cleaned.strip()

def split_compound_requirement(req_text):
    """
    Split compound requirements joined by 'and' or ';' into separate ones.
    e.g. "The system shall login users and generate reports" -> two requirements
    Only splits on clear compound patterns to avoid false splits.
    """
    import re
    # Pattern: "shall/must/should X and Y" where Y starts with a verb
    parts = re.split(r"\s+and\s+(?=the\s|a\s|an\s|be\s|allow\s|enable\s|provide\s|support\s|ensure\s|generate\s|display\s|send\s|store\s|process\s)", req_text, flags=re.IGNORECASE)
    if len(parts) > 1:
        # Carry the subject/verb from first part into subsequent parts
        prefix = re.match(r"^(the\s+\w+\s+(?:shall|must|should|will)\s+)", parts[0], re.IGNORECASE)
        result = [parts[0]]
        for part in parts[1:]:
            if prefix:
                result.append(prefix.group(1) + part)
            else:
                result.append(part)
        return result
    return [req_text]

def validate_requirement(req_text):
    """
    Check requirement length and return warning if too long.
    """
    if len(req_text) > 500:
        return f"⚠️ This requirement is very long ({len(req_text)} chars). Consider splitting it for better analysis."
    if len(req_text) < 10:
        return "⚠️ This requirement is very short — it may not contain enough information to grade accurately."
    return None

def grade_requirement(req_text):
    prompt = f"""Grade this software requirement on four ISO/IEC/IEEE 29148 quality attributes.
Score each from 1 (very poor) to 5 (excellent).

REQUIREMENT: {req_text}

Scoring guide:
- Unambiguity (U): Can it be interpreted only one way? (1=very ambiguous, 5=completely clear)
- Completeness (C): Does it contain all necessary information? (1=major gaps, 5=fully complete)
- Verifiability (V): Can it be tested/measured? (1=untestable, 5=clearly testable)
- Consistency (S): Does it contradict itself? (1=contradictory, 5=fully consistent)

Return ONLY minified JSON, no preamble:
{{"U":score,"C":score,"V":score,"S":score}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=30
        )
        scores = json.loads(response.choices[0].message.content.strip())
        return float(scores["U"]), float(scores["C"]), float(scores["V"]), float(scores["S"])
    except json.JSONDecodeError:
        st.warning("⚠️ Could not parse quality scores for one requirement — using default scores (3,3,3,4).")
        return 3.0, 3.0, 3.0, 4.0
    except Exception as e:
        if "rate_limit" in str(e).lower():
            st.error("⏳ Groq rate limit hit — please wait a few seconds and try again.")
        else:
            st.error(f"❌ Error grading requirement: {str(e)[:100]}")
        return 3.0, 3.0, 3.0, 4.0

def build_compiled_prompt(req_text, u, c, v, s):
    exec_flag = (u >= 4) and (v >= 4)
    policy = "IMPLEMENT" if exec_flag else "REPORT_ONLY"
    constraints = []
    if u >= 4:
        constraints.append("One interpretation only. Do not introduce alternatives.")
    else:
        constraints.append("AMBIGUOUS: List ambiguities. Do not guess. Do not implement.")
    if c >= 4:
        constraints.append("Implement exactly what is stated. Do not add unstated features.")
    else:
        constraints.append("MISSING: List missing information required for implementation.")
    if v >= 4:
        constraints.append("Keep behaviour deterministic and testable.")
    else:
        constraints.append("NOT_VERIFIABLE: List unverifiable claims. State what cannot be tested.")
    if s >= 4:
        constraints.append("Maintain internal consistency with stated requirements.")
    else:
        constraints.append("INCONSISTENT: Flag any contradictory or conflicting statements.")
    constraint_block = "\n".join([f"- {c_}" for c_ in constraints])
    if exec_flag:
        task = "Implement the requirement as a Python function."
        output_instruction = "Output Python code only. No markdown. No print statements."
    else:
        task = "You cannot implement this requirement as stated. Generate a structured defect report instead."
        output_instruction = """Output a structured defect report only. No code.
Use this format:
MISSING: <list missing information>
AMBIGUOUS: <list ambiguous terms>
NOT_VERIFIABLE: <list unverifiable claims>"""
    return f"""You are a professional software engineer.

Requirement:
{req_text}

Task: {task}

Constraints:
{constraint_block}

Policy: {policy}

{output_instruction}""", exec_flag, policy

def build_baseline_prompt(req_text):
    return f"""You are a professional software engineer.

Requirement:
{req_text}

Task: Implement the requirement as a Python function. Output code only."""

def classify_output(text):
    text_lower = text.lower()
    has_code = any(m in text for m in ["def ", "class ", "```"])
    gpt_diag = any(m in text_lower for m in ["missing:", "ambiguous:", "not_verifiable:", "not verifiable:"])
    claude_md = bool(re.search(r"#{1,4}\s*(missing|ambiguous|not.?verifiable)", text_lower))
    claude_tbl = bool(re.search(r"\|\s*(missing|ambiguous|not.?verifiable)\s*\|", text_lower))
    prose = [
        "the requirement lacks","is not verifiable","it is unclear","insufficient detail",
        "structured defect report","cannot be measured","no clear","not specified",
        "undefined","vague","cannot be tested","missing information","ambiguous term",
        "lacks specificity","no measurable","not quantified","unclear what","does not specify"
    ]
    claude_prose = (not has_code) and any(p in text_lower for p in prose)
    if gpt_diag or claude_md or claude_tbl or claude_prose:
        return "Diagnostic"
    elif has_code:
        return "Implementation"
    elif any(p in text_lower for p in ["assume ", "assuming "]):
        return "Assumption"
    elif any(p in text_lower for p in ["cannot ", "unable to"]):
        return "Refusal"
    return "Other"

def run_analysis(requirements, run_mode):
    results = []
    total = len(requirements)
    progress = st.progress(0)
    status = st.empty()

    # Pre-process: split compound requirements first
    processed_requirements = []
    for req in requirements:
        cleaned = preprocess_requirement(req)
        splits = split_compound_requirement(cleaned)
        processed_requirements.extend(splits)

    total = len(processed_requirements)

    for i, req_text in enumerate(processed_requirements):
        status.text(f"Step 1/2 - Grading requirement {i+1}/{total}...")

        # Validate length
        warning = validate_requirement(req_text)
        if warning:
            st.warning(f"Requirement {i+1}: {warning}")

        u, c, v, s = grade_requirement(req_text)
        time.sleep(0.2)

        exec_flag = (u >= 4) and (v >= 4)
        archetype_parts = []
        if u < 4: archetype_parts.append("Ambiguous")
        if c < 4: archetype_parts.append("Incomplete")
        if v < 4: archetype_parts.append("NonVerifiable")
        if s < 4: archetype_parts.append("Inconsistent")
        archetype = "+".join(archetype_parts) if archetype_parts else "HighQuality"

        row = {
            "Requirement": req_text[:100] + "..." if len(req_text) > 100 else req_text,
            "U": u, "C": c, "V": v, "S": s,
            "Archetype": archetype,
            "Exec Flag": exec_flag,
        }

        if run_mode in ["Compiled-Constraints only", "Compare both"]:
            status.text(f"Step 2/2 - Running RAPF on requirement {i+1}/{total}...")
            prompt, _, policy = build_compiled_prompt(req_text, u, c, v, s)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            output = response.choices[0].message.content
            row["Policy"] = policy
            row["RAPF Behaviour"] = classify_output(output)
            row["RAPF Output"] = output[:400]
            time.sleep(0.3)

        if run_mode == "Compare both":
            status.text(f"Step 2/2 - Running Baseline on requirement {i+1}/{total}...")
            b_prompt = build_baseline_prompt(req_text)
            b_response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": b_prompt}],
                temperature=0
            )
            b_output = b_response.choices[0].message.content
            row["Baseline Behaviour"] = classify_output(b_output)
            row["Baseline Output"] = b_output[:400]
            time.sleep(0.3)

        results.append(row)
        progress.progress((i + 1) / total)

    status.empty()
    progress.empty()
    return pd.DataFrame(results)

# Input section
st.header("Input Requirements")

# Try it button with sample requirements
sample_requirements = [
    "The system shall respond to all user queries within 2 seconds under normal load.",
    "The user should be able to login easily using their credentials.",
    "The system must generate reports for the management team on a regular basis.",
    "Citizens can register their complaints with police and then based on the evidence, facts and following investigation, police shall take the complaint forward.",
    "The application shall provide a secure and reliable way to store user data."
]

if st.button("✨ Try with sample requirements"):
    st.session_state["sample_loaded"] = True
    st.session_state["text_input"] = "\n".join(sample_requirements)

if st.session_state.get("sample_loaded"):
    st.success("✅ 5 sample requirements loaded! You can edit them in the box below or hit **Run RAPF Analysis** to go.")

input_method = st.radio("Input method", ["Paste text (one per line)", "Upload plain text CSV"])

requirements = []

if input_method == "Paste text (one per line)":
    # Pre-populate with sample if loaded
    if st.session_state.get("sample_loaded"):
        default = "\n".join(sample_requirements)
    else:
        default = ""

    text_input = st.text_area(
        "Enter requirements — one per line",
        value=default,
        height=250,
        placeholder="The system shall respond within 2 seconds.\nThe user should be able to login.\nThe system must generate reports."
    )
    if text_input.strip():
        requirements = [r.strip() for r in text_input.strip().split("\n") if r.strip()]
        st.success(f"{len(requirements)} requirement(s) ready")

else:
    uploaded = st.file_uploader("Upload CSV with a column named requirement_text", type="csv")
    if uploaded:
        df = pd.read_csv(uploaded)

        # Auto-detect requirement column
        req_col = None
        preferred = ["requirement_text", "requirement", "Requirement", "text", "Text", "description", "Description"]
        for col in preferred:
            if col in df.columns:
                req_col = col
                break

        # If none found, pick the longest text column
        if not req_col:
            text_cols = df.select_dtypes(include="object").columns.tolist()
            if text_cols:
                req_col = max(text_cols, key=lambda c: df[c].dropna().str.len().mean())
                st.info(f"No standard column found — using \"{req_col}\" as the requirements column. Rename it to \"requirement_text\" for best results.")

        if req_col:
            max_n = st.slider("Max requirements to analyse", 5, 30, 10)
            requirements = df[req_col].dropna().tolist()[:max_n]
            st.success(f"Loaded {len(requirements)} requirements from column \"{req_col}\"")
            st.dataframe(df[[req_col]].head(max_n), use_container_width=True)
        else:
            st.error("Could not find any text column in this CSV. Please check your file.")

# Run
# Always populate requirements from session state if sample was loaded
if st.session_state.get("sample_loaded") and not requirements:
    requirements = sample_requirements

if requirements:
    run_mode = st.radio(
        "Run mode",
        ["Compiled-Constraints only", "Compare both"],
        help="Compare both runs baseline and RAPF side by side — takes twice as long"
    )

    if st.button("Run RAPF Analysis", type="primary"):
        st.header("Results")
        results_df = run_analysis(requirements, run_mode)

        # Grading summary
        st.subheader("Step 1: Requirement Quality Grading (ISO 29148)")
        grade_cols = ["Requirement", "U", "C", "V", "S", "Archetype", "Policy"]
        st.dataframe(results_df[grade_cols], use_container_width=True)

        exec_count = int(results_df["Exec Flag"].sum())
        non_exec = len(results_df) - exec_count

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Requirements", len(results_df))
        c2.metric("✅ Executable (IMPLEMENT)", exec_count)
        c3.metric("🔴 Non-executable (REPORT_ONLY)", non_exec)

        # Pie chart
        chart_data = pd.DataFrame({
            "Policy": ["IMPLEMENT", "REPORT_ONLY"],
            "Count": [exec_count, non_exec]
        })
        st.markdown("**Policy Distribution**")
        st.bar_chart(chart_data.set_index("Policy"))

        # Behaviour results
        if "RAPF Behaviour" in results_df.columns:
            st.subheader("Step 2: RAPF Behaviour Classification")
            behaviour_cols = ["Requirement", "Policy", "RAPF Behaviour"]

            def explain_behaviour(row):
                if row["Policy"] == "IMPLEMENT" and row["RAPF Behaviour"] == "Diagnostic":
                    return "⚠️ Executable but incomplete — LLM flagged missing info while implementing"
                elif row["Policy"] == "IMPLEMENT" and row["RAPF Behaviour"] == "Implementation":
                    return "✅ Requirement is ready — LLM implemented it"
                elif row["Policy"] == "REPORT_ONLY" and row["RAPF Behaviour"] == "Diagnostic":
                    return "🔴 Not ready to build — LLM generated a defect report"
                elif row["Policy"] == "REPORT_ONLY" and row["RAPF Behaviour"] == "Implementation":
                    return "⚠️ Policy said REPORT_ONLY but LLM implemented anyway"
                else:
                    return row["RAPF Behaviour"]

            results_df["What happened?"] = results_df.apply(explain_behaviour, axis=1)

            if "Baseline Behaviour" in results_df.columns:
                behaviour_cols = ["Requirement", "Baseline Behaviour", "Policy", "RAPF Behaviour", "What happened?"]
            else:
                behaviour_cols = ["Requirement", "Policy", "RAPF Behaviour", "What happened?"]

            st.dataframe(results_df[behaviour_cols], use_container_width=True)

            # Metrics
            if "Baseline Behaviour" in results_df.columns:
                b_diag = (results_df["Baseline Behaviour"] == "Diagnostic").sum()
                r_diag = (results_df["RAPF Behaviour"] == "Diagnostic").sum()
                n = len(results_df)
                st.subheader("Key Finding: Diagnostic Rate Shift")
                m1, m2, m3 = st.columns(3)
                m1.metric("Baseline Diagnostic Rate", f"{b_diag/n*100:.0f}%")
                m2.metric("RAPF Diagnostic Rate", f"{r_diag/n*100:.0f}%")
                m3.metric("Shift", f"+{(r_diag-b_diag)/n*100:.0f}%")
            else:
                rapf_dist = results_df["RAPF Behaviour"].value_counts()
                cols = st.columns(5)
                for col, beh in zip(cols, ["Implementation","Diagnostic","Assumption","Refusal","Other"]):
                    count = rapf_dist.get(beh, 0)
                    col.metric(beh, count, f"{count/len(results_df)*100:.0f}%")

            # Detailed outputs
            st.subheader("Detailed Outputs")
            for _, row in results_df.iterrows():
                label = f"[{row.get('RAPF Behaviour', '')}] {row['Requirement'][:80]}"
                with st.expander(label):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("U", row["U"])
                    c2.metric("C", row["C"])
                    c3.metric("V", row["V"])
                    c4.metric("S", row["S"])
                    st.markdown(f"**Archetype:** {row['Archetype']}")
                    st.markdown(f"**Policy:** {row.get('Policy', 'N/A')}")
                    if "Baseline Output" in results_df.columns:
                        st.markdown("**Baseline Output:**")
                        st.code(row.get("Baseline Output", ""), language="text")
                    st.markdown("**RAPF Output:**")
                    st.code(row.get("RAPF Output", ""), language="text")

                    # Show compiled prompt
                    u, c, v, s = row["U"], row["C"], row["V"], row["S"]
                    exec_flag = (u >= 4) and (v >= 4)
                    constraints = []
                    constraints.append("One interpretation only. Do not introduce alternatives." if u >= 4 else "AMBIGUOUS: List ambiguities. Do not guess. Do not implement.")
                    constraints.append("Implement exactly what is stated. Do not add unstated features." if c >= 4 else "MISSING: List missing information required for implementation.")
                    constraints.append("Keep behaviour deterministic and testable." if v >= 4 else "NOT_VERIFIABLE: List unverifiable claims. State what cannot be tested.")
                    constraints.append("Maintain internal consistency with stated requirements." if s >= 4 else "INCONSISTENT: Flag any contradictory or conflicting statements.")
                    constraint_block = "\n".join([f"- {c_}" for c_ in constraints])
                    task = "Implement the requirement as a Python function." if exec_flag else "You cannot implement this requirement as stated. Generate a structured defect report instead."
                    output_instruction = "Output Python code only. No markdown. No print statements." if exec_flag else "Output a structured defect report only. No code.\nMISSING: ...\nAMBIGUOUS: ...\nNOT_VERIFIABLE: ..."
                    compiled_prompt = f"""You are a professional software engineer.

Requirement:
{row["Requirement"]}

Task: {task}

Constraints:
{constraint_block}

Policy: {row.get("Policy", "N/A")}

{output_instruction}"""
                    with st.expander("🔍 View compiled prompt sent to LLM"):
                        st.code(compiled_prompt, language="text")

        # Download
        st.markdown("---")
        st.subheader("Download Results")
        dl_col1, dl_col2 = st.columns(2)

        with dl_col1:
            st.download_button(
                "📥 Download CSV",
                results_df.to_csv(index=False),
                "rapf_results.csv",
                "text/csv",
                help="Raw results in spreadsheet format"
            )

        with dl_col2:
            try:
                html_report = generate_html_report(results_df, run_mode)
                st.download_button(
                    "📄 Download HTML Report",
                    html_report,
                    "rapf_report.html",
                    "text/html",
                    help="Full report — open in any browser, easy to read and share"
                )
            except Exception as e:
                st.error(f"Could not generate report: {str(e)[:100]}")
