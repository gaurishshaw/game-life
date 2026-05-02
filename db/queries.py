import json
import sqlite3
from datetime import datetime
from db.models import get_connection


def _row_to_dict(row) -> dict:
    return dict(row) if row else {}


# ─── USERS & CHARACTER ───────────────────────────────────────────────────────

def _seed_initial_data(username: str) -> None:
    """Populate defaults for a brand-new user. Runs exactly once per account."""
    # Dailies — non-negotiables
    create_daily(username,
                 "Nutrition Protocol",
                 "Execute 8-week rotational meal plan (Strict: No curd, no chutney).",
                 "hard", "daily", list(range(7)))
    create_daily(username,
                 "Physical Conditioning",
                 "Complete daily boxing and home workout split.",
                 "hard", "daily", list(range(7)))

    # Habits — the grind
    create_habit(username, "Study Ancient Texts",
                 "Dostoyevsky, Brontë, Herbert — the great works", True, False, "medium")
    create_habit(username, "Bardic Practice",
                 "Guitar, Piano, Singing", True, False, "medium")
    create_habit(username, "Agility Training",
                 "Kick the Jianzi shuttlecock", True, False, "easy")
    create_habit(username, "Arcane Engineering",
                 "Build and troubleshoot Agentic AI prototypes", True, False, "hard")

    # Questlines — tagged by project
    create_todo(username,
                "Advance to the next chapter of the Quantitative Finance syllabus",
                "", "hard", None, 0, "The Quant Path")
    create_todo(username,
                "Draft the technical roadmap for AI process consulting",
                "Strict constraint: Exclude all FP&A scope.", "hard", None, 0, "Nexup")
    create_todo(username,
                "Complete the Agentic Trade Finance UI wireframes",
                "", "medium", None, 0, "The Firm")

    # Custom rewards — grind for these
    create_custom_reward(username,
                         "Acquire a new garment for the Capsule Arsenal",
                         "A high-quality dark piece worthy of the wardrobe.", 500.0)
    create_custom_reward(username,
                         "Commission a Seiko Presage for the Collection",
                         "The next timepiece. Earned, not bought on impulse.", 5000.0)
    create_custom_reward(username,
                         "Fund a multi-city expedition — night sky & illuminated architecture",
                         "Photography pilgrimage. Weeks of grinding made visible.", 2500.0)
    create_custom_reward(username,
                         "Feast at a vibrant social venue with the guild",
                         "Dinner and drinks with a worthy company of adventurers.", 300.0)


def ensure_user_exists(username: str) -> None:
    from game.classes import CLASS_DEFINITIONS
    conn = get_connection()
    is_new = False
    with conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (username) VALUES (?)", (username,)
        )
        conn.execute("UPDATE users SET last_login=datetime('now') WHERE username=?", (username,))
        existing = conn.execute(
            "SELECT 1 FROM characters WHERE username=?", (username,)
        ).fetchone()
        if not existing:
            cls = CLASS_DEFINITIONS["Warrior"]
            ss = cls["starting_stats"]
            from game.mechanics import calc_hp_max, calc_mp_max, calc_xp_to_next
            hp_max = calc_hp_max(1, ss["constitution"], "Warrior")
            mp_max = calc_mp_max(1, ss["intelligence"], "Warrior")
            xp_to_next = calc_xp_to_next(1)
            conn.execute("""
                INSERT INTO characters
                    (username, class, level, xp, xp_to_next, hp, hp_max, mp, mp_max,
                     gold, strength, constitution, intelligence, perception)
                VALUES (?,?,1,0,?,?,?,?,?,0,?,?,?,?)
            """, (username, "Warrior", xp_to_next, hp_max, hp_max, mp_max, mp_max,
                  ss["strength"], ss["constitution"], ss["intelligence"], ss["perception"]))
            conn.execute("INSERT INTO equipment (username) VALUES (?)", (username,))
            is_new = True
    conn.close()
    if is_new:
        _seed_initial_data(username)


def get_character(username: str) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM characters WHERE username=?", (username,)
    ).fetchone()
    conn.close()
    return _row_to_dict(row)


def update_character(username: str, **kwargs) -> None:
    if not kwargs:
        return
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [username]
    conn = get_connection()
    with conn:
        conn.execute(f"UPDATE characters SET {fields} WHERE username=?", values)
    conn.close()


