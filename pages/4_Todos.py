import streamlit as st
from datetime import date

st.set_page_config(page_title="To-Dos — Life Game", page_icon="✅", layout="wide")

from components.auth import require_auth
from components.ui_helpers import (inject_custom_css, render_sidebar,
                                   render_reward_toast, difficulty_badge, due_date_badge)
from db.queries import (get_todos, create_todo, delete_todo,
                        complete_todo, update_todo)

inject_custom_css()
username = require_auth()
render_sidebar(username)

st.title("✅ To-Dos")
st.caption("One-off tasks. Check them off to earn XP and gold.")

# ── Add todo form ─────────────────────────────────────────────────────────────
with st.expander("➕ Add New To-Do", expanded=False):
    with st.form("add_todo_form", clear_on_submit=True):
        t_title = st.text_input("Task name *", placeholder="e.g. Finish quarterly report")
        t_notes = st.text_input("Notes", placeholder="Optional details")
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            t_diff = st.selectbox("Difficulty", ["trivial", "easy", "medium", "hard"], index=1)
        with tc2:
            t_due = st.date_input("Due date (optional)", value=None)
        with tc3:
            t_prio = st.checkbox("⭐ Priority", value=False)
        if st.form_submit_button("Add To-Do", use_container_width=True):
            if t_title.strip():
                due_str = str(t_due) if t_due else None
                create_todo(username, t_title.strip(), t_notes.strip(),
                            t_diff, due_str, int(t_prio))
                st.success(f"Added: {t_title}")
                st.rerun()
            else:
                st.error("Task name is required.")

st.markdown("---")

# ── Filters ───────────────────────────────────────────────────────────────────
fc1, fc2 = st.columns([3, 1])
with fc1:
    sort_by = st.radio("Sort by", ["Priority → Due Date", "Due Date", "Difficulty", "Created"],
                       horizontal=True, index=0)
with fc2:
    show_filter = st.selectbox("Show", ["All", "Overdue", "Due Today", "No Date"])

todos = get_todos(username, include_completed=False)
today = date.today()

# Apply filter
if show_filter == "Overdue":
    todos = [t for t in todos if t.get("due_date") and t["due_date"] < str(today)]
elif show_filter == "Due Today":
    todos = [t for t in todos if t.get("due_date") == str(today)]
elif show_filter == "No Date":
    todos = [t for t in todos if not t.get("due_date")]

# Apply sort
DIFF_ORDER = {"trivial": 0, "easy": 1, "medium": 2, "hard": 3}
if sort_by == "Due Date":
    todos.sort(key=lambda t: (t.get("due_date") or "9999-99-99"))
elif sort_by == "Difficulty":
    todos.sort(key=lambda t: DIFF_ORDER.get(t["difficulty"], 1), reverse=True)
elif sort_by == "Priority → Due Date":
    todos.sort(key=lambda t: (-t["priority_flag"], t.get("due_date") or "9999-99-99"))

# ── Active todos ──────────────────────────────────────────────────────────────
if not todos:
    st.success("No tasks match the filter. You're all caught up! 🎉")
else:
    for t in todos:
        col_done, col_info, col_actions = st.columns([1, 7, 2])

        with col_done:
            if st.button("☐", key=f"complete_{t['id']}", help="Mark complete"):
                result = complete_todo(username, t["id"])
                st.session_state[f"todo_reward_{t['id']}"] = result
                st.rerun()

        with col_info:
            prio_icon = "⭐ " if t["priority_flag"] else ""
            badge = difficulty_badge(t["difficulty"])
            due_badge = due_date_badge(t.get("due_date"))
            st.markdown(
                f'<div style="padding:6px 0;">'
                f'<span class="task-title">{prio_icon}{t["title"]}</span>{badge}'
                f'<span style="margin-left:10px;">{due_badge}</span>'
                + (f'<div class="task-notes">{t["notes"]}</div>' if t["notes"] else "")
                + '</div>',
                unsafe_allow_html=True
            )

        with col_actions:
            ac1, ac2 = st.columns(2)
            with ac1:
                new_prio = 0 if t["priority_flag"] else 1
                label = "⭐" if not t["priority_flag"] else "★"
                if st.button(label, key=f"prio_{t['id']}", help="Toggle priority"):
                    update_todo(t["id"], priority_flag=new_prio)
                    st.rerun()
            with ac2:
                if st.button("🗑️", key=f"del_todo_{t['id']}", help="Delete"):
                    delete_todo(t["id"])
                    st.rerun()

        if f"todo_reward_{t['id']}" in st.session_state:
            render_reward_toast(st.session_state.pop(f"todo_reward_{t['id']}"))

        # Edit
        with st.expander(f"✏️ Edit: {t['title']}", expanded=False):
            with st.form(f"edit_todo_{t['id']}", clear_on_submit=False):
                et = st.text_input("Title", value=t["title"])
                en = st.text_input("Notes", value=t["notes"] or "")
                ed = st.selectbox("Difficulty",
                                  ["trivial", "easy", "medium", "hard"],
                                  index=["trivial", "easy", "medium", "hard"].index(t["difficulty"]))
                curr_due = date.fromisoformat(t["due_date"]) if t.get("due_date") else None
                edp = st.date_input("Due date", value=curr_due)
                if st.form_submit_button("Save"):
                    update_todo(t["id"], title=et, notes=en, difficulty=ed,
                                due_date=str(edp) if edp else None)
                    st.success("Updated!")
                    st.rerun()

        st.markdown('<hr style="border-color:#2c2c3e;margin:4px 0;">', unsafe_allow_html=True)

# ── Completed todos ───────────────────────────────────────────────────────────
completed = get_todos(username, include_completed=True)
completed = [t for t in completed if t["completed"]]
if completed:
    with st.expander(f"Completed ({len(completed)})", expanded=False):
        for t in completed[-20:][::-1]:
            ts = t.get("completed_at", "")[:10]
            badge = difficulty_badge(t["difficulty"])
            st.markdown(
                f'<div class="task-card completed-task">'
                f'<span>✅ {t["title"]}</span>{badge}'
                f'<span style="color:#555;font-size:12px;margin-left:8px;">done {ts}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
