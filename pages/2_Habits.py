import streamlit as st

st.set_page_config(page_title="Habits — Life Game", page_icon="🔄", layout="wide")

from components.auth import require_auth
from components.ui_helpers import (inject_custom_css, render_sidebar,
                                   render_reward_toast, difficulty_badge,
                                   habit_value_display)
from db.queries import (get_habits, create_habit, delete_habit,
                        record_habit_click, update_habit)

inject_custom_css()
username = require_auth()
render_sidebar(username)

st.title("🔄 Habits")
st.caption("Click ➕ to reinforce good habits, ➖ to acknowledge bad ones.")

# ── Add habit form ────────────────────────────────────────────────────────────
with st.expander("➕ Add New Habit", expanded=False):
    with st.form("add_habit_form", clear_on_submit=True):
        h_title = st.text_input("Habit name *", placeholder="e.g. Exercise for 30 minutes")
        h_notes = st.text_input("Notes", placeholder="Optional description")
        hc1, hc2, hc3 = st.columns(3)
        with hc1:
            h_diff = st.selectbox("Difficulty", ["trivial", "easy", "medium", "hard"], index=1)
        with hc2:
            h_pos = st.checkbox("Has + button", value=True)
        with hc3:
            h_neg = st.checkbox("Has − button", value=True)
        if st.form_submit_button("Create Habit", use_container_width=True):
            if h_title.strip():
                create_habit(username, h_title.strip(), h_notes.strip(), h_pos, h_neg, h_diff)
                st.success(f"Created habit: {h_title}")
                st.rerun()
            else:
                st.error("Habit name is required.")

st.markdown("---")

# ── Habit list ────────────────────────────────────────────────────────────────
habits = get_habits(username)
if not habits:
    st.info("No habits yet. Add your first habit above!")
else:
    for h in habits:
        col_info, col_val, col_btns = st.columns([4, 3, 2])

        with col_info:
            badge = difficulty_badge(h["difficulty"])
            st.markdown(
                f'<div style="padding:8px 0;">'
                f'<span class="task-title">{h["title"]}</span>{badge}'
                + (f'<div class="task-notes">{h["notes"]}</div>' if h["notes"] else "")
                + f'<div style="font-size:11px;color:#555;margin-top:3px;">'
                f'✅ {h["up_count"]} times  ❌ {h["down_count"]} times</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col_val:
            st.markdown(
                f'<div style="padding:12px 0;">'
                + habit_value_display(h["value"])
                + '</div>',
                unsafe_allow_html=True
            )

        with col_btns:
            btn_cols = st.columns([1, 1, 1])
            if h.get("positive"):
                with btn_cols[0]:
                    if st.button("➕", key=f"up_{h['id']}", help="Reinforce this habit"):
                        result = record_habit_click(username, h["id"], "up")
                        st.session_state[f"reward_{h['id']}"] = result
                        st.rerun()
            if h.get("negative"):
                with btn_cols[1]:
                    if st.button("➖", key=f"dn_{h['id']}", help="You gave in to this habit"):
                        result = record_habit_click(username, h["id"], "down")
                        st.session_state[f"penalty_{h['id']}"] = result
                        st.rerun()
            with btn_cols[2]:
                if st.button("🗑️", key=f"del_{h['id']}", help="Delete habit"):
                    delete_habit(h["id"])
                    st.rerun()

        # Show reward toast if just clicked
        if f"reward_{h['id']}" in st.session_state:
            render_reward_toast(st.session_state.pop(f"reward_{h['id']}"))
        if f"penalty_{h['id']}" in st.session_state:
            r = st.session_state.pop(f"penalty_{h['id']}")
            st.warning("❌ −0.5 HP", icon=None)

        # Edit expander
        with st.expander(f"✏️ Edit: {h['title']}", expanded=False):
            with st.form(f"edit_habit_{h['id']}", clear_on_submit=False):
                et = st.text_input("Title", value=h["title"])
                en = st.text_input("Notes", value=h["notes"] or "")
                ec1, ec2, ec3 = st.columns(3)
                with ec1:
                    ed = st.selectbox("Difficulty",
                                      ["trivial", "easy", "medium", "hard"],
                                      index=["trivial", "easy", "medium", "hard"].index(h["difficulty"]))
                with ec2:
                    ep = st.checkbox("Has +", value=bool(h["positive"]))
                with ec3:
                    emin = st.checkbox("Has −", value=bool(h["negative"]))
                if st.form_submit_button("Save Changes"):
                    update_habit(h["id"], title=et, notes=en, difficulty=ed,
                                 positive=int(ep), negative=int(emin))
                    st.success("Updated!")
                    st.rerun()

        st.markdown('<hr style="border-color:#2c2c3e;margin:4px 0;">', unsafe_allow_html=True)
