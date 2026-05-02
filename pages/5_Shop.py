import streamlit as st

st.set_page_config(page_title="Shop — Life Game", page_icon="🛒", layout="wide")

from components.auth import require_auth
from components.ui_helpers import inject_custom_css, render_sidebar
from db.queries import (get_full_character, get_inventory, get_equipment,
                        buy_equipment, equip_item, unequip_slot,
                        get_custom_rewards, create_custom_reward,
                        update_custom_reward, delete_custom_reward, buy_custom_reward,
                        get_daily_gold_avg)
from game.items import ITEM_CATALOG, get_items_by_slot, SLOT_ORDER, SLOT_LABELS, TIER_COLORS

inject_custom_css()
username = require_auth()
render_sidebar(username)

char = get_full_character(username)
owned = get_inventory(username)
equip = get_equipment(username)

st.title("🛒 Shop")
st.markdown(
    f'<div class="gold-display" style="margin-bottom:16px;">💰 {char["gold"]:.1f} gold available</div>',
    unsafe_allow_html=True
)

tab_equip, tab_rewards = st.tabs(["⚔️ Equipment", "🎁 Custom Rewards"])

# ─── EQUIPMENT TAB ────────────────────────────────────────────────────────────
with tab_equip:
    slot_tabs = st.tabs([SLOT_LABELS[s] for s in SLOT_ORDER])

    for slot_tab, slot in zip(slot_tabs, SLOT_ORDER):
        with slot_tab:
            items = get_items_by_slot(slot)
            equipped_key = equip.get(f"{slot}_slot")

            if equipped_key:
                eq_item = ITEM_CATALOG.get(equipped_key, {})
                st.markdown(
                    f'<div style="background:#0d2b0d;border:1px solid #27ae60;border-radius:8px;'
                    f'padding:10px;margin-bottom:14px;">'
                    f'<span style="color:#27ae60;font-weight:bold;">Currently Equipped:</span> '
                    f'{eq_item.get("emoji","?")} {eq_item.get("name","?")} — '
                    f'STR+{eq_item.get("strength",0)} CON+{eq_item.get("constitution",0)} '
                    f'INT+{eq_item.get("intelligence",0)} PER+{eq_item.get("perception",0)}'
                    f'</div>',
                    unsafe_allow_html=True
                )
                if st.button(f"Unequip {eq_item.get('name','')}", key=f"unequip_{slot}"):
                    unequip_slot(username, slot)
                    st.rerun()

            cols = st.columns(3)
            for idx, item in enumerate(items):
                with cols[idx % 3]:
                    is_equipped = item["key"] == equipped_key
                    is_owned = item["key"] in owned
                    tier_color = TIER_COLORS.get(item["tier"], "#7f8c8d")

                    st.markdown(
                        f'<div style="background:#1a1a2e;border:1px solid {tier_color}44;'
                        f'border-radius:8px;padding:14px;margin-bottom:10px;'
                        f'{"border-color:" + tier_color + ";" if is_equipped else ""}'
                        f'">'
                        f'<div style="font-size:24px;">{item["emoji"]}</div>'
                        f'<div style="font-weight:bold;color:#e8e8e8;">{item["name"]}</div>'
                        f'<div style="font-size:11px;color:{tier_color};margin:3px 0;">Tier {item["tier"]}</div>'
                        f'<div style="font-size:12px;color:#888;margin-bottom:8px;">{item["description"]}</div>'
                        f'<div style="font-size:13px;">'
                        f'{"⚔️ +" + str(item["strength"]) if item["strength"] else ""} '
                        f'{"🛡️ +" + str(item["constitution"]) if item["constitution"] else ""} '
                        f'{"🔮 +" + str(item["intelligence"]) if item["intelligence"] else ""} '
                        f'{"👁️ +" + str(item["perception"]) if item["perception"] else ""}'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    if is_equipped:
                        st.success("Equipped ✓", icon=None)
                    elif is_owned:
                        if st.button("Equip", key=f"equip_{item['key']}", use_container_width=True):
                            res = equip_item(username, item["key"])
                            if res["success"]:
                                st.success(res["message"])
                            else:
                                st.error(res["message"])
                            st.rerun()
                    else:
                        can_afford = char["gold"] >= item["gold_cost"]
                        label = f"Buy — {item['gold_cost']}g"
                        if st.button(label, key=f"buy_{item['key']}",
                                     use_container_width=True, disabled=not can_afford):
                            res = buy_equipment(username, item["key"])
                            if res["success"]:
                                st.success(res["message"])
                            else:
                                st.error(res["message"])
                            st.rerun()
                        if not can_afford:
                            st.caption(f"Need {item['gold_cost'] - char['gold']:.1f} more gold")

# ─── CUSTOM REWARDS TAB ───────────────────────────────────────────────────────
with tab_rewards:
    st.subheader("Your Custom Rewards")
    st.caption("Define real-life treats and buy them with gold when you've earned it.")

    with st.expander("➕ Add Custom Reward", expanded=False):

        # ── Merchant's Oracle ─────────────────────────────────────────────────
        avg_wage = get_daily_gold_avg(username)
        oracle_on = st.session_state.get("oracle_visible", False)

        oc_left, oc_right = st.columns([5, 2])
        with oc_left:
            src = "7-day rolling average" if avg_wage != 50.0 else "default (no history yet)"
            st.markdown(
                f'<div style="font-family:\'Cinzel\',serif;font-size:12px;'
                f'color:#c9a22799;letter-spacing:0.08em;padding-top:6px;">'
                f'⚗ MERCHANT\'S ORACLE'
                f'<span style="font-family:\'Courier New\',monospace;font-size:10px;'
                f'color:#7a6f5c;margin-left:10px;letter-spacing:0.04em;">'
                f'Daily Wage: {avg_wage:.1f} ⬡ &nbsp;·&nbsp; {src}</span></div>',
                unsafe_allow_html=True
            )
        with oc_right:
            toggle_label = "▲ Close Oracle" if oracle_on else "⚗ Consult the Oracle"
            if st.button(toggle_label, key="oracle_toggle", use_container_width=True):
                st.session_state["oracle_visible"] = not oracle_on
                st.rerun()

        # ── Tier selection panel ──────────────────────────────────────────────
        if st.session_state.get("oracle_visible", False):
            ORACLE_TIERS = [
                ("◌", "Tier I",   "Consumable", 4,   "Minor treats & outings"),
                ("◈", "Tier II",  "Rare Drop",  14,  "Items & clothing"),
                ("◆", "Tier III", "Boss Loot",  45,  "Major milestones & trips"),
                ("☠", "Tier IV",  "Legendary",  120, "High-value assets"),
            ]
            st.markdown(
                '<div style="background:#0a0a0c;border:1px solid #c9a22733;'
                'border-radius:3px;padding:14px 12px;margin:8px 0 6px 0;">',
                unsafe_allow_html=True
            )
            tier_cols = st.columns(4)
            for i, (sym, tier_num, tier_name, mult, desc) in enumerate(ORACLE_TIERS):
                price = max(10, round(avg_wage * mult / 10) * 10)
                with tier_cols[i]:
                    st.markdown(
                        f'<div style="text-align:center;padding:4px 0 8px 0;">'
                        f'<div style="font-family:\'Cinzel\',serif;font-size:13px;'
                        f'color:#c9a227;letter-spacing:0.06em;">{sym} {tier_num}</div>'
                        f'<div style="font-size:11px;color:#e8dcc8;margin:3px 0;'
                        f'font-weight:bold;">{tier_name}</div>'
                        f'<div style="font-size:10px;color:#7a6f5c;font-style:italic;'
                        f'margin-bottom:6px;">{desc}</div>'
                        f'<div style="font-size:11px;color:#7a6f5c;">'
                        f'{avg_wage:.0f} ⬡ × {mult}d</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    if st.button(f"{price} ⬡", key=f"oracle_tier_{i}",
                                 use_container_width=True):
                        st.session_state["oracle_price"]     = float(price)
                        st.session_state["oracle_days"]      = mult
                        st.session_state["oracle_tier_name"] = tier_name
                        st.session_state["oracle_visible"]   = False
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Oracle explanation (shown after a tier is chosen) ─────────────────
        if "oracle_price" in st.session_state:
            op   = st.session_state["oracle_price"]
            od   = st.session_state.get("oracle_days", "?")
            otn  = st.session_state.get("oracle_tier_name", "")
            st.markdown(
                f'<div style="background:#0d0d10;border-left:3px solid #c9a22766;'
                f'padding:7px 12px;margin:4px 0 10px 0;border-radius:2px;">'
                f'<span style="color:#c9a227;font-size:13px;">⚗</span> '
                f'<span style="color:#e8dcc8;font-size:13px;">'
                f'Priced at <b>{op:.0f} Gold</b></span> '
                f'<span style="color:#7a6f5c;font-size:12px;">'
                f'— Requires ~{od} perfect days of effort &nbsp;·&nbsp; {otn}'
                f'</span></div>',
                unsafe_allow_html=True
            )

        # ── Creation form ─────────────────────────────────────────────────────
        with st.form("add_reward_form", clear_on_submit=True):
            r_title = st.text_input("Reward name *",
                                    placeholder="e.g. Feast at a social venue with the guild")
            r_notes = st.text_input("Notes", placeholder="Optional flavour text")
            r_cost  = st.number_input("Gold cost ⬡", min_value=1.0,
                                      value=float(st.session_state.get("oracle_price", 20.0)),
                                      step=5.0)
            if st.form_submit_button("Create Reward", use_container_width=True):
                if r_title.strip():
                    create_custom_reward(username, r_title.strip(), r_notes.strip(), r_cost)
                    for _k in ("oracle_price", "oracle_days", "oracle_tier_name", "oracle_visible"):
                        st.session_state.pop(_k, None)
                    st.success(f"Added: {r_title}")
                    st.rerun()
                else:
                    st.error("Name is required.")

    rewards = get_custom_rewards(username)
    if not rewards:
        st.info("No custom rewards yet. Add one above!")
    else:
        for r in rewards:
            rc1, rc2, rc3 = st.columns([5, 2, 1])
            with rc1:
                st.markdown(
                    f'<div style="padding:8px 0;">'
                    f'<span class="task-title">{r["title"]}</span>'
                    + (f'<div class="task-notes">{r["notes"]}</div>' if r["notes"] else "")
                    + '</div>',
                    unsafe_allow_html=True
                )
            with rc2:
                can_afford = char["gold"] >= r["gold_cost"]
                label = f"Redeem — {r['gold_cost']:.0f}g"
                if st.button(label, key=f"redeem_{r['id']}",
                             use_container_width=True, disabled=not can_afford):
                    res = buy_custom_reward(username, r["id"])
                    if res["success"]:
                        st.success(res["message"])
                        st.balloons()
                    else:
                        st.error(res["message"])
                    st.rerun()
                if not can_afford:
                    st.caption(f"Need {r['gold_cost'] - char['gold']:.1f} more gold")
            with rc3:
                if st.button("🗑️", key=f"del_reward_{r['id']}"):
                    delete_custom_reward(r["id"])
                    st.rerun()

            with st.expander(f"Edit: {r['title'][:45]}...", expanded=False):
                with st.form(f"edit_reward_{r['id']}", clear_on_submit=False):
                    er_title = st.text_input("Reward name", value=r["title"])
                    er_notes = st.text_input("Notes", value=r["notes"] or "")
                    er_cost = st.number_input("Gold cost", min_value=1.0,
                                              value=float(r["gold_cost"]), step=5.0)
                    if st.form_submit_button("Save", use_container_width=True):
                        if er_title.strip():
                            update_custom_reward(r["id"], title=er_title.strip(),
                                                 notes=er_notes.strip(), gold_cost=er_cost)
                            st.success("Reward updated.")
                            st.rerun()
                        else:
                            st.error("Name is required.")

            st.markdown('<hr style="border-color:#2c2c3e;margin:4px 0;">', unsafe_allow_html=True)
