import streamlit as st

st.set_page_config(page_title="Shop — Life Game", page_icon="🛒", layout="wide")

from components.auth import require_auth
from components.ui_helpers import inject_custom_css, render_sidebar
from db.queries import (get_full_character, get_inventory, get_equipment,
                        buy_equipment, equip_item, unequip_slot,
                        get_custom_rewards, create_custom_reward,
                        delete_custom_reward, buy_custom_reward)
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
        with st.form("add_reward_form", clear_on_submit=True):
            r_title = st.text_input("Reward name *", placeholder="e.g. Watch a movie")
            r_notes = st.text_input("Notes", placeholder="e.g. 2h on Netflix")
            r_cost = st.number_input("Gold cost", min_value=1.0, value=20.0, step=5.0)
            if st.form_submit_button("Create Reward", use_container_width=True):
                if r_title.strip():
                    create_custom_reward(username, r_title.strip(), r_notes.strip(), r_cost)
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
            st.markdown('<hr style="border-color:#2c2c3e;margin:4px 0;">', unsafe_allow_html=True)
