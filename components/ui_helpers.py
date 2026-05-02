import streamlit as st
from datetime import date

DIFFICULTY_COLORS = {
    "trivial": "#7f8c8d",
    "easy":    "#27ae60",
    "medium":  "#f39c12",
    "hard":    "#e74c3c",
}
DIFFICULTY_EMOJI = {"trivial": "☁️", "easy": "⭐", "medium": "🔥", "hard": "💀"}

HABIT_VALUE_COLORS = {
    "purple": "#9b59b6",
    "blue":   "#2980b9",
    "yellow": "#f1c40f",
    "orange": "#e67e22",
    "red":    "#c0392b",
}


def habit_value_color(value: float) -> tuple:
    if value >= 3.0:
        return HABIT_VALUE_COLORS["purple"], "purple"
    if value >= 1.0:
        return HABIT_VALUE_COLORS["blue"], "blue"
    if value >= -1.0:
        return HABIT_VALUE_COLORS["yellow"], "yellow"
    if value >= -3.0:
        return HABIT_VALUE_COLORS["orange"], "orange"
    return HABIT_VALUE_COLORS["red"], "red"


def inject_custom_css() -> None:
    st.markdown("""
    <style>
    /* Progress bar containers */
    .stat-bar-wrap { margin-bottom: 10px; }
    .stat-bar-label {
        display: flex; justify-content: space-between;
        margin-bottom: 3px; font-size: 13px; font-family: monospace;
    }
    .stat-bar-track {
        background: #2c2c3e; border-radius: 6px; height: 18px; overflow: hidden;
    }
    .stat-bar-fill {
        height: 100%; border-radius: 6px; transition: width 0.4s ease;
    }

    /* Task cards */
    .task-card {
        background: #1a1a2e;
        border-left: 4px solid #9b59b6;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .task-title { font-size: 15px; font-weight: bold; color: #e8e8e8; }
    .task-notes { font-size: 12px; color: #888; margin-top: 2px; }

    /* Difficulty badge */
    .diff-badge {
        display: inline-block; border-radius: 4px; padding: 2px 7px;
        font-size: 11px; font-weight: bold; margin-left: 6px;
    }

    /* Habit value bar */
    .hval-bar {
        display: inline-block; width: 80px; height: 8px;
        border-radius: 4px; vertical-align: middle; margin: 0 6px;
    }

    /* Gold display */
    .gold-display {
        font-size: 20px; font-weight: bold; color: #f1c40f;
    }

    /* Character panel */
    .char-panel {
        background: #1a1a2e; border: 1px solid #9b59b680;
        border-radius: 10px; padding: 16px; text-align: center;
    }

    /* Reward/crit toast */
    .reward-toast {
        background: #1e3a1e; border: 1px solid #27ae60;
        border-radius: 8px; padding: 10px 14px;
        color: #2ecc71; font-size: 14px; margin: 4px 0;
    }
    .crit-toast {
        background: #3a1e1e; border: 1px solid #e74c3c;
        border-radius: 8px; padding: 10px 14px;
        color: #e74c3c; font-size: 14px; margin: 4px 0;
    }

    /* Overdue badge */
    .overdue { color: #e74c3c; font-weight: bold; }
    .due-today { color: #f39c12; font-weight: bold; }
    .completed-task { opacity: 0.45; text-decoration: line-through; }
    </style>
    """, unsafe_allow_html=True)


def stat_bar_html(label: str, current: float, maximum: float,
                  color: str, icon: str) -> str:
    pct = min(100, max(0, int(current / maximum * 100))) if maximum > 0 else 0
    return f"""
    <div class="stat-bar-wrap">
        <div class="stat-bar-label">
            <span>{icon} <b>{label}</b></span>
            <span style="color:#aaa;">{current:.1f} / {maximum:.1f}</span>
        </div>
        <div class="stat-bar-track">
            <div class="stat-bar-fill" style="background: linear-gradient(90deg,{color}99,{color});
                 width:{pct}%; box-shadow: 0 0 6px {color}66;"></div>
        </div>
    </div>"""


