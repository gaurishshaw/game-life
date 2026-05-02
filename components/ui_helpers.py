import streamlit as st
from datetime import date

GOLD    = "#c9a227"
GOLD_DIM = "#8b6914"
DARK_BG  = "#0a0a0c"
CARD_BG  = "#111116"
TEXT     = "#e8dcc8"
TEXT_DIM = "#7a6f5c"

DIFFICULTY_COLORS = {
    "trivial": "#5a6068",
    "easy":    "#4a8c5c",
    "medium":  "#b87333",
    "hard":    "#8b1a1a",
}
DIFFICULTY_EMOJI  = {"trivial": "◌", "easy": "◈", "medium": "◆", "hard": "☠"}
DIFFICULTY_LABELS = {"trivial": "Trivial", "easy": "Standard", "medium": "Demanding", "hard": "Brutal"}

HABIT_VALUE_COLORS = {
    "legendary": "#c9a227",
    "strong":    "#4a90d9",
    "neutral":   "#7a6f5c",
    "weakening": "#b87333",
    "broken":    "#8b1a1a",
}

# Predefined project order for Questlines
QUESTLINE_ORDER = ["The Firm", "Nexup", "The Quant Path"]


def habit_value_color(value: float) -> tuple:
    if value >= 3.0:
        return HABIT_VALUE_COLORS["legendary"], "Legendary"
    if value >= 1.0:
        return HABIT_VALUE_COLORS["strong"],    "Strong"
    if value >= -1.0:
        return HABIT_VALUE_COLORS["neutral"],   "Neutral"
    if value >= -3.0:
        return HABIT_VALUE_COLORS["weakening"], "Weakening"
    return HABIT_VALUE_COLORS["broken"], "Broken"


