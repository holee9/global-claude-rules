#!/usr/bin/env python3
"""
Rule Analytics Module

Tracks rule usage and provides analytics for the Global Claude Rules system.
Used to:
- Track which rules are viewed most frequently
- Track when rules are triggered
- Provide insights for rule improvement

Cache location: ~/.claude/cache/rule_analytics.json
"""

from __future__ import annotations

import json
import logging
import os
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# =============================================================================
# Constants
# =============================================================================
CACHE_DIR = Path.home() / ".claude" / "cache"
ANALYTICS_FILE = CACHE_DIR / "rule_analytics.json"

# Analytics retention period (days)
RETENTION_DAYS = 90

# Minimum views to be considered "frequently triggered"
FREQUENT_THRESHOLD = 3


def get_analytics_data() -> dict[str, Any]:
    """Load analytics data from cache.

    Returns:
        Analytics dictionary with view counts and timestamps
    """
    if not ANALYTICS_FILE.exists():
        return {
            "rule_views": {},
            "rule_triggers": {},
            "last_updated": None,
        }

    try:
        data = json.loads(ANALYTICS_FILE.read_text(encoding="utf-8"))

        # Clean old entries
        cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
        cleaned_data = {
            "rule_views": {},
            "rule_triggers": {},
            "last_updated": data.get("last_updated"),
        }

        for rule_id, count in data.get("rule_views", {}).items():
            # Keep all view counts (they're aggregates)
            cleaned_data["rule_views"][rule_id] = count

        for rule_id, timestamps in data.get("rule_triggers", {}).items():
            # Filter old timestamps
            recent = [
                ts for ts in timestamps
                if datetime.fromisoformat(ts) > cutoff_date
            ]
            if recent:
                cleaned_data["rule_triggers"][rule_id] = recent

        return cleaned_data

    except (json.JSONDecodeError, OSError, ValueError):
        return {
            "rule_views": {},
            "rule_triggers": {},
            "last_updated": None,
        }


def save_analytics_data(data: dict[str, Any]) -> None:
    """Save analytics data to cache.

    Args:
        data: Analytics dictionary to save
    """
    try:
        ANALYTICS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data["last_updated"] = datetime.now().isoformat()

        ANALYTICS_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except (OSError, PermissionError) as e:
        logging.warning(f"Failed to save analytics data: {e}")


def track_rule_view(err_id: str, context: str | None = None) -> None:
    """Record when a rule is viewed/shown to the user.

    Args:
        err_id: The ERR rule ID (e.g., "ERR-001")
        context: Optional context (tool name, action, etc.)
    """
    data = get_analytics_data()

    # Increment view count
    err_id_upper = err_id.upper()
    data["rule_views"][err_id_upper] = data["rule_views"].get(err_id_upper, 0) + 1

    # Record trigger timestamp
    if "rule_triggers" not in data:
        data["rule_triggers"] = {}

    if err_id_upper not in data["rule_triggers"]:
        data["rule_triggers"][err_id_upper] = []

    data["rule_triggers"][err_id_upper].append(datetime.now().isoformat())

    # Limit trigger history size (keep last 100)
    if len(data["rule_triggers"][err_id_upper]) > 100:
        data["rule_triggers"][err_id_upper] = data["rule_triggers"][err_id_upper][-100:]

    save_analytics_data(data)


def track_rules_view(err_ids: list[str], context: str | None = None) -> None:
    """Record multiple rules being viewed.

    Args:
        err_ids: List of ERR rule IDs
        context: Optional context
    """
    for err_id in err_ids:
        track_rule_view(err_id, context)


def get_rule_view_count(err_id: str) -> int:
    """Get the number of times a rule has been viewed.

    Args:
        err_id: The ERR rule ID

    Returns:
        Number of views
    """
    data = get_analytics_data()
    return data["rule_views"].get(err_id.upper(), 0)


