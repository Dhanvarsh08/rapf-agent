# RAPF-Agent — Requirements-Aware Prompting Framework

**Live demo:** https://rapf-agent-by-dhanvarshinie.streamlit.app/

A deployable web app implementing the Requirements-Aware Prompting Framework (RAPF) from my M.Sc. thesis at Chalmers University of Technology and the University of Gothenburg.

---

## What it does

Most LLMs will attempt to implement *any* requirement — even ones that are too vague, incomplete, or ambiguous to build correctly. RAPF stops that.

The app checks whether a software requirement is **ready to build** before asking an LLM to implement it. Requirements that pass get implemented. Requirements that don't get a structured defect report explaining exactly what needs to be fixed first.

---

## Key thesis finding

| Condition | Diagnostic Rate |
|---|---|
| Baseline prompt | 0% |
| RAPF compiled-constraints | 63–73% |

*Same model. Same requirement. Just a smarter prompt.*  
Validated on the PURE corpus (2,503 real-world software requirements), using GPT-4o-mini.

---

## How it works

1. Paste or upload your software requirements
2. Each requirement is automatically graded on four ISO/IEC/IEEE 29148 quality attributes:
   - **U — Unambiguity:** Is it clear? Can it only be interpreted one way?
   - **C — Completeness:** Does it contain everything a developer needs?
   - **V — Verifiability:** Can it be tested or measured?
   - **S — Consistency:** Does it contradict itself or other requirements?
3. A compiled-constraints prompt is built dynamically from those scores
4. If U≥4 AND V≥4 → policy = `IMPLEMENT` (LLM writes Python code)
5. Otherwise → policy = `REPORT_ONLY` (LLM generates a structured defect report)
6. LLM output is classified: Implementation, Diagnostic, Assumption, Refusal, or Other

---

## Pre-processing

The app automatically handles:
- **Section numbers** — strips "7.3.4" style prefixes before grading
- **Compound requirements** — splits "shall X and Y" into separate requirements
- **Long requirements** — warns if a requirement exceeds 300 characters
- **CSV auto-detection** — finds the requirements column automatically

---

## Tech stack

| Component | Tool |
|---|---|
| LLM inference | Groq API (Llama 3.1 8B Instant) |
| Embeddings | HuggingFace sentence-transformers |
| Vector store | ChromaDB |
| Orchestration | LangChain |
| UI | Streamlit |
| Deployment | Streamlit Community Cloud |

**Cost to run: $0** — entirely free tier.

---

## Run locally

```bash
git clone https://github.com/Dhanvarsh08/rapf-agent.git
cd rapf-agent
pip install -r requirements.txt
cp .env.example .env
# Add your Groq API key to .env
streamlit run app.py
```

Get a free Groq API key at https://console.groq.com

---

## Known limitations

- English requirements only
- Inter-requirement dependencies not handled (each requirement graded in isolation)
- Non-functional requirements (performance, security) may be graded less accurately
- Thesis finding (63–73%) validated on GPT-4o-mini; this app uses Llama 3.1 8B via Groq

---

## About

Built as part of my M.Sc. thesis:  
**"A Requirements-Aware Prompting Framework for LLM-Based Code Generation"**  
Chalmers University of Technology & University of Gothenburg, 2026  
Grounded in ISO/IEC/IEEE 29148:2018

**Author:** Dhanvarshinie Rajan  
**Portfolio:** https://dhanvarshinie.lovable.app/  
**LinkedIn:** https://www.linkedin.com/in/dhanvarshinie-rajan/

---

## Citation

If you use this work, please cite:

> Rajan, D. (2026). *A Requirements-Aware Prompting Framework for LLM-Based Code Generation*. 
> M.Sc. Thesis, Chalmers University of Technology & University of Gothenburg.
