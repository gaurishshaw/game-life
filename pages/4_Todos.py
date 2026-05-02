import streamlit as st
from datetime import date
from collections import defaultdict

st.set_page_config(page_title="Questlines — Life Game", page_icon="📜", layout="wide")

from components.auth import require_auth
from components.ui_helpers import (inject_custom_css, render_sidebar,
                                   render_reward_toast, difficulty_badge,
                                   due_date_badge, questline_section_header,
                                   QUESTLINE_ORDER, GOLD, TEXT_DIM, CARD_BG)
from db.queries import (get_todos, create_todo, delete_todo,
                        complete_todo, update_todo)

inject_custom_css()
username = require_auth()
render_sidebar(username)

st.title("📜 Questlines")
st.caption("Objectives grouped by initiative. Completion grants Grace and Gold.")

# ── Collect existing tags for the project selector ────────────────────────────
all_todos_raw = get_todos(username, include_completed=True)
existing_tags = sorted({t.get("tag", "") for t in all_todos_raw if t.get("tag", "").strip()})
suggested_tags = list(dict.fromkeys(QUESTLINE_ORDER + existing_tags))  # dedup, preserve order

# ── Add quest form ─────────────────────────────────────────────────────────────
with st.expander("◈  Add New Quest", expanded=False):
    with st.form("add_quest_form", clear_on_submit=True):
        fc1, fc2 = st.columns([3, 1])
        with fc1:
            t_title = st.text_input("Objective *", placeholder="Describe the deliverable clearly")
        with fc2:
            t_diff = st.selectbox("Difficulty", ["trivial", "easy", "medium", "hard"], index=1)

        gc1, gc2, gc3 = st.columns([2, 2, 1])
        with gc1:
            tag_choice = st.selectbox("Questline (project)",
                                      ["— New —"] + suggested_tags,
                                      index=0)
        with gc2:
            tag_custom = st.text_input("New questline name",
                                       placeholder="Only if '— New —' selected above",
                                       disabled=(tag_choice != "— New —"))
        with gc3:
            t_prio = st.checkbox("⭐ Priority")

        t_notes = st.text_input("Notes / constraints", placeholder="Optional")
        t_due   = st.date_input("Due date (optional)", value=None)

        if st.form_submit_button("Add to Questline", use_container_width=True):
            if not t_title.strip():
                st.error("Objective title is required.")
            else:
                tag = tag_custom.strip() if tag_choice == "— New —" else tag_choice
                due_str = str(t_due) if t_due else None
                create_todo(username, t_title.strip(), t_notes.strip(),
                            t_diff, due_str, int(t_prio), tag)
                st.success(f"Quest added to: {tag or 'Miscellaneous'}")
                st.rerun()

st.markdown("---")

# ── Filter / sort controls ────────────────────────────────────────────────────
fc1, fc2, fc3 = st.columns([3, 2, 2])
with fc1:
    sort_by = st.radio("Sort within questline",
                       ["Priority", "Due Date", "Difficulty"],
                       horizontal=True)
with fc2:
    show_filter = st.selectbox("Show", ["Active", "Overdue", "Due Today", "All Active"])
with fc3:
    tag_filter = st.selectbox("Filter questline",
                              ["All"] + suggested_tags)

# ── Load and filter todos ─────────────────────────────────────────────────────
todos = get_todos(username, include_completed=False)
today = date.today()

if show_filter == "Overdue":
    todos = [t for t in todos if t.get("due_date") and t["due_date"] < str(today)]
elif show_filter == "Due Today":
    todos = [t for t in todos if t.get("due_date") == str(today)]

if tag_filter != "All":
    todos = [t for t in todos if (t.get("tag") or "") == tag_filter]

# Sort within each group
DIFF_ORDER = {"trivial": 0, "easy": 1, "medium": 2, "hard": 3}
if sort_by == "Due Date":
    todos.sort(key=lambda t: (t.get("due_date") or "9999-99-99"))
elif sort_by == "Difficulty":
    todos.sort(key=lambda t: DIFF_ORDER.get(t["difficulty"], 1), reverse=True)
else:
    todos.sort(key=lambda t: (-t["priority_flag"], t.get("due_date") or "9999-99-99"))

# ── Group by questline ────────────────────────────────────────────────────────
grouped = defaultdict(list)
for t in todos:
    bucket = (t.get("tag") or "").strip() or "Miscellaneous"
    grouped[bucket].append(t)

