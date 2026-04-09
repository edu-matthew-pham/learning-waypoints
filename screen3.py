import streamlit as st
from utils import standards_map, get_prior_chain, generate_pdf


def build_context(selected_codes):
    """Build shared context block for all prompts."""
    hinge_nodes, y_goals, sc_lines, prior_lines = [], [], [], []
    for code in selected_codes:
        if code not in standards_map:
            continue
        std = standards_map[code]
        y_goals.append(f"{code}: {std['y_goal']}")
        for node in std["nodes"]:
            if node["hinge"]:
                hinge_nodes.append(f"- Node {node['id']} ({code}): {node['label']} — {node.get('hinge_reason', '')}")
            sc = node.get("success_criteria", [])
            if sc:
                sc_lines.append(f"Node {node['id']} ({code}) — {node['label']}:")
                for s in sc:
                    sc_lines.append(f"  • {s}")
        chain = get_prior_chain(code)
        if chain:
            prior_lines.append(f"{code} prior pathway:")
            for item in chain:
                prior_lines.append(f"  Year {item['year_level']} · {item['code']} · {item['title']}: {item['y_goal']}")

    return {
        "y_goal_text": "\n".join(y_goals),
        "prior_text": "\n".join(prior_lines) if prior_lines else "No prior pathway found.",
        "hinge_text": "\n".join(hinge_nodes) if hinge_nodes else "None identified",
        "sc_text": "\n".join(sc_lines) if sc_lines else "None defined",
    }


def build_assessment_prompt(selected_codes, assessment_type, existing_task, existing_summary):
    ctx = build_context(selected_codes)

    # Adapt instructions based on what exists
    task_section = ""
    if existing_task.strip():
        task_section = f"""EXISTING TASK
──────────────────────────────────
{existing_task}

OUTPUT 1 — REVISED ASSESSMENT TASK
Review and improve the existing task against the X–Y model:
1. Does it certify Xmin for all students? (~60% of marks)
2. Does it reward X+ without new content? (~30% of marks)
3. Does it provide open-access X++? (~10% of marks)
4. Are hinge concepts adequately assessed?
5. Does any item exceed the Y-goals?
Rewrite items that do not meet requirements."""
    else:
        task_section = """OUTPUT 1 — FULL ASSESSMENT TASK
Draft a complete assessment task with three sections:

Section A — Core Width (Xmin) (~60% of marks)
Compulsory, accessible to all. Tests minimum construction at key nodes.

Section B — Extended Width (X+) (~30% of marks)
Same concepts, broader integration and coordination.

Section C — Synthetic Width (X++) (~10% of marks)
Open-access. Transfer, application or synthesis.

- No section introduces content beyond the Y-goals
- All students may attempt all sections
- Do not label any section as "extension"
- Assessment mean should naturally sit around 60%"""

    summary_section = ""
    if existing_summary.strip():
        summary_section = f"""EXISTING SUMMARY
──────────────────────────────────
{existing_summary}

OUTPUT 2 — REVISED SUMMARY
Review and improve the existing summary. It should be 150 words max and include:
- Assessment type and format
- Key concepts per section (A/B/C)
- Which hinge concepts are tested
- Mark weighting per section"""
    else:
        summary_section = """OUTPUT 2 — ASSESSMENT SUMMARY (150 words max)
A concise summary for lesson planning. Include:
- Assessment type and format
- Key concepts per section (A/B/C)
- Which hinge concepts are directly tested
- Mark weighting per section"""

    return f"""You are helping a Head of Department design a Year 7 Science assessment aligned to the X–Y Constructivist Model.

CONTEXT
──────────────────────────────────
Year Level: 7
Subject: Science
Assessment Type: {assessment_type}
Standards: {', '.join(selected_codes)}

Y-GOALS (do not exceed these)
──────────────────────────────────
{ctx['y_goal_text']}

PRIOR KNOWLEDGE PATHWAY
──────────────────────────────────
{ctx['prior_text']}

HINGE CONCEPTS (must be adequately assessed)
──────────────────────────────────
{ctx['hinge_text']}

SUCCESS CRITERIA PER NODE (Section A must test these)
──────────────────────────────────
{ctx['sc_text']}

ASSESSMENT MODEL
──────────────────────────────────
- Xmin = minimum construction (~60%)
- X+ = extended width, same concepts (~30%)
- X++ = synthetic width, open-access transfer (~10%)

{task_section}

{summary_section}"""


