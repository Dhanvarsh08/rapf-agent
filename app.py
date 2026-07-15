
import streamlit as st
import chromadb
from sentence_transformers import SentenceTransformer
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

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("GROQ_API_KEY not found. Please add it to your Streamlit secrets or .env file.")
    st.stop()

client = Groq(api_key=api_key)

@st.cache_resource
def load_rag_components():
    """Load ChromaDB and embedding model once at startup."""
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    chroma_client = chromadb.Client()
    collection = chroma_client.create_collection("iso29148_criteria")

    iso_criteria = [
        {"id":"U1","attribute":"Unambiguity","text":"The requirement admits exactly one valid interpretation. A requirement is unambiguous if it can only be read in one way by all stakeholders."},
        {"id":"U2","attribute":"Unambiguity","text":"Lexical ambiguity arises when a term admits multiple meanings. For example, secure can mean protected or fastened. Requirements must avoid such terms without qualification."},
        {"id":"U3","attribute":"Unambiguity","text":"Pragmatic ambiguity arises when interpretation depends on unstated contextual assumptions. Requirements should be self-contained and not rely on implicit context."},
        {"id":"U4","attribute":"Unambiguity","text":"Syntactic ambiguity occurs when sentence structure allows multiple parse trees. Requirements should use simple, unambiguous sentence structures."},
        {"id":"U5","attribute":"Unambiguity","text":"A requirement scores low on unambiguity when multiple valid interpretations exist, when subjective terms are used without measurable criteria, or when the subject of the requirement is unclear."},
        {"id":"C1","attribute":"Completeness","text":"All necessary information for implementation is explicitly specified. A complete requirement contains all the information a developer needs without having to infer or assume missing details."},
        {"id":"C2","attribute":"Completeness","text":"Incompleteness arises when essential conditions, constraints, or edge cases are omitted, forcing implementers to infer missing information."},
        {"id":"C3","attribute":"Completeness","text":"A requirement is incomplete when it omits necessary constraints, preconditions, postconditions, error handling, or operational boundaries required for correct implementation."},
        {"id":"C4","attribute":"Completeness","text":"Requirements should specify what the system shall do, under what conditions, with what inputs, producing what outputs. Missing any of these elements indicates incompleteness."},
        {"id":"C5","attribute":"Completeness","text":"A requirement scores low on completeness when a developer would need to make assumptions to implement it, when edge cases are not covered, or when success criteria are not defined."},
        {"id":"V1","attribute":"Verifiability","text":"The requirement can be tested against observable behaviour. A verifiable requirement has a clear, measurable criterion that can be evaluated through repeatable tests."},
        {"id":"V2","attribute":"Verifiability","text":"Non-verifiability occurs when requirements are expressed in subjective or qualitative terms that cannot be evaluated through deterministic testing."},
        {"id":"V3","attribute":"Verifiability","text":"A requirement is verifiable if it can be evaluated against observable system behaviour using repeatable tests. Requirements using words like fast, easy, reliable, or user-friendly without measurable criteria are not verifiable."},
        {"id":"V4","attribute":"Verifiability","text":"A verifiable requirement specifies a measurable outcome: a response time in milliseconds, an accuracy percentage, a maximum error rate, or a specific observable behaviour that can be confirmed through testing."},
        {"id":"V5","attribute":"Verifiability","text":"A requirement scores low on verifiability when it contains subjective terms without measurement criteria, when success cannot be determined through testing, or when the expected output is not observable."},
        {"id":"S1","attribute":"Consistency","text":"The requirement does not conflict with other requirements or assumptions. A consistent requirement is internally coherent and compatible with the broader system specification."},
        {"id":"S2","attribute":"Consistency","text":"Inconsistency emerges when requirements contradict each other or rely on incompatible assumptions."},
        {"id":"S3","attribute":"Consistency","text":"A requirement is internally inconsistent when it contains contradictory statements within itself, such as requiring both exclusive and non-exclusive access, or both mandatory and optional behaviour."},
        {"id":"S4","attribute":"Consistency","text":"Consistency is a document-level property. A requirement may be internally consistent but conflict with other requirements in the same specification."},
        {"id":"S5","attribute":"Consistency","text":"A requirement scores low on consistency when it contradicts itself, uses conflicting terminology, or makes assumptions incompatible with other stated requirements."},
        {"id":"P1","attribute":"Policy","text":"A requirement is executable when both unambiguity and verifiability scores are at or above 4. Under these conditions, the policy directive is IMPLEMENT."},
        {"id":"P2","attribute":"Policy","text":"When a requirement is not executable, the policy directive is REPORT_ONLY. The LLM is instructed to generate a structured defect report rather than implementation code."},
        {"id":"P3","attribute":"Policy","text":"The compiled-constraints prompt augments the baseline with a structured constraint block aligned with ISO 29148 quality attributes. The constraints are tailored to the quality mode of the requirement."},
    ]

    texts = [c["text"] for c in iso_criteria]
    ids = [c["id"] for c in iso_criteria]
    metadatas = [{"attribute": c["attribute"]} for c in iso_criteria]
    embeddings = embedding_model.encode(texts).tolist()

    collection.add(documents=texts, embeddings=embeddings, ids=ids, metadatas=metadatas)
    return embedding_model, collection