# Render in defined order, then alphabetical remainders, Misc always last
ordered_keys = [k for k in QUESTLINE_ORDER if k in grouped]
ordered_keys += sorted([k for k in grouped if k not in QUESTLINE_ORDER and k != "Miscellaneous"])
if "Miscellaneous" in grouped:
    ordered_keys.append("Miscellaneous")

if not ordered_keys:
    st.info("No active quests. Add your first objective above.")

for bucket in ordered_keys:
    bucket_todos = grouped[bucket]
    st.markdown(questline_section_header(bucket, len(bucket_todos)), unsafe_allow_html=True)

    for t in bucket_todos:
        col_done, col_info, col_actions = st.columns([1, 7, 2])

        with col_done:
            if st.button("☐", key=f"complete_{t['id']}", help="Mark complete"):
                result = complete_todo(username, t["id"])
                st.session_state[f"quest_reward_{t['id']}"] = result
                st.rerun()

        with col_info:
            prio_icon = "⭐ " if t["priority_flag"] else ""
            badge     = difficulty_badge(t["difficulty"])
            due_badge = due_date_badge(t.get("due_date"))
            tag_html  = (f'<span style="color:{TEXT_DIM};font-size:10px;'
                         f'border:1px solid #c9a22733;padding:1px 5px;border-radius:2px;'
                         f'margin-left:6px;letter-spacing:0.06em;">{t.get("tag","")}</span>'
                         if t.get("tag") else "")
            st.markdown(
                f'<div style="padding:5px 0;">'
                f'<span class="task-title">{prio_icon}{t["title"]}</span>{badge}'
                f'<span style="margin-left:8px;">{due_badge}</span>{tag_html}'
                + (f'<div class="task-notes">{t["notes"]}</div>' if t["notes"] else "")
                + '</div>',
                unsafe_allow_html=True
            )

        with col_actions:
            ac1, ac2 = st.columns(2)
            with ac1:
                label = "⭐" if not t["priority_flag"] else "★"
                if st.button(label, key=f"prio_{t['id']}", help="Toggle priority"):
                    update_todo(t["id"], priority_flag=0 if t["priority_flag"] else 1)
                    st.rerun()
            with ac2:
                if st.button("✕", key=f"del_{t['id']}", help="Delete"):
                    delete_todo(t["id"])
                    st.rerun()

        if f"quest_reward_{t['id']}" in st.session_state:
            render_reward_toast(st.session_state.pop(f"quest_reward_{t['id']}"))

        # Edit expander
        with st.expander(f"Edit: {t['title'][:40]}...", expanded=False):
            with st.form(f"edit_quest_{t['id']}", clear_on_submit=False):
                et  = st.text_input("Title", value=t["title"])
                en  = st.text_input("Notes", value=t["notes"] or "")
                ec1, ec2 = st.columns(2)
                with ec1:
                    ed = st.selectbox("Difficulty",
                                      ["trivial", "easy", "medium", "hard"],
                                      index=["trivial","easy","medium","hard"].index(t["difficulty"]))
                with ec2:
                    etag_choice = st.selectbox("Questline",
                                               ["— New —"] + suggested_tags,
                                               index=(suggested_tags.index(t.get("tag","")) + 1)
                                               if t.get("tag","") in suggested_tags else 0)
                etag_custom = st.text_input("New questline name",
                                            disabled=(etag_choice != "— New —"))
                curr_due = date.fromisoformat(t["due_date"]) if t.get("due_date") else None
                edp = st.date_input("Due date", value=curr_due)
                if st.form_submit_button("Save"):
                    new_tag = etag_custom.strip() if etag_choice == "— New —" else etag_choice
                    update_todo(t["id"], title=et, notes=en, difficulty=ed,
                                tag=new_tag, due_date=str(edp) if edp else None)
                    st.success("Quest updated.")
                    st.rerun()

        st.markdown(f'<hr style="border-color:#c9a22714;margin:4px 0;">', unsafe_allow_html=True)

# ── Completed quests archive ──────────────────────────────────────────────────
completed = [t for t in all_todos_raw if t["completed"]]
if completed:
    with st.expander(f"◇  Completed Archive  ({len(completed)})", expanded=False):
        for t in completed[-30:][::-1]:
            ts    = (t.get("completed_at") or "")[:10]
            badge = difficulty_badge(t["difficulty"])
            tag_html = (f'<span class="questline-tag">{t["tag"]}</span>'
                        if t.get("tag") else "")
            st.markdown(
                f'<div class="task-card completed-task">'
                f'✓ {t["title"]}{badge}{tag_html}'
                f'<span style="color:{TEXT_DIM};font-size:11px;margin-left:8px;">{ts}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