def inject_custom_css() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&display=swap');

    /* ── Global ───────────────────────────────────────────────────── */
    html, body, [class*="css"] { font-family: 'Courier New', monospace; }

    h1, h2, h3 {
        font-family: 'Cinzel', Georgia, serif !important;
        color: #c9a227 !important;
        letter-spacing: 0.06em;
        text-shadow: 0 0 20px #c9a22744;
    }
    h1 { border-bottom: 1px solid #c9a22733; padding-bottom: 10px; }

    /* ── Sidebar ──────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: #080809 !important;
        border-right: 1px solid #c9a22733 !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-size: 14px !important;
    }

    /* ── Buttons ──────────────────────────────────────────────────── */
    .stButton > button {
        background: transparent !important;
        border: 1px solid #c9a22766 !important;
        color: #c9a227 !important;
        font-family: 'Courier New', monospace !important;
        letter-spacing: 0.04em;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        border-color: #c9a227 !important;
        background: #c9a22714 !important;
        box-shadow: 0 0 12px #c9a22733 !important;
    }
    .stButton > button:active {
        background: #c9a22722 !important;
    }

    /* ── Inputs ───────────────────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stSelectbox > div > div {
        background: #0d0d10 !important;
        border: 1px solid #c9a22744 !important;
        color: #e8dcc8 !important;
        font-family: 'Courier New', monospace !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea textarea:focus {
        border-color: #c9a227 !important;
        box-shadow: 0 0 8px #c9a22733 !important;
    }

    /* ── Metrics ──────────────────────────────────────────────────── */
    [data-testid="metric-container"] {
        background: #111116;
        border: 1px solid #c9a22733;
        border-radius: 4px;
        padding: 12px 16px;
    }
    [data-testid="metric-container"] label {
        color: #7a6f5c !important;
        font-size: 11px !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #c9a227 !important;
        font-family: 'Cinzel', Georgia, serif !important;
    }

    /* ── Expanders ────────────────────────────────────────────────── */
    details > summary {
        color: #c9a227 !important;
        font-family: 'Courier New', monospace !important;
        border-bottom: 1px solid #c9a22733;
        padding-bottom: 4px;
    }
    details > summary:hover { color: #e8c84a !important; }
    .streamlit-expanderHeader { color: #c9a227 !important; }

    /* ── Tabs ─────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid #c9a22733;
    }
    .stTabs [data-baseweb="tab"] {
        color: #7a6f5c !important;
        font-family: 'Courier New', monospace !important;
        letter-spacing: 0.05em;
    }
    .stTabs [aria-selected="true"] {
        color: #c9a227 !important;
        border-bottom: 2px solid #c9a227 !important;
    }

    /* ── Dividers ─────────────────────────────────────────────────── */
    hr { border-color: #c9a22728 !important; margin: 16px 0 !important; }

    /* ── Alerts ───────────────────────────────────────────────────── */
    .stAlert { border-radius: 3px !important; border-left-width: 3px !important; }

    /* ── Stat bars ────────────────────────────────────────────────── */
    .stat-bar-wrap { margin-bottom: 10px; }
    .stat-bar-label {
        display: flex; justify-content: space-between;
        margin-bottom: 3px; font-size: 12px; font-family: 'Courier New', monospace;
        letter-spacing: 0.04em;
    }
    .stat-bar-track {
        background: #1a1810; border-radius: 2px; height: 16px; overflow: hidden;
        border: 1px solid #c9a22722;
    }
    .stat-bar-fill { height: 100%; transition: width 0.4s ease; }

    /* ── Task / Quest cards ───────────────────────────────────────── */
    .task-card {
        background: #0e0e12;
        border-left: 3px solid #c9a22766;
        border-radius: 2px;
        padding: 10px 14px;
        margin-bottom: 6px;
    }
    .task-card:hover { border-left-color: #c9a227; }
    .task-title { font-size: 14px; font-weight: 600; color: #e8dcc8; letter-spacing: 0.02em; }
    .task-notes { font-size: 11px; color: #7a6f5c; margin-top: 3px; font-style: italic; }

    /* ── Questline section headers ────────────────────────────────── */
    .questline-header {
        font-family: 'Cinzel', Georgia, serif;
        font-size: 14px;
        color: #c9a227;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        border-bottom: 1px solid #c9a22744;
        padding: 6px 0 4px 0;
        margin: 18px 0 10px 0;
    }
    .questline-tag {
        display: inline-block;
        font-size: 10px;
        color: #c9a227;
        border: 1px solid #c9a22766;
        border-radius: 2px;
        padding: 1px 6px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-left: 8px;
        vertical-align: middle;
    }

    /* ── Difficulty badge ─────────────────────────────────────────── */
    .diff-badge {
        display: inline-block; border-radius: 2px; padding: 1px 6px;
        font-size: 10px; font-weight: bold; margin-left: 6px;
        letter-spacing: 0.06em; text-transform: uppercase;
    }

    /* ── Habit value bar ──────────────────────────────────────────── */
    .hval-bar {
        display: inline-block; width: 70px; height: 6px;
        border-radius: 1px; vertical-align: middle; margin: 0 6px;
    }

    /* ── Gold display ─────────────────────────────────────────────── */
    .gold-display {
        font-size: 18px; font-weight: bold; color: #c9a227;
        font-family: 'Cinzel', Georgia, serif;
        text-shadow: 0 0 10px #c9a22766;
    }

    /* ── Character panel ──────────────────────────────────────────── */
    .char-panel {
        background: #0a0a0c;
        border: 1px solid #c9a22766;
        border-radius: 3px;
        padding: 16px;
        text-align: center;
    }

    /* ── Status badges ────────────────────────────────────────────── */
    .overdue   { color: #8b1a1a; font-weight: bold; }
    .due-today { color: #b87333; font-weight: bold; }
    .completed-task { opacity: 0.35; text-decoration: line-through; }
    </style>
    """, unsafe_allow_html=True)


def stat_bar_html(label: str, current: float, maximum: float,
                  color: str, icon: str) -> str:
    pct = min(100, max(0, int(current / maximum * 100))) if maximum > 0 else 0
    return f"""
    <div class="stat-bar-wrap">
        <div class="stat-bar-label">
            <span>{icon} <b>{label}</b></span>
            <span style="color:{TEXT_DIM};">{current:.1f} / {maximum:.1f}</span>
        </div>
        <div class="stat-bar-track">
            <div class="stat-bar-fill" style="background: linear-gradient(90deg,{color}88,{color});
                 width:{pct}%; box-shadow: 0 0 8px {color}55;"></div>
        </div>
    </div>"""


def render_stat_bars(char: dict) -> None:
    hp_bar = stat_bar_html("VITALITY",  char["hp"],  char["hp_max"],  "#8b1a1a", "❤")
    xp_bar = stat_bar_html("GRACE",     char["xp"],  char["xp_to_next"], GOLD,   "✦")
    mp_bar = stat_bar_html("FOCUS",     char["mp"],  char["mp_max"],  "#2a5c8a", "◈")
    st.markdown(hp_bar + xp_bar + mp_bar, unsafe_allow_html=True)


def render_sidebar(username: str) -> None:
    from db.queries import get_full_character
    from game.classes import CLASS_DEFINITIONS
    char = get_full_character(username)
    cls_def = CLASS_DEFINITIONS.get(char.get("class", "Warrior"), {})
    emoji = cls_def.get("emoji", "⚔️")

    with st.sidebar:
        st.markdown(f"""
        <div class="char-panel">
            <div style="font-size:36px;">{emoji}</div>
            <div style="font-family:'Cinzel',serif;font-size:15px;color:{GOLD};
                        letter-spacing:0.08em;margin-top:6px;">{username.upper()}</div>
            <div style="color:{TEXT_DIM};font-size:11px;letter-spacing:0.1em;text-transform:uppercase;">
                Lv.{char['level']} &nbsp;·&nbsp; {char['class']}</div>
            <div class="gold-display" style="margin-top:8px;">⬡ {char['gold']:.1f}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")
        render_stat_bars(char)
        st.markdown("---")
        if st.button("◁  Leave", use_container_width=True):
            from components.auth import logout
            logout()


def render_reward_toast(result: dict) -> None:
    if not result:
        return
    lines = []
    if result.get("crit"):
        lines.append("⚡ **CRITICAL STRIKE**")
    if result.get("xp", 0) > 0:
        lines.append(f"✦ +{result['xp']:.2f} Grace")
    if result.get("gold", 0) > 0:
        lines.append(f"⬡ +{result['gold']:.2f} Gold")
    if result.get("hp_regen", 0) > 0:
        lines.append(f"❤ +{result['hp_regen']:.1f} Vitality restored")
    if result.get("leveled_up"):
        lines.append(f"◈ **ASCENDED** → Level {result['new_level']}")
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
        st.warning(
            f"⚠ You faltered on **{total_missed}** protocol(s) across **{days}** day(s). "
            f"Lost **{total_hp:.1f}** Vitality."
        )
    elif days > 0:
        st.info(f"✦ Protocols held for {days} day(s). Discipline intact.")


def difficulty_badge(difficulty: str) -> str:
    color = DIFFICULTY_COLORS.get(difficulty, TEXT_DIM)
    symbol = DIFFICULTY_EMOJI.get(difficulty, "◌")
    label  = DIFFICULTY_LABELS.get(difficulty, difficulty.capitalize())
    return (f'<span class="diff-badge" style="background:{color}18;color:{color};'
            f'border:1px solid {color}55;">{symbol} {label}</span>')


def due_date_badge(due_date_str: str) -> str:
    if not due_date_str:
        return f'<span style="color:{TEXT_DIM};font-size:11px;">Open-ended</span>'
    try:
        due = date.fromisoformat(due_date_str)
        today = date.today()
        if due < today:
            days = (today - due).days
            return f'<span class="overdue">▲ Overdue {days}d</span>'
        if due == today:
            return '<span class="due-today">◆ Due Today</span>'
        days = (due - today).days
        return f'<span style="color:{TEXT_DIM};font-size:11px;">◇ In {days}d</span>'
    except ValueError:
        return ""


def habit_value_display(value: float) -> str:
    color, name = habit_value_color(value)
    pct = int((value + 5) / 10 * 100)
    return (f'<div class="hval-bar" style="background:{color}22;border:1px solid {color}44;">'
            f'<div style="width:{pct}%;height:100%;background:{color};"></div>'
            f'</div><span style="color:{color};font-size:11px;letter-spacing:0.04em;">'
            f'{name} ({value:+.1f})</span>')


def questline_section_header(tag: str, count: int) -> str:
    return (f'<div class="questline-header">◈ {tag.upper()}'
            f'<span style="color:{TEXT_DIM};font-size:11px;margin-left:10px;">'
            f'{count} quest{"s" if count != 1 else ""}</span></div>')
