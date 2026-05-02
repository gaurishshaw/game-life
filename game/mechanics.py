import math
import random


DIFFICULTY_MULT = {"trivial": 0.1, "easy": 1.0, "medium": 1.5, "hard": 2.0}


def calc_xp_to_next(level: int) -> float:
    return math.floor(level * 150 * (1 + level * 0.3))


def calc_hp_max(level: int, constitution: int, class_name: str) -> float:
    from game.classes import CLASS_DEFINITIONS
    hp_bonus = CLASS_DEFINITIONS.get(class_name, {}).get("hp_bonus", 0)
    return 50.0 + (level - 1) * 5.0 + constitution * 2.5 + hp_bonus


def calc_mp_max(level: int, intelligence: int, class_name: str) -> float:
    from game.classes import CLASS_DEFINITIONS
    mp_bonus = CLASS_DEFINITIONS.get(class_name, {}).get("mp_bonus", 0)
    return 30.0 + intelligence * 2.0 + mp_bonus


def check_crit(character: dict) -> bool:
    from game.classes import CLASS_DEFINITIONS
    cls = character.get("class", "Warrior")
    crit_base = CLASS_DEFINITIONS.get(cls, {}).get("crit_base", 0.03)
    per = character.get("perception", 1)
    if character.get("rogue_crit_pending"):
        return True
    return random.random() < (crit_base + per * 0.002)


def calc_xp_reward(difficulty: str, character: dict, habit_value: float = 1.0,
                   streak: int = 0, task_type: str = "daily") -> tuple:
    """Returns (xp_amount, crit_bool)."""
    from game.classes import CLASS_DEFINITIONS
    base = DIFFICULTY_MULT.get(difficulty, 1.0)
    streak_mult = min(2.0, 1.0 + streak * 0.02)
    cls = character.get("class", "Warrior")
    primary = CLASS_DEFINITIONS.get(cls, {}).get("xp_primary_stat", "strength")
    stat_mult = 1.0 + character.get(primary, 1) * 0.025
    habit_mult = max(0.1, 1.0 + habit_value * 0.1)

    crit = check_crit(character)
    crit_mult = 1.5 if crit else 1.0

    # Mage surge: 3x everything on next task
    if character.get("mage_surge_active"):
        crit_mult = 3.0
        crit = True

    # Mage passive: 1.2x XP always
    class_mult = 1.0
    if cls == "Mage":
        class_mult = CLASS_DEFINITIONS["Mage"]["passive"]["value"]

    xp = base * streak_mult * stat_mult * habit_mult * crit_mult * class_mult
    return round(max(0.1, xp), 2), crit


def calc_gold_reward(difficulty: str, character: dict, habit_value: float = 1.0,
                     task_type: str = "daily") -> float:
    from game.classes import CLASS_DEFINITIONS
    base = DIFFICULTY_MULT.get(difficulty, 1.0)
    per_mult = 1.0 + character.get("perception", 1) * 0.02
    habit_mult = max(0.1, 1.0 + habit_value * 0.1)

    class_mult = 1.0
    cls = character.get("class", "Warrior")
    if cls == "Rogue":
        class_mult = CLASS_DEFINITIONS["Rogue"]["passive"]["value"]  # 1.3x

    surge_mult = 3.0 if character.get("mage_surge_active") else 1.0

    gold = base * per_mult * habit_mult * class_mult * surge_mult
    return round(max(0.1, gold), 2)


def daily_miss_damage(character: dict, task: dict) -> float:
    from game.classes import CLASS_DEFINITIONS
    diff_dmg = {"trivial": 0.1, "easy": 1.0, "medium": 1.5, "hard": 2.0}
    base = diff_dmg.get(task.get("difficulty", "easy"), 1.0)
    con = character.get("constitution", 1)
    con_reduction = 1.0 - min(0.80, con * 0.01)
    streak = task.get("streak", 0)
    streak_factor = max(0.5, streak * 0.02 + 1.0)
    damage = base * con_reduction * streak_factor
    cls = character.get("class", "Warrior")
    if cls == "Warrior":
        damage *= (1.0 - CLASS_DEFINITIONS["Warrior"]["passive"]["value"])
    # Defensive Stance: checked in cron
    return round(max(0.01, damage), 2)


def apply_xp(username: str, xp_amount: float) -> dict:
    from db.queries import get_character, update_character
    from game.classes import apply_level_up_stats
    char = get_character(username)
    new_xp = char["xp"] + xp_amount
    level = char["level"]
    xp_to_next = char["xp_to_next"]
    leveled_up = False

    while new_xp >= xp_to_next:
        new_xp -= xp_to_next
        level += 1
        xp_to_next = calc_xp_to_next(level)
        leveled_up = True
        apply_level_up_stats(username, char["class"])
        from db.queries import log_activity
        log_activity(username, "level_up", detail={"new_level": level})

    update_character(username, xp=new_xp, xp_to_next=xp_to_next, level=level)
    if leveled_up:
        fresh = get_character(username)
        update_character(username,
                         hp=fresh["hp_max"],
                         mp=fresh["mp_max"])
    return {"leveled_up": leveled_up, "new_level": level, "new_xp": new_xp}


def apply_gold(username: str, gold_delta: float) -> float:
    from db.queries import get_character, update_character
    char = get_character(username)
    new_gold = max(0.0, round(char["gold"] + gold_delta, 2))
    update_character(username, gold=new_gold)
    return new_gold


def recalculate_stats(username: str) -> dict:
    from db.queries import get_character, get_equipment, update_character
    from game.items import get_stat_bonuses_from_equipment
    char = get_character(username)
    equip = get_equipment(username)
    bonuses = get_stat_bonuses_from_equipment(equip)
    total_con = char["constitution"] + bonuses["constitution"]
    total_int = char["intelligence"] + bonuses["intelligence"]
    new_hp_max = calc_hp_max(char["level"], total_con, char["class"])
    new_mp_max = calc_mp_max(char["level"], total_int, char["class"])
    update_character(username,
                     hp_max=new_hp_max,
                     mp_max=new_mp_max,
                     hp=min(char["hp"], new_hp_max),
                     mp=min(char["mp"], new_mp_max))
    return get_character(username)
