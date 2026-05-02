import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Character — Life Game", page_icon="👤", layout="wide")

from components.auth import require_auth
from components.ui_helpers import inject_custom_css, render_sidebar, render_stat_bars
from db.queries import get_full_character, get_equipment
from game.classes import CLASS_DEFINITIONS, use_active_skill, change_class
from game.items import ITEM_CATALOG, SLOT_ORDER, SLOT_LABELS

inject_custom_css()
username = require_auth()
render_sidebar(username)

st.title("👤 Character Sheet")

char = get_full_character(username)
equip = get_equipment(username)
cls_def = CLASS_DEFINITIONS.get(char["class"], {})

# ── Top row: portrait + bars ──────────────────────────────────────────────────
top_left, top_right = st.columns([1, 2])

with top_left:
    color = cls_def.get("color", "#9b59b6")
    emoji = cls_def.get("emoji", "⚔️")
    st.markdown(f"""
    <div class="char-panel" style="border-color:{color};">
        <div style="font-size:64px;">{emoji}</div>
        <div style="font-size:22px;font-weight:bold;color:#e8e8e8;margin-top:8px;">{username}</div>
        <div style="color:{color};font-size:16px;">Level {char['level']} {char['class']}</div>
        <div style="color:#f1c40f;font-size:20px;margin-top:6px;">💰 {char['gold']:.1f} gold</div>
        <div style="color:#555;font-size:12px;margin-top:8px;">
            XP to next level: {char['xp_to_next'] - char['xp']:.1f}
        </div>
    </div>
    """, unsafe_allow_html=True)