def render_stat_bars(char: dict) -> None:
    hp_bar = stat_bar_html("HP", char["hp"], char["hp_max"], "#e74c3c", "❤️")
    xp_bar = stat_bar_html("XP", char["xp"], char["xp_to_next"], "#9b59b6", "✨")
    mp_bar = stat_bar_html("MP", char["mp"], char["mp_max"], "#3498db", "💙")
    st.markdown(hp_bar + xp_bar + mp_bar, unsafe_allow_html=True)


def render_sidebar(username: str) -> None:
    from db.queries import get_full_character
    from game.classes import CLASS_DEFINITIONS
    char = get_full_character(username)
    cls_def = CLASS_DEFINITIONS.get(char.get("class", "Warrior"), {})
    emoji = cls_def.get("emoji", "⚔️")
    color = cls_def.get("color", "#9b59b6")

    with st.sidebar:
        st.markdown(f"""
        <div class="char-panel">
            <div style="font-size:40px;">{emoji}</div>
            <div style="font-size:18px;font-weight:bold;color:#e8e8e8;">{username}</div>
            <div style="color:{color};font-size:13px;">Lv.{char['level']} {char['class']}</div>
            <div class="gold-display" style="margin-top:6px;">💰 {char['gold']:.1f}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")
        render_stat_bars(char)
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            from components.auth import logout
            logout()


def render_reward_toast(result: dict) -> None:
    if not result:
        return
    lines = []
    if result.get("crit"):
        lines.append("⚡ **CRITICAL HIT!**")
    if result.get("xp", 0) > 0:
        lines.append(f"✨ +{result['xp']:.2f} XP")
    if result.get("gold", 0) > 0:
        lines.append(f"💰 +{result['gold']:.2f} gold")
    if result.get("hp_regen", 0) > 0:
        lines.append(f"❤️ +{result['hp_regen']:.1f} HP (Regeneration)")
    if result.get("leveled_up"):
        lines.append(f"🎉 **LEVEL UP!** → Level {result['new_level']}")
    if lines:
        for line in lines:
            st.success(line)


def render_cron_banner(cron_results: list) -> None:
    if not cron_results:
        return
    total_missed = sum(r["dailies_missed"] for r in cron_results)
    total_hp = sum(r["hp_lost"] for r in cron_results)
    days = len(cron_results)
    if total_missed > 0:
        msg = f"You missed **{total_missed}** daily task(s) over **{days}** day(s) and lost **{total_hp:.1f} HP**."
        st.warning(f"⚠️ {msg}", icon=None)
    elif days > 0:
        st.info(f"✅ Cron ran for {days} day(s). No missed dailies — great job!")


def difficulty_badge(difficulty: str) -> str:
    color = DIFFICULTY_COLORS.get(difficulty, "#7f8c8d")
    emoji = DIFFICULTY_EMOJI.get(difficulty, "")
    label = difficulty.capitalize()
    return (f'<span class="diff-badge" style="background:{color}22;color:{color};'
            f'border:1px solid {color};">{emoji} {label}</span>')


def due_date_badge(due_date_str: str) -> str:
    if not due_date_str:
        return '<span style="color:#555;font-size:12px;">No due date</span>'
    try:
        due = date.fromisoformat(due_date_str)
        today = date.today()
        if due < today:
            days = (today - due).days
            return f'<span class="overdue">🔴 Overdue {days}d</span>'
        if due == today:
            return '<span class="due-today">🟡 Due Today</span>'
        days = (due - today).days
        return f'<span style="color:#aaa;font-size:12px;">📅 In {days}d</span>'
    except ValueError:
        return ""


def habit_value_display(value: float) -> str:
    color, name = habit_value_color(value)
    pct = int((value + 5) / 10 * 100)
    return (f'<div class="hval-bar" style="background:{color}33;">'
            f'<div style="width:{pct}%;height:100%;background:{color};border-radius:4px;"></div>'
            f'</div><span style="color:{color};font-size:11px;">{name} ({value:.1f})</span>')