def show():
    selected_codes = st.session_state.selected_codes
    assessment_type = st.session_state.assessment_type

    if st.button("← Back"):
        st.session_state.page = "s2_nodes"
        st.rerun()

    st.subheader("Assessment Setup")
    st.caption(f"Assessment type: **{assessment_type}** · Standards: {', '.join(selected_codes)}")

    # ── Step 1: Optional existing inputs + generate ───────────────────────────
    st.subheader("Step 1 — Generate Assessment Prompt")
    st.caption("Optionally paste existing task and/or summary — the prompt will review and improve them. Leave blank to draft from scratch.")

    col1, col2 = st.columns(2)
    with col1:
        existing_task = st.text_area(
            "Existing task (optional)",
            value=st.session_state.get("existing_task", ""),
            height=140,
            placeholder="Paste existing task to review, or leave blank to draft new..."
        )
        st.session_state["existing_task"] = existing_task
    with col2:
        existing_summary = st.text_area(
            "Existing summary (optional)",
            value=st.session_state.get("existing_summary", ""),
            height=140,
            placeholder="Paste existing summary to review, or leave blank to generate new..."
        )
        st.session_state["existing_summary"] = existing_summary

    if st.button("Generate Assessment Prompt", type="primary", use_container_width=True):
        st.session_state["last_assessment_prompt"] = build_assessment_prompt(
            selected_codes, assessment_type, existing_task, existing_summary
        )

    if st.session_state.get("last_assessment_prompt"):
        st.code(st.session_state["last_assessment_prompt"], language=None)
        st.caption("Copy and paste into Claude.ai, ChatGPT, or Gemini.")

    # ── Step 2: Paste outputs ─────────────────────────────────────────────────
    st.divider()
    st.subheader("Step 2 — Paste AI Outputs")
    st.caption("Paste the full task and summary from the AI response.")

    col1, col2 = st.columns(2)
    with col1:
        finalised_task = st.text_area(
            "Full assessment task",
            value=st.session_state.get("finalised_task", ""),
            height=180,
            placeholder="Paste Output 1 — full task here..."
        )
        st.session_state["finalised_task"] = finalised_task
    with col2:
        assessment_summary = st.text_area(
            "Assessment summary",
            value=st.session_state.get("assessment_summary", ""),
            height=180,
            placeholder="Paste Output 2 — summary here..."
        )
        st.session_state["assessment_summary"] = assessment_summary

    # ── Confirm and export ────────────────────────────────────────────────────
    st.divider()
    task_confirmed = st.checkbox(
        "Assessment task and summary are finalised — ready for class planning",
        disabled=not (finalised_task.strip() and assessment_summary.strip())
    )

    if task_confirmed:
        st.divider()
        st.subheader("Download Unit Plan")
        st.caption("Class-agnostic PDF — teachers annotate with their friction level.")
        pdf_buf = generate_pdf(
            selected_codes=selected_codes,
            num_lessons=st.session_state.num_lessons,
            assessment_type=assessment_type,
            assessment_summary=assessment_summary
        )
        st.download_button(
            label="⬇ Download Unit Plan PDF",
            data=pdf_buf,
            file_name=f"unit_plan_{'_'.join(selected_codes)}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

    st.divider()
    if st.button("Continue to Class Planning →", type="primary",
                 disabled=not task_confirmed, use_container_width=True):
        st.session_state.page = "s4_planning"
        st.rerun()