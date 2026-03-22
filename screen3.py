import streamlit as st
from utils import standards_map, generate_pdf

def show():
    selected_codes = st.session_state.selected_codes
    assessment_type = st.session_state.assessment_type

    if st.button("← Back"):
        st.session_state.page = "s2_nodes"
        st.rerun()

    st.subheader("Assessment Setup")
    st.caption(f"Assessment type: **{assessment_type}** · Standards: {', '.join(selected_codes)}")

    # ── Step 1: Generate assessment prompt ────────────────────────────────────
    st.subheader("Step 1 — Generate Assessment Prompt")
    mode = st.radio(
        "Assessment task",
        ["Draft new", "Review existing"],
        index=["Draft new", "Review existing"].index(st.session_state.assessment_mode),
        horizontal=True
    )
    st.session_state.assessment_mode = mode

    existing_task = ""
    if mode == "Review existing":
        existing_task = st.text_area(
            "Paste your existing assessment task here",
            value=st.session_state.existing_task,
            height=200,
            placeholder="Paste the full assessment task text..."
        )
        st.session_state.existing_task = existing_task

    if st.button("Generate Assessment Prompt", type="primary", use_container_width=True):
        hinge_nodes = []
        y_goals = []
        for code in selected_codes:
            if code not in standards_map:
                continue
            std = standards_map[code]
            y_goals.append(f"{code}: {std['y_goal']}")
            for node in std["nodes"]:
                if node["hinge"]:
                    hinge_nodes.append(f"- Node {node['id']} ({code}): {node['label']} — {node.get('hinge_reason', '')}")

        hinge_text = "\n".join(hinge_nodes) if hinge_nodes else "None identified"
        y_goal_text = "\n".join(y_goals)

        if mode == "Draft new":
            task_instruction = """YOUR TASK
──────────────────────────────────
Draft a complete assessment task with three sections:

Section A — Core Width (Xmin) (~60% of marks)
Compulsory items accessible to all students. Test minimum construction at key nodes.
Focus: clarity, correctness, structured response.
Typical items: identify, describe, explain, compare using scaffolded criteria.

Section B — Extended Width (X+) (~30% of marks)
Same concepts but requiring broader integration and coordination.
Typical items: complete and explain, justify using reasoning, analyse a scenario.

Section C — Synthetic Width (X++) (~10% of marks)
Open-access. Students choose one option demonstrating transfer, application or synthesis.
Typical items: evaluate a claim, explain a real-world application, defend a position.

IMPORTANT:
- No section introduces content beyond the Y-goals above
- All students may attempt all sections
- Do not label any section as "extension"
- Assessment mean should naturally sit around 60% if well-calibrated"""
        else:
            task_instruction = f"""EXISTING TASK TO REVIEW
──────────────────────────────────
{existing_task}

YOUR TASK
──────────────────────────────────
Evaluate the existing task above against the X–Y model requirements:

1. Does it certify minimum width (Xmin) for all students? (~60% of marks)
2. Does it reward extended width (X+) without requiring new content? (~30% of marks)
3. Does it provide open-access synthetic width (X++)? (~10% of marks)
4. Are hinge concepts adequately assessed?
5. Does any item exceed the Y-goals stated above?

Then suggest specific improvements to align it with the three-section structure.
Rewrite any items that do not meet the model's requirements."""

        assessment_prompt = f"""You are helping a Head of Department design a Year 7 Science assessment aligned to the X–Y Constructivist Model.

CONTEXT
──────────────────────────────────
Year Level: 7
Subject: Science
Assessment Type: {assessment_type}
Standards: {', '.join(selected_codes)}

Y-GOALS (fixed conceptual endpoints — do not exceed these)
──────────────────────────────────
{y_goal_text}

HINGE CONCEPTS (must be adequately assessed)
──────────────────────────────────
{hinge_text}

ASSESSMENT MODEL
──────────────────────────────────
This assessment uses the X–Y model where:
- Y-axis = conceptual depth (fixed, same for all students)
- X-axis = width of construction (differentiated horizontally)
- Xmin = minimum construction certifying the standard (~60% of marks)
- X+ = extended width, same concepts, broader integration (~30% of marks)
- X++ = synthetic width, open-access transfer and application (~10% of marks)

{task_instruction}"""

        st.session_state["last_assessment_prompt"] = assessment_prompt

    if st.session_state.get("last_assessment_prompt"):
        st.code(st.session_state["last_assessment_prompt"], language=None)
        st.caption("Copy and paste into Claude.ai, ChatGPT, or Gemini.")

    # ── Step 2: Paste full task ───────────────────────────────────────────────
    st.divider()
    st.subheader("Step 2 — Paste Full Task")
    st.caption("Paste the full AI-generated task here. This enables summary generation in Step 3.")

    finalised_task = st.text_area(
        "Full assessment task",
        value=st.session_state.get("finalised_task", ""),
        height=180,
        placeholder="Paste the full AI-generated task here...",
        label_visibility="collapsed"
    )
    st.session_state["finalised_task"] = finalised_task

    # ── Step 3: Generate and paste summary ───────────────────────────────────
    st.divider()
    st.subheader("Step 3 — Generate and Paste Assessment Summary")
    st.caption("Generate a concise summary to inform lesson planning. Only the summary feeds into Screen 4.")

    if finalised_task.strip():
        if st.button("Generate Summary Prompt", use_container_width=True):
            summary_prompt = f"""You are helping summarise an assessment task for Year 7 Science lesson planning purposes.

ASSESSMENT TASK
──────────────────────────────────
{finalised_task}

YOUR TASK
──────────────────────────────────
Generate a concise assessment summary (maximum 150 words) suitable for informing lesson planning. Include:
- Assessment type and format
- Key concepts assessed in Section A (Xmin), Section B (X+), and Section C (X++)
- Which hinge concepts are directly tested
- Overall mark weighting per section

Do not reproduce the full task. The summary will be used as context in lesson planning prompts."""
            st.session_state["last_summary_prompt"] = summary_prompt

        if st.session_state.get("last_summary_prompt"):
            st.code(st.session_state["last_summary_prompt"], language=None)
            st.caption("Copy and paste into Claude.ai, ChatGPT, or Gemini.")
    else:
        st.info("Paste the full task in Step 2 first to enable summary generation.")

    assessment_summary = st.text_area(
        "Assessment summary (feeds into lesson planning prompts)",
        value=st.session_state.get("assessment_summary", ""),
        height=120,
        placeholder="Paste the AI-generated summary here...",
        label_visibility="collapsed"
    )
    st.session_state["assessment_summary"] = assessment_summary

    st.divider()
    task_confirmed = st.checkbox(
        "Assessment task and summary are finalised — ready for class planning",
        disabled=not (finalised_task.strip() and st.session_state.get("assessment_summary", "").strip())
    )

    if task_confirmed:
        st.divider()
        st.subheader("Download Unit Plan")
        st.caption("Download the complete node map and assessment structure as a PDF. Teachers annotate their copy with friction level and prior knowledge.")
        pdf_buf = generate_pdf(
            selected_codes=selected_codes,
            num_lessons=st.session_state.num_lessons,
            assessment_type=assessment_type,
            assessment_summary=st.session_state.get("assessment_summary", "")
        )
        st.download_button(
            label="⬇ Download Unit Plan PDF",
            data=pdf_buf,
            file_name=f"unit_plan_{'_'.join(selected_codes)}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
        st.caption("This plan is class-agnostic. Teachers circle the appropriate width level for their class.")

    st.divider()
    if st.button("Continue to Class Planning →", type="primary",
                 disabled=not task_confirmed, use_container_width=True):
        st.session_state.page = "s4_planning"
        st.rerun()
