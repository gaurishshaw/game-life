import streamlit as st
from datetime import date, datetime

st.set_page_config(page_title="Dashboard — Life Game", page_icon="🏠", layout="wide")

from components.auth import require_auth
from components.ui_helpers import (inject_custom_css, render_sidebar,
                                   render_cron_banner, difficulty_badge)
from db.queries import get_full_character, get_activity_log, get_dailies, get_todos

inject_custom_css()
username = require_auth()
render_sidebar(username)

# Run cron once per session
if "cron_checked" not in st.session_state:
    from db.queries import ensure_user_exists
    from game.cron import maybe_run_cron
    ensure_user_exists(username)
    st.session_state["cron_results"] = maybe_run_cron(username)
    st.session_state["cron_checked"] = True

render_cron_banner(st.session_state.get("cron_results", []))

char = get_full_character(username)
from game.classes import CLASS_DEFINITIONS
cls_def = CLASS_DEFINITIONS.get(char["class"], {})

st.title(f"{cls_def.get('emoji','⚔️')} Dashboard")

# ── Today at a glance ────────────────────────────────────────────────────────
today = date.today()
today_dow = str(today.weekday())

dailies = get_dailies(username)
due_today = [d for d in dailies if today_dow in d["days_of_week"].split(",")]
completed_today = sum(1 for d in due_today if d["completed_today"])

todos_all = get_todos(username, include_completed=False)
todos_due_today = [t for t in todos_all if t.get("due_date") == str(today)]
overdue = [t for t in todos_all if t.get("due_date") and t["due_date"] < str(today)]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Level", char["level"])
col2.metric("Dailies Today", f"{completed_today} / {len(due_today)}")
col3.metric("Overdue To-Dos", len(overdue), delta=f"-{len(overdue)}" if overdue else None,
            delta_color="inverse")
col4.metric("Gold", f"{char['gold']:.1f} 💰")

st.markdown("---")

# ── Stats overview ────────────────────────────────────────────────────────────
st.subheader("Character Stats")
sc1, sc2, sc3, sc4 = st.columns(4)
with sc1:
    st.markdown(f"""
    <div style="background:#1a1a2e;border-radius:8px;padding:14px;text-align:center;border:1px solid #9b59b640;">
        <div style="font-size:11px;color:#888;text-transform:uppercase;">Strength</div>
        <div style="font-size:28px;font-weight:bold;color:#e74c3c;">⚔️ {char['strength']}</div>
        <div style="font-size:11px;color:#555;">(base {char['base_strength']} + {char['equip_strength']} equip)</div>
    </div>""", unsafe_allow_html=True)
with sc2:
    st.markdown(f"""
    <div style="background:#1a1a2e;border-radius:8px;padding:14px;text-align:center;border:1px solid #9b59b640;">
        <div style="font-size:11px;color:#888;text-transform:uppercase;">Constitution</div>
        <div style="font-size:28px;font-weight:bold;color:#27ae60;">🛡️ {char['constitution']}</div>
        <div style="font-size:11px;color:#555;">(base {char['base_constitution']} + {char['equip_constitution']} equip)</div>
    </div>""", unsafe_allow_html=True)
with sc3:
    st.markdown(f"""
    <div style="background:#1a1a2e;border-radius:8px;padding:14px;text-align:center;border:1px solid #9b59b640;">
        <div style="font-size:11px;color:#888;text-transform:uppercase;">Intelligence</div>
        <div style="font-size:28px;font-weight:bold;color:#9b59b6;">🔮 {char['intelligence']}</div>
        <div style="font-size:11px;color:#555;">(base {char['base_intelligence']} + {char['equip_intelligence']} equip)</div>
    </div>""", unsafe_allow_html=True)
with sc4:
    st.markdown(f"""
    <div style="background:#1a1a2e;border-radius:8px;padding:14px;text-align:center;border:1px solid #9b59b640;">
        <div style="font-size:11px;color:#888;text-transform:uppercase;">Perception</div>
        <div style="font-size:28px;font-weight:bold;color:#f39c12;">👁️ {char['perception']}</div>
        <div style="font-size:11px;color:#555;">(base {char['base_perception']} + {char['equip_perception']} equip)</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ── Upcoming dailies ─────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📅 Today's Dailies")
    if not due_today:
        st.info("No dailies due today.")
    else:
        for d in due_today:
            done = d["completed_today"]
            icon = "✅" if done else "⬜"
            streak_txt = f" 🔥{d['streak']}" if d["streak"] > 0 else ""
            badge = difficulty_badge(d["difficulty"])
            st.markdown(
                f'<div class="task-card" style="opacity:{0.5 if done else 1.0};">'
                f'<span class="task-title">{icon} {d["title"]}</span>{badge}'
                f'<span style="color:#888;font-size:12px;">{streak_txt}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

with col_right:
    st.subheader("✅ Overdue To-Dos")
    if not overdue:
        st.success("No overdue tasks!")
    else:
        for t in overdue[:10]:
            days_late = (today - date.fromisoformat(t["due_date"])).days
            badge = difficulty_badge(t["difficulty"])
            st.markdown(
                f'<div class="task-card" style="border-left-color:#e74c3c;">'
                f'<span class="task-title">{t["title"]}</span>{badge}'
                f'<span class="overdue" style="font-size:12px;margin-left:8px;">'
                f'🔴 {days_late}d overdue</span>'
                f'</div>',
                unsafe_allow_html=True
            )

st.markdown("---")

# ── Activity feed ─────────────────────────────────────────────────────────────
st.subheader("📜 Recent Activity")
log = get_activity_log(username, limit=25)
if not log:
    st.info("No activity yet. Complete some tasks to see your history here!")
else:
    EVENT_ICONS = {
        "habit_up": "✅", "habit_down": "❌", "daily_complete": "📅",
        "daily_miss": "💔", "todo_complete": "✔️", "reward_buy": "🎁",
        "level_up": "🎉", "item_buy": "🛒", "skill_use": "⚡", "cron_run": "🌙",
    }
    for event in log:
        ts = event["created_at"][:16].replace("T", " ")
        icon = EVENT_ICONS.get(event["event_type"], "•")
        import json
        detail = {}
        if event.get("detail"):
            try:
                detail = json.loads(event["detail"])
            except Exception:
                pass
        title = detail.get("title", event["event_type"].replace("_", " ").title())

        xp_txt = f" +{event['xp_delta']:.1f}XP" if event.get("xp_delta", 0) > 0 else ""
        gold_txt = f" +{event['gold_delta']:.1f}g" if event.get("gold_delta", 0) > 0 else ""
        hp_txt = f" {event['hp_delta']:+.1f}HP" if event.get("hp_delta", 0) != 0 else ""
        crit_txt = " ⚡CRIT" if detail.get("crit") else ""

        st.markdown(
            f'<div style="display:flex;justify-content:space-between;padding:6px 10px;'
            f'border-bottom:1px solid #2c2c3e;font-size:13px;">'
            f'<span>{icon} {title}{crit_txt}</span>'
            f'<span style="color:#888;">'
            f'<span style="color:#9b59b6;">{xp_txt}</span>'
            f'<span style="color:#f1c40f;">{gold_txt}</span>'
            f'<span style="color:#e74c3c;">{hp_txt}</span>'
            f' &nbsp; {ts}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
