from datetime import date, timedelta


def maybe_run_cron(username: str) -> list:
    """Check if cron is due and run it. Returns list of result dicts for UI display."""
    from db.queries import get_character, update_character
    char = get_character(username)
    if not char:
        return []

    last_cron = date.fromisoformat(char["last_cron"])
    today = date.today()
    if last_cron >= today:
        return []

    results = []
    current = last_cron + timedelta(days=1)
    while current <= today:
        result = _run_cron_for_date(username, current)
        results.append(result)
        current += timedelta(days=1)

    return results


def _run_cron_for_date(username: str, target_date: date) -> dict:
    from db.queries import (get_character, get_dailies, update_character,
                             update_daily, log_activity, get_full_character)
    from db.models import get_connection
    from game.mechanics import daily_miss_damage, calc_mp_max

    char = get_full_character(username)
    dow = target_date.weekday()  # 0=Mon, 6=Sun

    dailies = get_dailies(username)
    due = [
        d for d in dailies
        if d["start_date"] <= str(target_date)
        and str(dow) in d["days_of_week"].split(",")
    ]

    missed = [d for d in due if not d["completed_today"]]

    total_hp_lost = 0.0
    for task in missed:
        dmg = daily_miss_damage(char, task)
        # Defensive Stance check
        if char.get("warrior_stance_date") == str(target_date):
            dmg *= 0.5
        total_hp_lost += dmg
        log_activity(username, "daily_miss", task_id=task["id"],
                     hp_delta=-dmg,
                     detail={"title": task["title"], "date": str(target_date)})
        # Break streaks on miss
        update_daily(task["id"], streak=0)

    # Apply damage (floor HP at 1.0)
    if total_hp_lost > 0:
        new_hp = max(1.0, char["hp"] - total_hp_lost)
        update_character(username, hp=new_hp)

    # Decay habit values
    _decay_habits(username)

    # Reset dailies for this date
    _reset_daily_completions(username, target_date)

    # Mage passive: +3 MP per cron
    if char.get("class") == "Mage":
        new_mp = min(char["mp"] + 3.0, char["mp_max"])
        update_character(username, mp=new_mp)

    # Advance last_cron
    update_character(username, last_cron=str(target_date))

    # Log cron run
    conn = get_connection()
    with conn:
        conn.execute("""
            INSERT INTO cron_log (username, run_date, dailies_due, dailies_missed, hp_lost)
            VALUES (?,?,?,?,?)
        """, (username, str(target_date), len(due), len(missed), round(total_hp_lost, 2)))
    conn.close()

    return {
        "date": str(target_date),
        "dailies_due": len(due),
        "dailies_missed": len(missed),
        "hp_lost": round(total_hp_lost, 2),
    }


def _decay_habits(username: str) -> None:
    from db.models import get_connection
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, value FROM habits WHERE username=? AND is_active=1", (username,)
    ).fetchall()
    conn.close()
    for row in rows:
        v = row["value"]
        if v > 1.0:
            new_v = round(max(1.0, v - 0.1), 2)
        elif v < -1.0:
            new_v = round(min(-1.0, v + 0.1), 2)
        else:
            continue
        conn = get_connection()
        with conn:
            conn.execute("UPDATE habits SET value=? WHERE id=?", (new_v, row["id"]))
        conn.close()


def _reset_daily_completions(username: str, for_date: date) -> None:
    """Mark all dailies as not completed for the next day."""
    from db.models import get_connection
    conn = get_connection()
    with conn:
        conn.execute(
            "UPDATE dailies SET completed_today=0 WHERE username=? AND is_active=1",
            (username,)
        )
    conn.close()