def get_frequently_triggered_rules(limit: int = 10) -> list[tuple[str, int]]:
    """Get the most frequently triggered rules.

    Args:
        limit: Maximum number of rules to return

    Returns:
        List of (err_id, view_count) tuples sorted by count
    """
    data = get_analytics_data()

    # Filter by threshold and sort
    rules = [
        (err_id, count)
        for err_id, count in data["rule_views"].items()
        if count >= FREQUENT_THRESHOLD
    ]

    rules.sort(key=lambda x: x[1], reverse=True)
    return rules[:limit]


def get_recently_triggered_rules(hours: int = 24, limit: int = 10) -> list[tuple[str, int]]:
    """Get rules triggered recently.

    Args:
        hours: Time window in hours
        limit: Maximum number of rules to return

    Returns:
        List of (err_id, trigger_count) tuples sorted by count
    """
    data = get_analytics_data()
    cutoff = datetime.now() - timedelta(hours=hours)

    recent_counts = Counter()

    for err_id, timestamps in data.get("rule_triggers", {}).items():
        recent = [
            ts for ts in timestamps
            if datetime.fromisoformat(ts) > cutoff
        ]
        if recent:
            recent_counts[err_id] = len(recent)

    # Sort by count
    return recent_counts.most_common(limit)


def get_rule_trigger_history(err_id: str, limit: int = 20) -> list[str]:
    """Get trigger history for a specific rule.

    Args:
        err_id: The ERR rule ID
        limit: Maximum number of timestamps to return

    Returns:
        List of ISO format timestamps
    """
    data = get_analytics_data()
    timestamps = data.get("rule_triggers", {}).get(err_id.upper(), [])

    # Return most recent first
    return timestamps[-limit:][::-1]


def get_analytics_summary() -> dict[str, Any]:
    """Get a summary of analytics data.

    Returns:
        Dictionary with analytics summary
    """
    data = get_analytics_data()

    total_views = sum(data["rule_views"].values())
    total_rules = len(data["rule_views"])

    frequent_rules = get_frequently_triggered_rules(5)
    recent_rules = get_recently_triggered_rules(5)

    return {
        "total_views": total_views,
        "total_rules_tracked": total_rules,
        "most_frequent": frequent_rules,
        "most_recent": recent_rules,
        "last_updated": data.get("last_updated"),
    }


def reset_analytics() -> None:
    """Reset all analytics data."""
    save_analytics_data({
        "rule_views": {},
        "rule_triggers": {},
        "last_updated": datetime.now().isoformat(),
    })


def export_analytics(output_path: Path | None = None) -> str:
    """Export analytics data to JSON.

    Args:
        output_path: Path to save export (uses default if None)

    Returns:
        Path to exported file
    """
    if output_path is None:
        output_path = CACHE_DIR / "rule_analytics_export.json"

    data = get_analytics_data()

    # Add summary
    data["summary"] = get_analytics_summary()

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return str(output_path)


def main() -> None:
    """CLI entry point for testing analytics."""
    import argparse

    parser = argparse.ArgumentParser(description="Rule Analytics CLI")
    parser.add_argument("--show", action="store_true", help="Show analytics summary")
    parser.add_argument("--top", type=int, default=10, help="Show top N rules")
    parser.add_argument("--recent", type=int, default=24, help="Show recent rules (hours)")
    parser.add_argument("--reset", action="store_true", help="Reset analytics")
    parser.add_argument("--export", action="store_true", help="Export analytics")

    args = parser.parse_args()

    if args.reset:
        reset_analytics()
        print("Analytics reset.")
        return

    if args.show:
        summary = get_analytics_summary()
        print("Rule Analytics Summary:")
        print(f"  Total Views: {summary['total_views']}")
        print(f"  Rules Tracked: {summary['total_rules_tracked']}")

        print("\n  Most Frequent Rules:")
        for err_id, count in summary['most_frequent']:
            print(f"    {err_id}: {count} views")

        print(f"\n  Recent (last {args.recent}h):")
        for err_id, count in summary['most_recent']:
            print(f"    {err_id}: {count} times")

    if args.export:
        path = export_analytics()
        print(f"Exported to: {path}")


if __name__ == "__main__":
    main()
