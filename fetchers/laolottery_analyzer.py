"""Lao Lottery 2-digit result analyzer."""

from collections import Counter
from datetime import datetime


def _iso_week(date_str: str) -> tuple[int, int]:
    try:
        d = datetime.strptime(date_str[:10], "%Y-%m-%d")
        y, w, _ = d.isocalendar()
        return (y, w)
    except Exception:
        return (0, 0)


def analyze(results: list[dict]) -> dict:
    if not results:
        return {"total_draws": 0, "hot": [], "cold": [], "due": [], "weekly_avg": [], "suggestions": []}

    total = len(results)
    digits = [r["two_digit"] for r in results]
    all_numbers = [f"{i:02d}" for i in range(100)]

    freq = Counter(digits)

    # --- HOT ---
    hot_sorted = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    hot = [{"number": n, "count": c} for n, c in hot_sorted[:5]]

    # --- COLD ---
    full_freq = {n: freq.get(n, 0) for n in all_numbers}
    cold_sorted = sorted(full_freq.items(), key=lambda x: (x[1], x[0]))
    cold = [{"number": n, "count": c} for n, c in cold_sorted[:5]]

    # --- DUE ---
    positions: dict[str, list[int]] = {}
    for idx, num in enumerate(digits):
        positions.setdefault(num, []).append(idx)

    due_candidates = []
    for num, pos_list in positions.items():
        if len(pos_list) < 2:
            continue
        gaps = [pos_list[i + 1] - pos_list[i] for i in range(len(pos_list) - 1)]
        avg_gap = sum(gaps) / len(gaps)
        last_seen = pos_list[0]
        if last_seen > avg_gap:
            due_candidates.append({
                "number": num,
                "avg_gap": round(avg_gap, 4),
                "last_seen": last_seen,
                "_score": last_seen - avg_gap,
            })

    due_candidates.sort(key=lambda x: (-x["_score"], x["number"]))
    due = [
        {"number": d["number"], "avg_gap": d["avg_gap"], "last_seen": d["last_seen"]}
        for d in due_candidates[:5]
    ]

    # --- WEEKLY AVERAGE ---
    weeks = {_iso_week(r.get("date", "")) for r in results}
    weeks.discard((0, 0))
    num_weeks = max(len(weeks), 1)
    weekly_sorted = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    weekly_avg = [
        {"number": n, "count": c, "avg_per_week": round(c / num_weeks, 1)}
        for n, c in weekly_sorted[:5]
    ]

    # --- SUGGESTIONS: top-3 hot + top-5 due, deduped, up to 5 ---
    seen: set[str] = set()
    suggestions: list[str] = []
    for entry in hot[:3]:
        n = entry["number"]
        if n not in seen:
            seen.add(n)
            suggestions.append(n)
    for entry in due[:5]:
        n = entry["number"]
        if n not in seen and len(suggestions) < 5:
            seen.add(n)
            suggestions.append(n)

    return {
        "total_draws": total,
        "hot": hot,
        "cold": cold,
        "due": due,
        "weekly_avg": weekly_avg,
        "suggestions": suggestions,
    }