with top_right:
    render_stat_bars(char)

    # Stat radar chart
    stats = ["STR", "CON", "INT", "PER"]
    values = [char["strength"], char["constitution"], char["intelligence"], char["perception"]]
    fig = go.Figure(go.Scatterpolar(
        r=values + [values[0]],
        theta=stats + [stats[0]],
        fill="toself",
        line_color=cls_def.get("color", "#9b59b6"),
        fillcolor=cls_def.get("color", "#9b59b6") + "33",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#1a1a2e",
            radialaxis=dict(visible=True, range=[0, max(values) + 2], color="#555"),
            angularaxis=dict(color="#aaa"),
        ),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        margin=dict(l=20, r=20, t=20, b=20),
        height=260,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Class selector ────────────────────────────────────────────────────────────
st.subheader("Class")
cls_cols = st.columns(4)
class_names = list(CLASS_DEFINITIONS.keys())

for i, (cname, cdef) in enumerate(CLASS_DEFINITIONS.items()):
    with cls_cols[i]:
        is_current = cname == char["class"]
        border = f"border: 2px solid {cdef['color']};" if is_current else f"border: 1px solid {cdef['color']}44;"
        st.markdown(f"""
        <div style="background:#1a1a2e;{border}border-radius:8px;padding:12px;text-align:center;
                    {'opacity:1' if is_current else 'opacity:0.6'};">
            <div style="font-size:32px;">{cdef['emoji']}</div>
            <div style="font-weight:bold;color:{cdef['color']};">{cname}</div>
            <div style="font-size:11px;color:#888;margin-top:4px;">{cdef['description'][:80]}...</div>
            <div style="font-size:11px;color:#555;margin-top:6px;">
                STR:{cdef['starting_stats']['strength']}
                CON:{cdef['starting_stats']['constitution']}
                INT:{cdef['starting_stats']['intelligence']}
                PER:{cdef['starting_stats']['perception']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        if not is_current:
            if st.button(f"Switch to {cname}", key=f"cls_{cname}", use_container_width=True):
                change_class(username, cname)
                st.success(f"Class changed to {cname}! Stats reset to class defaults.")
                st.rerun()
        else:
            st.success("Current class ✓", icon=None)

st.markdown("---")

# ── Skills ────────────────────────────────────────────────────────────────────
st.subheader("Skills")
passive = cls_def.get("passive", {})
active = cls_def.get("active", {})

skill_left, skill_right = st.columns(2)

with skill_left:
    st.markdown(f"""
    <div style="background:#1a1a2e;border:1px solid #9b59b640;border-radius:8px;padding:14px;">
        <div style="font-size:11px;color:#888;text-transform:uppercase;margin-bottom:4px;">Passive Skill</div>
        <div style="font-weight:bold;color:#9b59b6;">{passive.get('name','')}</div>
        <div style="color:#aaa;font-size:13px;margin-top:4px;">{passive.get('description','')}</div>
        <div style="color:#27ae60;font-size:12px;margin-top:6px;">Always active</div>
    </div>
    """, unsafe_allow_html=True)

with skill_right:
    mp_cost = active.get("mp_cost", 0)
    can_use = char["mp"] >= mp_cost

    # Check if skill is active
    skill_active = False
    skill_status = ""
    effect = active.get("effect", "")
    if effect == "warrior_stance" and char.get("warrior_stance_date"):
        from datetime import date
        skill_active = char["warrior_stance_date"] == str(date.today())
        skill_status = "Active today ✓"
    elif effect == "mage_surge" and char.get("mage_surge_active"):
        skill_active = True
        skill_status = "Active — next task = 3x rewards ✓"
    elif effect == "rogue_crit" and char.get("rogue_crit_pending"):
        skill_active = True
        skill_status = "Active — next action guaranteed crit ✓"

    st.markdown(f"""
    <div style="background:#1a1a2e;border:1px solid #9b59b640;border-radius:8px;padding:14px;">
        <div style="font-size:11px;color:#888;text-transform:uppercase;margin-bottom:4px;">Active Skill</div>
        <div style="font-weight:bold;color:#3498db;">{active.get('name','')}</div>
        <div style="color:#aaa;font-size:13px;margin-top:4px;">{active.get('description','')}</div>
        <div style="color:#888;font-size:12px;margin-top:6px;">Cost: {mp_cost} MP
            | Current MP: {char['mp']:.1f} / {char['mp_max']:.1f}</div>
        {f'<div style="color:#27ae60;font-size:12px;margin-top:4px;">{skill_status}</div>' if skill_active else ''}
    </div>
    """, unsafe_allow_html=True)

    btn_label = f"Use: {active.get('name','')} ({mp_cost} MP)"
    if not skill_active:
        if st.button(btn_label, disabled=not can_use, use_container_width=True):
            result = use_active_skill(username, char["class"])
            if result["success"]:
                st.success(result["message"])
            else:
                st.error(result["message"])
            st.rerun()
    else:
        st.info(f"Skill active: {skill_status}")

st.markdown("---")

# ── Stats breakdown ───────────────────────────────────────────────────────────
st.subheader("Stats Breakdown")
stat_col1, stat_col2 = st.columns(2)

with stat_col1:
    st.markdown("**Base Stats** (from class + level-ups)")
    stats_data = {
        "⚔️ Strength": char["base_strength"],
        "🛡️ Constitution": char["base_constitution"],
        "🔮 Intelligence": char["base_intelligence"],
        "👁️ Perception": char["base_perception"],
    }
    for label, val in stats_data.items():
        st.metric(label, val)

with stat_col2:
    st.markdown("**Equipment Bonuses**")
    equip_data = {
        "⚔️ Strength": char["equip_strength"],
        "🛡️ Constitution": char["equip_constitution"],
        "🔮 Intelligence": char["equip_intelligence"],
        "👁️ Perception": char["equip_perception"],
    }
    for label, val in equip_data.items():
        st.metric(label, f"+{val}")

    total_bonus = sum(equip_data.values())
    st.metric("Total Equipment Bonus", f"+{total_bonus}")

st.markdown("---")

# ── Equipped gear ─────────────────────────────────────────────────────────────
st.subheader("Equipped Gear")
for slot in SLOT_ORDER:
    item_key = equip.get(f"{slot}_slot")
    if item_key and item_key in ITEM_CATALOG:
        item = ITEM_CATALOG[item_key]
        st.markdown(
            f'<div style="display:flex;align-items:center;padding:8px 0;border-bottom:1px solid #2c2c3e;">'
            f'<span style="color:#888;font-size:12px;width:120px;">{SLOT_LABELS[slot]}</span>'
            f'<span style="font-size:20px;margin-right:8px;">{item["emoji"]}</span>'
            f'<span style="color:#e8e8e8;">{item["name"]}</span>'
            f'<span style="color:#555;font-size:12px;margin-left:10px;">'
            f'STR+{item["strength"]} CON+{item["constitution"]} '
            f'INT+{item["intelligence"]} PER+{item["perception"]}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div style="display:flex;align-items:center;padding:8px 0;border-bottom:1px solid #2c2c3e;">'
            f'<span style="color:#888;font-size:12px;width:120px;">{SLOT_LABELS[slot]}</span>'
            f'<span style="color:#555;">Empty</span>'
            f'</div>',
            unsafe_allow_html=True
        )
