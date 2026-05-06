"""Lao Lottery 2-digit result analyzer."""

from collections import Counter


def analyze(results: list[dict]) -> dict:
    """Analyze Lao lottery results and return hot/cold/due/suggestions stats.

    Args:
        results: list of dicts with at least a 'two_digit' key, newest first.

    Returns:
        dict with keys: total_draws, hot, cold, due, suggestions
    """
    if not results:
        return {"total_draws": 0, "hot": [], "cold": [], "due": [], "suggestions": []}

    total = len(results)
    digits = [r["two_digit"] for r in results]
    all_numbers = [f"{i:02d}" for i in range(100)]

    # Frequency counts
    freq = Counter(digits)

    # --- HOT: top 5 by frequency, ties broken ascending ---
    hot_sorted = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    hot = [{"number": n, "count": c} for n, c in hot_sorted[:5]]

    # --- COLD: 5 least frequent (prefer count=0 first), ties broken ascending ---
    full_freq = {n: freq.get(n, 0) for n in all_numbers}
    cold_sorted = sorted(full_freq.items(), key=lambda x: (x[1], x[0]))
    cold = [{"number": n, "count": c} for n, c in cold_sorted[:5]]

    # --- DUE: numbers where last_seen > avg_gap ---
    # Build position lists (index 0 = most recent draw)
    positions: dict[str, list[int]] = {}
    for idx, num in enumerate(digits):
        positions.setdefault(num, []).append(idx)

    due_candidates = []
    for num, pos_list in positions.items():
        if len(pos_list) < 2:
            # Only one appearance — no gaps to compute avg from, skip
            continue
        # Gaps between consecutive appearances (positions are already sorted asc
        # because we iterate digits newest-first, so pos_list is ascending)
        gaps = [pos_list[i + 1] - pos_list[i] for i in range(len(pos_list) - 1)]
        avg_gap = sum(gaps) / len(gaps)
        last_seen = pos_list[0]  # smallest index = most recent
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

    # --- SUGGESTIONS: top-3 hot + top-3 due, deduped, hot first ---
    seen: set[str] = set()
    suggestions: list[str] = []
    for entry in hot[:3]:
        n = entry["number"]
        if n not in seen:
            seen.add(n)
            suggestions.append(n)
    for entry in due[:3]:
        n = entry["number"]
        if n not in seen:
            seen.add(n)
            suggestions.append(n)

    return {
        "total_draws": total,
        "hot": hot,
        "cold": cold,
        "due": due,
        "suggestions": suggestions,
    }