embedding_model, iso_collection = load_rag_components()

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
*Ever asked an AI to build something from a vague requirement and got confidently wrong code back?
That's the problem RAPF solves.*
""")

st.sidebar.markdown("""
---
### How it works

RAPF acts as a quality gate before any code gets written.

It reads your requirement, scores it on four quality checks, and makes a decision: 
is this ready to build, or does it need work first?

If it's ready → the AI writes code.  
If it's not → the AI writes a detailed report explaining exactly what's wrong, 
so you can fix the requirement before wasting development time.
""")

st.sidebar.markdown("""
---
### The four quality checks

Each requirement is automatically scored **1–5** on:

| | Attribute | The question it asks |
|---|---|---|
| **U** | Unambiguity | Is it clear? Could a developer interpret it two different ways? |
| **C** | Completeness | Does it contain everything needed to build it? |
| **V** | Verifiability | Can you write a test for it? Is there a measurable outcome? |
| **S** | Consistency | Does it contradict itself or other requirements? |
""")

st.sidebar.markdown("""
---
### The decision rule

RAPF looks at just two scores to decide whether to implement or report:

- If **Unambiguity ≥ 4** and **Verifiability ≥ 4** → the requirement is clear enough 
to understand and specific enough to test → **AI writes code**
- Otherwise → the requirement isn't ready yet → **AI writes a defect report**

*Why just U and V? Because ambiguity makes any implementation wrong by definition, 
and if you can't test it, you'll never know if it was built correctly. 
Completeness and consistency matter too — but they show up in the defect report, 
not the build decision.*
""")

st.sidebar.markdown("""
---
### Why it matters

Most AI tools will attempt to implement any requirement, no matter how vague. 
RAPF doesn't. It catches the problems before they become bugs — and tells you 
exactly what to fix.
""")

st.sidebar.markdown("""
---
### Grading Mode
""")

grading_mode = st.sidebar.radio(
    "Choose grading approach:",
    ["RAG-Enhanced Grading (Recommended)", "Standard Grading"],
    help="RAG-Enhanced retrieves ISO 29148 criteria before grading each requirement"
)

st.sidebar.markdown("""
**Standard Grading**  
The AI grades your requirement based on its own training knowledge of what makes a good software requirement.

**RAG-Enhanced Grading**  
Before grading, the AI retrieves the most relevant quality criteria from an ISO/IEC/IEEE 29148 knowledge base — like giving the AI a reference book to check before scoring. This makes grading more accurate and grounded in the actual standard.

*RAG (Retrieval-Augmented Generation) is a technique where the AI looks up relevant information before generating a response, rather than relying purely on what it learned during training.*
""")

st.sidebar.markdown("""
---
### Built by
**Dhanvarshinie Rajan**  
M.Sc. Software Engineering & Management  
Chalmers University of Technology & University of Gothenburg · 2026  
[Portfolio](https://dhanvarshinie.lovable.app/)
""")

def grade_requirement_rag(req_text):
    """RAG-enhanced grading using ChromaDB + ISO 29148 knowledge base."""
    req_embedding = embedding_model.encode([req_text]).tolist()
    results = iso_collection.query(query_embeddings=req_embedding, n_results=4)
    retrieved_context = ""
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        attr = meta["attribute"]
        retrieved_context += f"\n[{attr}] {doc}"

    prompt = f"""You are a requirements quality auditor trained in ISO/IEC/IEEE 29148.

Grade this software requirement using the following relevant ISO 29148 quality criteria as reference:

RETRIEVED CRITERIA:
{retrieved_context}

REQUIREMENT TO GRADE: {req_text}

Using the criteria above as your reference, score the requirement on:
- U (Unambiguity): one interpretation only (1=very ambiguous, 5=completely clear)
- C (Completeness): all details to implement (1=major gaps, 5=fully complete)
- V (Verifiability): can be tested (1=untestable, 5=clearly testable)
- S (Consistency): no contradictions (1=contradictory, 5=fully consistent)

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
        st.warning("Could not parse RAG grading scores — using defaults.")
        return 3.0, 3.0, 3.0, 4.0
    except Exception as e:
        if "rate_limit" in str(e).lower():
            st.error("Groq rate limit hit — please wait a few seconds and try again.")
        return 3.0, 3.0, 3.0, 4.0

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

        if grading_mode == "RAG-Enhanced Grading (Recommended)":
            u, c, v, s = grade_requirement_rag(req_text)
        else:
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
