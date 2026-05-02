CLASS_DEFINITIONS = {
    "Warrior": {
        "starting_stats": {"strength": 7, "constitution": 5, "intelligence": 1, "perception": 2},
        "level_up_stats": {"strength": 2, "constitution": 1, "intelligence": 0, "perception": 0},
        "hp_bonus": 30,
        "mp_bonus": 0,
        "crit_base": 0.03,
        "xp_primary_stat": "strength",
        "passive": {
            "name": "Iron Will",
            "description": "Reduces all daily miss damage by 15%.",
            "effect": "dmg_reduction",
            "value": 0.15,
        },
        "active": {
            "name": "Defensive Stance",
            "description": "For the rest of today, daily miss damage is reduced by an additional 50%.",
            "mp_cost": 10,
            "effect": "warrior_stance",
        },
        "description": "A stalwart fighter who excels at withstanding damage from missed dailies. High HP and CON make failures sting less.",
        "emoji": "⚔️",
        "color": "#e74c3c",
    },
    "Mage": {
        "starting_stats": {"strength": 1, "constitution": 1, "intelligence": 7, "perception": 4},
        "level_up_stats": {"strength": 0, "constitution": 0, "intelligence": 3, "perception": 1},
        "hp_bonus": 0,
        "mp_bonus": 20,
        "crit_base": 0.03,
        "xp_primary_stat": "intelligence",
        "passive": {
            "name": "Arcane Amplifier",
            "description": "Gain 20% bonus XP from all completed tasks.",
            "effect": "xp_multiplier",
            "value": 1.2,
        },
        "active": {
            "name": "Arcane Surge",
            "description": "Your next task completion grants triple XP and gold.",
            "mp_cost": 25,
            "effect": "mage_surge",
        },
        "description": "A powerful spellcaster who levels up fast thanks to bonus XP. High MP and INT make skills more potent.",
        "emoji": "🔮",
        "color": "#9b59b6",
    },
    "Healer": {
        "starting_stats": {"strength": 2, "constitution": 6, "intelligence": 4, "perception": 3},
        "level_up_stats": {"strength": 0, "constitution": 2, "intelligence": 1, "perception": 1},
        "hp_bonus": 20,
        "mp_bonus": 10,
        "crit_base": 0.03,
        "xp_primary_stat": "constitution",
        "passive": {
            "name": "Regeneration",
            "description": "Restore 3 HP each time you complete a daily.",
            "effect": "daily_hp_regen",
            "value": 3.0,
        },
        "active": {
            "name": "Mending Light",
            "description": "Restore 25 HP immediately.",
            "mp_cost": 20,
            "effect": "heal",
        },
        "description": "A resilient healer who regains HP from completing dailies. High CON and an HP bonus make staying alive easy.",
        "emoji": "💚",
        "color": "#27ae60",
    },
    "Rogue": {
        "starting_stats": {"strength": 4, "constitution": 2, "intelligence": 2, "perception": 7},
        "level_up_stats": {"strength": 1, "constitution": 0, "intelligence": 1, "perception": 2},
        "hp_bonus": 0,
        "mp_bonus": 0,
        "crit_base": 0.08,
        "xp_primary_stat": "perception",
        "passive": {
            "name": "Opportunist",
            "description": "Earn 30% more gold from all completed tasks.",
            "effect": "gold_multiplier",
            "value": 1.3,
        },
        "active": {
            "name": "Shadow Step",
            "description": "Guarantee a critical hit on your next habit or daily completion.",
            "mp_cost": 15,
            "effect": "rogue_crit",
        },
        "description": "A cunning rogue who earns more gold and crits more often. High PER and a gold bonus make the shop very accessible.",
        "emoji": "🗡️",
        "color": "#f39c12",
    },
}


def get_class_definition(class_name: str) -> dict:
    if class_name not in CLASS_DEFINITIONS:
        raise ValueError(f"Unknown class: {class_name}")
    return CLASS_DEFINITIONS[class_name]


def apply_level_up_stats(username: str, class_name: str) -> None:
    from db.queries import get_character, update_character
    from game.mechanics import calc_hp_max, calc_mp_max
    cls = CLASS_DEFINITIONS[class_name]
    delta = cls["level_up_stats"]
    char = get_character(username)
    new_str = char["strength"] + delta["strength"]
    new_con = char["constitution"] + delta["constitution"]
    new_int = char["intelligence"] + delta["intelligence"]
    new_per = char["perception"] + delta["perception"]
    new_hp_max = calc_hp_max(char["level"], new_con + char.get("equip_constitution", 0), class_name)
    new_mp_max = calc_mp_max(char["level"], new_int + char.get("equip_intelligence", 0), class_name)
    update_character(username,
                     strength=new_str,
                     constitution=new_con,
                     intelligence=new_int,
                     perception=new_per,
                     hp_max=new_hp_max,
                     mp_max=new_mp_max,
                     hp=new_hp_max,
                     mp=new_mp_max)


def use_active_skill(username: str, class_name: str) -> dict:
    from db.queries import get_character, update_character
    from datetime import date
    cls = CLASS_DEFINITIONS[class_name]
    active = cls["active"]
    char = get_character(username)

    if char["mp"] < active["mp_cost"]:
        return {"success": False, "message": f"Not enough MP (need {active['mp_cost']}, have {char['mp']:.1f})"}

    new_mp = char["mp"] - active["mp_cost"]
    updates = {"mp": new_mp}
    effect = active["effect"]

    if effect == "warrior_stance":
        updates["warrior_stance_date"] = str(date.today())
    elif effect == "mage_surge":
        updates["mage_surge_active"] = 1
    elif effect == "heal":
        updates["hp"] = min(char["hp"] + 25.0, char["hp_max"])
    elif effect == "rogue_crit":
        updates["rogue_crit_pending"] = 1

    update_character(username, **updates)

    from db.queries import log_activity
    log_activity(username, "skill_use", mp_delta=-active["mp_cost"],
                 detail={"skill": active["name"], "class": class_name})

    return {"success": True, "message": f"{active['name']} activated!"}


def change_class(username: str, new_class: str) -> None:
    """Reset base stats to new class starting stats and recalculate HP/MP."""
    from db.queries import update_character
    from game.mechanics import calc_hp_max, calc_mp_max, calc_xp_to_next
    if new_class not in CLASS_DEFINITIONS:
        raise ValueError(f"Unknown class: {new_class}")
    cls = CLASS_DEFINITIONS[new_class]
    ss = cls["starting_stats"]
    from db.queries import get_character
    char = get_character(username)
    hp_max = calc_hp_max(char["level"], ss["constitution"], new_class)
    mp_max = calc_mp_max(char["level"], ss["intelligence"], new_class)
    update_character(username,
                     strength=ss["strength"],
                     constitution=ss["constitution"],
                     intelligence=ss["intelligence"],
                     perception=ss["perception"],
                     hp_max=hp_max,
                     mp_max=mp_max,
                     hp=min(char["hp"], hp_max),
                     mp=min(char["mp"], mp_max),
                     mage_surge_active=0,
                     warrior_stance_date=None,
                     rogue_crit_pending=0)
    # update_character uses **kwargs so 'class' needs special handling
    from db.models import get_connection
    conn = get_connection()
    with conn:
        conn.execute("UPDATE characters SET class=? WHERE username=?", (new_class, username))
    conn.close()
