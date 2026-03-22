import streamlit as st
from utils import data, standards_map, compression_warnings

def show():
    st.subheader("Curriculum Setup")
    st.caption("Select the standards, lesson count and assessment type for this unit.")

    all_titles = [f"{s['code']} — {s['title']}" for s in data["standards"]]
    selected_display = st.multiselect(
        "Standards covered by this assessment",
        options=all_titles,
        default=[all_titles[4], all_titles[5]]
    )
    selected_codes = [t.split(" — ")[0] for t in selected_display]

    col1, col2 = st.columns(2)
    with col1:
        num_lessons = st.number_input(
            "Total lessons available",
            min_value=4, max_value=40, value=st.session_state.num_lessons, step=1
        )
    with col2:
        assessment_type = st.radio(
            "Assessment type",
            ["Test", "Investigation"],
            index=["Test", "Investigation"].index(st.session_state.assessment_type),
            captions=[
                "Closed response, time-limited, teacher-designed",
                "Practical or extended task, teacher-structured"
            ]
        )

    if selected_codes:
        total_nodes = sum(len(standards_map[c]["nodes"]) for c in selected_codes if c in standards_map)
        st.info(f"**{total_nodes} nodes** across {len(selected_codes)} standard(s) · ~**{num_lessons / total_nodes:.1f} lessons/node**")
        for w in compression_warnings(selected_codes, num_lessons):
            st.warning(w)
    else:
        st.warning("Select at least one standard to continue.")

    if st.button("Review Node Map →", type="primary", disabled=not selected_codes, use_container_width=True):
        st.session_state.selected_codes = selected_codes
        st.session_state.num_lessons = num_lessons
        st.session_state.assessment_type = assessment_type
        st.session_state.page = "s2_nodes"
        st.rerun()