def get_equipment(username: str) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM equipment WHERE username=?", (username,)
    ).fetchone()
    conn.close()
    return _row_to_dict(row)


def get_full_character(username: str) -> dict:
    """Returns character dict with effective stats (base + equipment bonuses) merged in."""
    from game.items import get_stat_bonuses_from_equipment
    char = get_character(username)
    equip = get_equipment(username)
    bonuses = get_stat_bonuses_from_equipment(equip)
    char["base_strength"] = char["strength"]
    char["base_constitution"] = char["constitution"]
    char["base_intelligence"] = char["intelligence"]
    char["base_perception"] = char["perception"]
    char["equip_strength"] = bonuses["strength"]
    char["equip_constitution"] = bonuses["constitution"]
    char["equip_intelligence"] = bonuses["intelligence"]
    char["equip_perception"] = bonuses["perception"]
    char["strength"] = char["base_strength"] + bonuses["strength"]
    char["constitution"] = char["base_constitution"] + bonuses["constitution"]
    char["intelligence"] = char["base_intelligence"] + bonuses["intelligence"]
    char["perception"] = char["base_perception"] + bonuses["perception"]
    return char


# ─── HABITS ──────────────────────────────────────────────────────────────────

def get_habits(username: str, active_only: bool = True) -> list:
    conn = get_connection()
    q = "SELECT * FROM habits WHERE username=?"
    params = [username]
    if active_only:
        q += " AND is_active=1"
    q += " ORDER BY created_at"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def create_habit(username: str, title: str, notes: str, positive: bool,
                 negative: bool, difficulty: str) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute("""
            INSERT INTO habits (username, title, notes, positive, negative, difficulty)
            VALUES (?,?,?,?,?,?)
        """, (username, title, notes, int(positive), int(negative), difficulty))
    conn.close()
    return cur.lastrowid


def update_habit(habit_id: int, **kwargs) -> None:
    if not kwargs:
        return
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [habit_id]
    conn = get_connection()
    with conn:
        conn.execute(f"UPDATE habits SET {fields} WHERE id=?", values)
    conn.close()


