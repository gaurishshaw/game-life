import streamlit as st
from datetime import date

st.set_page_config(page_title="Dailies — Life Game", page_icon="📅", layout="wide")

from components.auth import require_auth
from components.ui_helpers import (inject_custom_css, render_sidebar,
                                   render_reward_toast, difficulty_badge)
from db.queries import get_dailies, create_daily, delete_daily, complete_daily, update_daily

inject_custom_css()
username = require_auth()
render_sidebar(username)

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
today_dow = date.today().weekday()

st.title("📅 Dailies")
st.caption(f"Today is **{date.today().strftime('%A, %b %d')}**. Complete your dailies before midnight!")

# ── Add daily form ────────────────────────────────────────────────────────────
with st.expander("➕ Add New Daily", expanded=False):
    with st.form("add_daily_form", clear_on_submit=True):
        d_title = st.text_input("Daily name *", placeholder="e.g. Read for 20 minutes")
        d_notes = st.text_input("Notes", placeholder="Optional")
        dc1, dc2 = st.columns(2)
        with dc1:
            d_diff = st.selectbox("Difficulty", ["trivial", "easy", "medium", "hard"], index=1)
        with dc2:
            d_freq = st.radio("Frequency", ["Every day", "Specific days"], horizontal=True)
        if d_freq == "Specific days":
            selected_days = st.multiselect("Active days", DAY_NAMES,
                                           default=["Mon", "Tue", "Wed", "Thu", "Fri"])
            days_list = [DAY_NAMES.index(d) for d in selected_days]
        else:
            days_list = list(range(7))
        if st.form_submit_button("Create Daily", use_container_width=True):
            if d_title.strip():
                if not days_list:
                    st.error("Select at least one day.")
                else:
                    create_daily(username, d_title.strip(), d_notes.strip(),
                                 d_diff, "weekly" if d_freq == "Specific days" else "daily", days_list)
                    st.success(f"Created: {d_title}")
                    st.rerun()
            else:
                st.error("Name is required.")

st.markdown("---")

dailies = get_dailies(username)
today_str = str(today_dow)

due_today = [d for d in dailies if today_str in d["days_of_week"].split(",")]
not_due = [d for d in dailies if today_str not in d["days_of_week"].split(",")]

# ── Due today ─────────────────────────────────────────────────────────────────
done_count = sum(1 for d in due_today if d["completed_today"])
st.subheader(f"Due Today — {done_count}/{len(due_today)} completed")

if not due_today:
    st.info("No dailies scheduled for today. Enjoy your rest day!")
else:
    for d in due_today:
        done = bool(d["completed_today"])
        col_check, col_info, col_actions = st.columns([1, 7, 2])

        with col_check:
            st.markdown(f'<div style="padding:10px 0;font-size:28px;">{"✅" if done else "⬜"}</div>',
                        unsafe_allow_html=True)

        with col_info:
            streak_html = (f'<span style="color:#f39c12;font-size:13px;margin-left:8px;">'
                           f'🔥 {d["streak"]} day streak'
                           + (f' (best: {d["best_streak"]})' if d["best_streak"] > d["streak"] else "")
                           + '</span>') if d["streak"] > 0 else ""
            badge = difficulty_badge(d["difficulty"])
            days_active = ", ".join(DAY_NAMES[int(i)] for i in d["days_of_week"].split(",") if i.strip())
            st.markdown(
                f'<div style="padding:8px 0;opacity:{0.5 if done else 1.0};">'
                f'<span class="task-title">{d["title"]}</span>{badge}{streak_html}'
                + (f'<div class="task-notes">{d["notes"]}</div>' if d["notes"] else "")
                + f'<div style="font-size:11px;color:#555;margin-top:2px;">Repeats: {days_active}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col_actions:
            if not done:
                if st.button("Complete ✓", key=f"done_{d['id']}", use_container_width=True):
                    result = complete_daily(username, d["id"])
                    st.session_state[f"daily_reward_{d['id']}"] = result
                    st.rerun()
            else:
                st.markdown('<div style="color:#27ae60;padding:10px 0;text-align:center;">Done!</div>',
                            unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_daily_{d['id']}", help="Delete this daily"):
                delete_daily(d["id"])
                st.rerun()

        if f"daily_reward_{d['id']}" in st.session_state:
            render_reward_toast(st.session_state.pop(f"daily_reward_{d['id']}"))

        # Edit
        with st.expander(f"✏️ Edit: {d['title']}", expanded=False):
            with st.form(f"edit_daily_{d['id']}", clear_on_submit=False):
                et = st.text_input("Title", value=d["title"])
                en = st.text_input("Notes", value=d["notes"] or "")
                ed = st.selectbox("Difficulty",
                                  ["trivial", "easy", "medium", "hard"],
                                  index=["trivial", "easy", "medium", "hard"].index(d["difficulty"]))
                curr_days = [DAY_NAMES[int(i)] for i in d["days_of_week"].split(",") if i.strip()]
                new_days = st.multiselect("Active days", DAY_NAMES, default=curr_days)
                if st.form_submit_button("Save"):
                    days_list = [DAY_NAMES.index(x) for x in new_days]
                    update_daily(d["id"], title=et, notes=en, difficulty=ed,
                                 days_of_week=",".join(str(x) for x in days_list))
                    st.success("Updated!")
                    st.rerun()

        st.markdown('<hr style="border-color:#2c2c3e;margin:4px 0;">', unsafe_allow_html=True)

# ── Not due today ──────────────────────────────────────────────────────────────
if not_due:
    with st.expander(f"Not due today ({len(not_due)})", expanded=False):
        for d in not_due:
            badge = difficulty_badge(d["difficulty"])
            days_active = ", ".join(DAY_NAMES[int(i)] for i in d["days_of_week"].split(",") if i.strip())
            next_days = [int(i) for i in d["days_of_week"].split(",") if i.strip()]
            nxt = next((DAY_NAMES[x] for x in next_days if x > today_dow), DAY_NAMES[next_days[0]] if next_days else "?")
            st.markdown(
                f'<div class="task-card" style="opacity:0.5;">'
                f'<span class="task-title">{d["title"]}</span>{badge}'
                f'<span style="color:#555;font-size:12px;"> — next: {nxt} | repeats: {days_active}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