def delete_habit(habit_id: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute("UPDATE habits SET is_active=0 WHERE id=?", (habit_id,))
    conn.close()


def record_habit_click(username: str, habit_id: int, direction: str) -> dict:
    """Click a habit + or -. Returns reward dict."""
    from game.mechanics import calc_xp_reward, calc_gold_reward, check_crit, apply_xp, apply_gold
    conn = get_connection()
    habit = _row_to_dict(conn.execute(
        "SELECT * FROM habits WHERE id=? AND username=?", (habit_id, username)
    ).fetchone())
    conn.close()

    char = get_full_character(username)

    xp_earned, crit = calc_xp_reward(
        habit["difficulty"], char, habit_value=habit["value"], task_type="habit"
    )
    gold_earned = calc_gold_reward(habit["difficulty"], char, habit_value=habit["value"], task_type="habit")
    if crit:
        gold_earned *= 1.5

    if direction == "up":
        delta = 1.0 if habit["value"] < 1.0 else 0.5
        new_value = min(5.0, habit["value"] + delta)
        hp_delta = 0.0
        mp_delta = 2.0
        update_habit(habit_id, value=new_value,
                     up_count=habit["up_count"] + 1)
    else:
        delta = 1.0 if habit["value"] > -1.0 else 0.5
        new_value = max(-5.0, habit["value"] - delta)
        xp_earned = 0.0
        gold_earned = 0.0
        hp_delta = -0.5
        mp_delta = 0.0
        update_habit(habit_id, value=new_value,
                     down_count=habit["down_count"] + 1)

    result = {"xp": xp_earned, "gold": gold_earned, "crit": crit, "direction": direction}

    if direction == "up":
        xp_result = apply_xp(username, xp_earned)
        apply_gold(username, gold_earned)
        mp_delta = min(2.0, char["mp_max"] - char["mp"])
        update_character(username, mp=min(char["mp"] + 2.0, char["mp_max"]))
        result["leveled_up"] = xp_result["leveled_up"]
        result["new_level"] = xp_result["new_level"]
    else:
        new_hp = max(1.0, char["hp"] - 0.5)
        update_character(username, hp=new_hp)
        result["leveled_up"] = False

    if char.get("rogue_crit_pending") and direction == "up":
        update_character(username, rogue_crit_pending=0)
    if char.get("mage_surge_active") and direction == "up":
        update_character(username, mage_surge_active=0)

    log_activity(username, "habit_up" if direction == "up" else "habit_down",
                 task_id=habit_id, xp_delta=xp_earned, gold_delta=gold_earned,
                 hp_delta=hp_delta if direction == "down" else 0.0,
                 mp_delta=mp_delta if direction == "up" else 0.0,
                 detail={"title": habit["title"], "crit": crit})
    return result


# ─── DAILIES ─────────────────────────────────────────────────────────────────

def get_dailies(username: str, active_only: bool = True) -> list:
    conn = get_connection()
    q = "SELECT * FROM dailies WHERE username=?"
    params = [username]
    if active_only:
        q += " AND is_active=1"
    q += " ORDER BY created_at"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def create_daily(username: str, title: str, notes: str, difficulty: str,
                 frequency: str, days_of_week: list) -> int:
    days_str = ",".join(str(d) for d in days_of_week)
    conn = get_connection()
    with conn:
        cur = conn.execute("""
            INSERT INTO dailies (username, title, notes, difficulty, frequency, days_of_week)
            VALUES (?,?,?,?,?,?)
        """, (username, title, notes, difficulty, frequency, days_str))
    conn.close()
    return cur.lastrowid


def update_daily(daily_id: int, **kwargs) -> None:
    if not kwargs:
        return
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [daily_id]
    conn = get_connection()
    with conn:
        conn.execute(f"UPDATE dailies SET {fields} WHERE id=?", values)
    conn.close()


def delete_daily(daily_id: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute("UPDATE dailies SET is_active=0 WHERE id=?", (daily_id,))
    conn.close()


def complete_daily(username: str, daily_id: int) -> dict:
    """Mark a daily complete. Returns reward dict."""
    from game.mechanics import calc_xp_reward, calc_gold_reward, apply_xp, apply_gold
    from datetime import date
    conn = get_connection()
    daily = _row_to_dict(conn.execute(
        "SELECT * FROM dailies WHERE id=? AND username=?", (daily_id, username)
    ).fetchone())
    conn.close()

    if daily.get("completed_today"):
        return {"xp": 0, "gold": 0, "crit": False, "already_done": True}

    char = get_full_character(username)
    today = str(date.today())

    xp_earned, crit = calc_xp_reward(
        daily["difficulty"], char, streak=daily["streak"], task_type="daily"
    )
    gold_earned = calc_gold_reward(daily["difficulty"], char, task_type="daily")
    if crit:
        gold_earned *= 1.5

    new_streak = daily["streak"] + 1
    best_streak = max(daily["best_streak"], new_streak)
    update_daily(daily_id,
                 completed_today=1,
                 last_completed=today,
                 streak=new_streak,
                 best_streak=best_streak)

    xp_result = apply_xp(username, xp_earned)
    apply_gold(username, gold_earned)

    mp_gain = min(5.0, char["mp_max"] - char["mp"])
    new_mp = min(char["mp"] + 5.0, char["mp_max"])
    update_character(username, mp=new_mp)

    hp_delta = 0.0
    if char.get("class") == "Healer":
        hp_gain = min(3.0, char["hp_max"] - char["hp"])
        new_hp = min(char["hp"] + 3.0, char["hp_max"])
        update_character(username, hp=new_hp)
        hp_delta = hp_gain

    if char.get("rogue_crit_pending"):
        update_character(username, rogue_crit_pending=0)
    if char.get("mage_surge_active"):
        update_character(username, mage_surge_active=0)

    log_activity(username, "daily_complete", task_id=daily_id,
                 xp_delta=xp_earned, gold_delta=gold_earned,
                 hp_delta=hp_delta, mp_delta=mp_gain,
                 detail={"title": daily["title"], "streak": new_streak, "crit": crit})

    return {
        "xp": xp_earned, "gold": gold_earned, "crit": crit,
        "streak": new_streak, "hp_regen": hp_delta,
        "leveled_up": xp_result["leveled_up"], "new_level": xp_result["new_level"]
    }


# ─── TODOS ───────────────────────────────────────────────────────────────────

def get_todos(username: str, include_completed: bool = False) -> list:
    conn = get_connection()
    q = "SELECT * FROM todos WHERE username=?"
    params = [username]
    if not include_completed:
        q += " AND completed=0"
    q += " ORDER BY priority_flag DESC, due_date ASC, created_at ASC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def create_todo(username: str, title: str, notes: str, difficulty: str,
                due_date: str = None, priority_flag: int = 0, tag: str = '') -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute("""
            INSERT INTO todos (username, title, notes, difficulty, due_date, priority_flag, tag)
            VALUES (?,?,?,?,?,?,?)
        """, (username, title, notes, difficulty, due_date, priority_flag, tag or ''))
    conn.close()
    return cur.lastrowid


def update_todo(todo_id: int, **kwargs) -> None:
    if not kwargs:
        return
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [todo_id]
    conn = get_connection()
    with conn:
        conn.execute(f"UPDATE todos SET {fields} WHERE id=?", values)
    conn.close()


def delete_todo(todo_id: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM todos WHERE id=?", (todo_id,))
    conn.close()


def complete_todo(username: str, todo_id: int) -> dict:
    """Mark a todo complete. Returns reward dict."""
    from game.mechanics import calc_xp_reward, calc_gold_reward, apply_xp, apply_gold
    conn = get_connection()
    todo = _row_to_dict(conn.execute(
        "SELECT * FROM todos WHERE id=? AND username=?", (todo_id, username)
    ).fetchone())
    conn.close()

    char = get_full_character(username)
    now = datetime.now().isoformat()

    xp_earned, crit = calc_xp_reward(todo["difficulty"], char, task_type="todo")
    gold_earned = calc_gold_reward(todo["difficulty"], char, task_type="todo")
    if crit:
        gold_earned *= 1.5

    update_todo(todo_id, completed=1, completed_at=now)
    xp_result = apply_xp(username, xp_earned)
    apply_gold(username, gold_earned)

    mp_gain = min(1.0, char["mp_max"] - char["mp"])
    update_character(username, mp=min(char["mp"] + 1.0, char["mp_max"]))

    if char.get("rogue_crit_pending"):
        update_character(username, rogue_crit_pending=0)
    if char.get("mage_surge_active"):
        update_character(username, mage_surge_active=0)

    log_activity(username, "todo_complete", task_id=todo_id,
                 xp_delta=xp_earned, gold_delta=gold_earned,
                 mp_delta=mp_gain,
                 detail={"title": todo["title"], "crit": crit})

    return {
        "xp": xp_earned, "gold": gold_earned, "crit": crit,
        "leveled_up": xp_result["leveled_up"], "new_level": xp_result["new_level"]
    }


# ─── CUSTOM REWARDS ──────────────────────────────────────────────────────────

def get_custom_rewards(username: str) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM custom_rewards WHERE username=? AND is_active=1 ORDER BY gold_cost",
        (username,)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def create_custom_reward(username: str, title: str, notes: str, gold_cost: float) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute("""
            INSERT INTO custom_rewards (username, title, notes, gold_cost)
            VALUES (?,?,?,?)
        """, (username, title, notes, gold_cost))
    conn.close()
    return cur.lastrowid


def update_custom_reward(reward_id: int, **kwargs) -> None:
    if not kwargs:
        return
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [reward_id]
    conn = get_connection()
    with conn:
        conn.execute(f"UPDATE custom_rewards SET {fields} WHERE id=?", values)
    conn.close()


def delete_custom_reward(reward_id: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute("UPDATE custom_rewards SET is_active=0 WHERE id=?", (reward_id,))
    conn.close()


def buy_custom_reward(username: str, reward_id: int) -> dict:
    """Deduct gold and log. Returns {'success': bool, 'message': str}."""
    conn = get_connection()
    reward = _row_to_dict(conn.execute(
        "SELECT * FROM custom_rewards WHERE id=? AND username=?", (reward_id, username)
    ).fetchone())
    char = _row_to_dict(conn.execute(
        "SELECT gold FROM characters WHERE username=?", (username,)
    ).fetchone())
    conn.close()

    if char["gold"] < reward["gold_cost"]:
        return {"success": False, "message": f"Need {reward['gold_cost']:.1f} gold (have {char['gold']:.1f})"}

    from game.mechanics import apply_gold
    apply_gold(username, -reward["gold_cost"])
    log_activity(username, "reward_buy", task_id=reward_id,
                 gold_delta=-reward["gold_cost"],
                 detail={"title": reward["title"]})
    return {"success": True, "message": f"Redeemed: {reward['title']}"}


# ─── SHOP / EQUIPMENT ────────────────────────────────────────────────────────

def get_inventory(username: str) -> set:
    """Returns set of owned item_keys."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT item_key FROM inventory WHERE username=?", (username,)
    ).fetchall()
    conn.close()
    return {r["item_key"] for r in rows}


def buy_equipment(username: str, item_key: str) -> dict:
    from game.items import ITEM_CATALOG
    item = ITEM_CATALOG.get(item_key)
    if not item:
        return {"success": False, "message": "Item not found"}

    owned = get_inventory(username)
    if item_key in owned:
        return {"success": False, "message": "Already owned"}

    conn = get_connection()
    char = _row_to_dict(conn.execute(
        "SELECT gold FROM characters WHERE username=?", (username,)
    ).fetchone())
    conn.close()

    if char["gold"] < item["gold_cost"]:
        return {"success": False, "message": f"Need {item['gold_cost']} gold"}

    from game.mechanics import apply_gold
    apply_gold(username, -item["gold_cost"])

    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT OR IGNORE INTO inventory (username, item_key) VALUES (?,?)",
            (username, item_key)
        )
    conn.close()

    log_activity(username, "item_buy", gold_delta=-item["gold_cost"],
                 detail={"item_key": item_key, "name": item["name"]})
    return {"success": True, "message": f"Bought {item['name']}!"}


def equip_item(username: str, item_key: str) -> dict:
    from game.items import ITEM_CATALOG
    from game.mechanics import recalculate_stats
    item = ITEM_CATALOG.get(item_key)
    if not item:
        return {"success": False, "message": "Item not found"}

    owned = get_inventory(username)
    if item_key not in owned:
        return {"success": False, "message": "You don't own this item"}

    slot = item["slot"] + "_slot"
    conn = get_connection()
    with conn:
        conn.execute(f"UPDATE equipment SET {slot}=? WHERE username=?", (item_key, username))
    conn.close()

    recalculate_stats(username)
    return {"success": True, "message": f"Equipped {item['name']}!"}


def unequip_slot(username: str, slot: str) -> None:
    from game.mechanics import recalculate_stats
    conn = get_connection()
    with conn:
        conn.execute(f"UPDATE equipment SET {slot}_slot=NULL WHERE username=?", (username,))
    conn.close()
    recalculate_stats(username)


# ─── ACTIVITY LOG ────────────────────────────────────────────────────────────

def log_activity(username: str, event_type: str, task_id: int = None,
                 xp_delta: float = 0.0, gold_delta: float = 0.0,
                 hp_delta: float = 0.0, mp_delta: float = 0.0,
                 detail: dict = None) -> None:
    detail_str = json.dumps(detail) if detail else None
    conn = get_connection()
    with conn:
        conn.execute("""
            INSERT INTO activity_log
                (username, event_type, task_id, xp_delta, gold_delta, hp_delta, mp_delta, detail)
            VALUES (?,?,?,?,?,?,?,?)
        """, (username, event_type, task_id, xp_delta, gold_delta, hp_delta, mp_delta, detail_str))
    conn.close()


def get_daily_gold_avg(username: str, days: int = 7) -> float:
    """Average gold earned per day over the last N days. Falls back to 50.0 if no history."""
    from datetime import date, timedelta
    cutoff = str(date.today() - timedelta(days=days))
    conn = get_connection()
    rows = conn.execute("""
        SELECT date(created_at) AS day, SUM(gold_delta) AS daily_gold
        FROM activity_log
        WHERE username=? AND gold_delta > 0 AND date(created_at) >= ?
        GROUP BY date(created_at)
    """, (username, cutoff)).fetchall()
    conn.close()
    if not rows:
        return 50.0
    total = sum(r["daily_gold"] for r in rows)
    return total / days


def get_activity_log(username: str, limit: int = 50) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM activity_log WHERE username=?
        ORDER BY created_at DESC LIMIT ?
    """, (username, limit)).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]
