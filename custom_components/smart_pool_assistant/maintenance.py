"""Maintenance history helpers for Smart Pool Assistant."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from homeassistant.util import dt as dt_util


VISIBLE_ACTIVITY_TYPES = ("chlor", "ph_plus", "ph_minus", "water_exchange", "filter_clean", "filter_replace")
CONTEXT_HISTORY_KEY = "pool_context_history"
MAX_CONTEXT_HISTORY_ITEMS = 240


def activity_text(
    m_type: str | None,
    amount: float | int | None,
    pool_covered: bool = True,
    usage_mode: str = "none",
    details: dict | None = None,
) -> str:
    """Return a human readable activity label."""
    if m_type == "chlor":
        return f"{amount:g}g Chlor hinzugef\u00fcgt" if amount is not None else "Chlor hinzugef\u00fcgt"
    if m_type == "ph_plus":
        return f"{amount:g}g PH-Plus hinzugef\u00fcgt" if amount is not None else "PH-Plus hinzugef\u00fcgt"
    if m_type == "ph_minus":
        return f"{amount:g}ml PH-Minus hinzugef\u00fcgt" if amount is not None else "PH-Minus hinzugef\u00fcgt"
    if m_type == "water_exchange":
        liters = details.get("liters") if isinstance(details, dict) else amount
        percent = details.get("percent") if isinstance(details, dict) else None
        if liters is not None and percent is not None:
            return f"{liters:g}l Wasser gewechselt ({percent:g}%)"
        if liters is not None:
            return f"{liters:g}l Wasser gewechselt"
        if percent is not None:
            return f"{percent:g}% Wasser gewechselt"
        return "Wasser gewechselt"
    if m_type == "filter_clean":
        return "Filter gereinigt"
    if m_type == "filter_replace":
        return "Filter getauscht"
    if m_type == "set_covered":
        return "Abdeckung: " + ("Abgedeckt" if pool_covered else "Offen")
    if m_type == "set_usage":
        mode_labels = {"none": "Keine", "normal": "Normal", "party": "Party"}
        return f"Nutzungsmodus: {mode_labels.get(usage_mode, usage_mode)}"
    return ""


def normalize_loaded_history(
    stored: dict,
    pool_covered: bool = True,
    usage_mode: str = "none",
) -> dict:
    """Fix legacy history entries after loading from storage."""
    if not isinstance(stored, dict):
        return {}

    history = dict(stored)
    activities = history.get("last_activities")
    if isinstance(activities, list):
        normalized: list[dict] = []
        changed = False

        for entry in activities:
            if not isinstance(entry, dict):
                continue

            item = dict(entry)
            m_type = item.get("type")

            if m_type in ("filter_clean", "filter_replace"):
                expected_text = activity_text(m_type, None, pool_covered, usage_mode)
                if item.get("text") != expected_text:
                    item["text"] = expected_text
                    changed = True
                if item.get("amount") == 0:
                    item["amount"] = None
                    changed = True
            elif not item.get("text"):
                item["text"] = activity_text(
                    m_type,
                    item.get("amount"),
                    pool_covered,
                    usage_mode,
                    item,
                ) or "--"
                changed = True

            normalized.append(item)

        if changed:
            history["last_activities"] = normalized

    for key in ("filter_clean", "filter_replace"):
        entry = history.get(key)
        if isinstance(entry, dict) and entry.get("amount") == 0:
            entry = dict(entry)
            entry["amount"] = None
            history[key] = entry

    context_history = history.get(CONTEXT_HISTORY_KEY)
    if isinstance(context_history, list):
        normalized_context: list[dict] = []
        changed = False
        last_key: tuple[str | None, bool | None, str | None] | None = None
        for entry in context_history:
            if not isinstance(entry, dict):
                changed = True
                continue
            raw_ts = entry.get("raw_ts")
            if not isinstance(raw_ts, str) or not raw_ts:
                changed = True
                continue
            normalized_entry = {
                "raw_ts": raw_ts,
                "pool_covered": _bool_optional(entry.get("pool_covered")),
                "usage_mode": _clean_usage_mode(entry.get("usage_mode")),
            }
            entry_key = (
                normalized_entry["raw_ts"],
                normalized_entry["pool_covered"],
                normalized_entry["usage_mode"],
            )
            if entry_key == last_key:
                changed = True
                continue
            normalized_context.append(normalized_entry)
            last_key = entry_key
            if normalized_entry != entry:
                changed = True
        if changed:
            history[CONTEXT_HISTORY_KEY] = normalized_context[-MAX_CONTEXT_HISTORY_ITEMS:]

    measurement_history = history.get("last_measurements_display")
    if isinstance(measurement_history, list):
        normalized_measurements: list[dict] = []
        changed = False
        allowed_parameters = {"Chlor", "pH", "Cyanursaeure"}
        parameter_aliases = {
            "PL Chlorine Free": "Chlor",
            "PL pH": "pH",
            "PL Temperature": "Temperatur",
            "PL Cyanuric Acid": "Cyanursaeure",
            "PL Cyanuric acid": "Cyanursaeure",
            "PL CYA": "Cyanursaeure",
            "chlor": "Chlor",
            "ph": "pH",
            "temperature": "Temperatur",
            "cyanuric_acid": "Cyanursaeure",
        }
        seen_measurements: set[tuple[str | None, str | None, str | None, str]] = set()

        for entry in measurement_history:
            if not isinstance(entry, dict):
                changed = True
                continue

            raw_parameter = entry.get("parameter")
            normalized_parameter = parameter_aliases.get(raw_parameter, raw_parameter)
            if normalized_parameter not in allowed_parameters:
                changed = True
                continue

            timestamp = entry.get("timestamp")
            source = entry.get("source")
            value = entry.get("value")
            dedupe_key = (timestamp, normalized_parameter, source, str(value))
            if dedupe_key in seen_measurements:
                changed = True
                continue

            seen_measurements.add(dedupe_key)
            normalized_entry = {
                "timestamp": timestamp,
                "parameter": normalized_parameter,
                "source": source,
                "value": value,
            }
            if normalized_entry != entry:
                changed = True
            normalized_measurements.append(normalized_entry)

        if changed:
            history["last_measurements_display"] = normalized_measurements

    history.pop("bluetooth_connected", None)

    return history


def format_activity(
    entry: dict,
    pool_covered: bool = True,
    usage_mode: str = "none",
) -> str:
    """Format a stored activity entry."""
    return activity_text(entry.get("type"), entry.get("amount"), pool_covered, usage_mode, entry) or "--"


def collect_last_activities(
    history: dict,
    parse_ts: Callable[[str | None], datetime | None],
    pool_covered: bool = True,
    usage_mode: str = "none",
) -> list[dict]:
    """Build a compact activity list from stored maintenance actions."""
    items = history.get("last_activities")
    if isinstance(items, list) and items:
        normalized = []
        for entry in items:
            if not isinstance(entry, dict):
                continue
            if entry.get("type") not in VISIBLE_ACTIVITY_TYPES:
                continue
            raw_ts = entry.get("raw_ts")
            dt = parse_ts(raw_ts)
            if not dt:
                continue
            normalized.append({
                "type": entry.get("type"),
                "text": entry.get("text")
                or activity_text(entry.get("type"), entry.get("amount"), pool_covered, usage_mode, entry)
                or "--",
                "time": entry.get("time"),
                "raw_ts": raw_ts,
                "percent": entry.get("percent"),
                "liters": entry.get("liters"),
                "_dt": dt,
            })
        normalized.sort(key=lambda item: item["_dt"], reverse=True)
        for item in normalized:
            item.pop("_dt", None)
        return normalized[:5]

    legacy_items = []

    for key in VISIBLE_ACTIVITY_TYPES:
        entry = history.get(key)
        if not isinstance(entry, dict):
            continue

        raw_ts = entry.get("raw_ts")
        dt = parse_ts(raw_ts)
        if not dt:
            continue

        legacy_items.append({
            "type": key,
            "text": format_activity({"type": key, **entry}, pool_covered, usage_mode),
            "time": entry.get("time"),
            "raw_ts": raw_ts,
            "_dt": dt,
        })

    legacy_items.sort(key=lambda item: item["_dt"], reverse=True)
    for item in legacy_items:
        item.pop("_dt", None)
    return legacy_items[:5]


def update_maintenance_history(
    history: dict,
    m_type: str,
    amount: float,
    now: datetime,
    pool_covered: bool,
    usage_mode: str,
    details: dict | None = None,
) -> tuple[bool, str, str | None]:
    """Update maintenance history and return pool state plus notification text."""
    ts_formatted = now.strftime("%d.%m. %H:%M")
    msg = None
    known_state_types = {"set_covered", "set_usage"}

    if m_type not in VISIBLE_ACTIVITY_TYPES and m_type not in known_state_types:
        return pool_covered, usage_mode, None

    if m_type == "set_covered":
        pool_covered = amount > 0
        history["pool_covered"] = pool_covered
    elif m_type == "set_usage":
        modes = ["none", "normal", "party"]
        usage_mode = modes[int(amount)] if int(amount) < len(modes) else "none"
        history["usage_mode"] = usage_mode

    action_text = activity_text(m_type, amount, pool_covered, usage_mode, details) if m_type else ""
    if not action_text:
        label, unit = _maintenance_label_and_unit(m_type)
        action_text = f"{amount:g}{unit} {label}" if amount else label

    stored_amount = None if m_type in ("filter_clean", "filter_replace") else amount
    history_entry = {"amount": stored_amount, "time": ts_formatted, "raw_ts": now.isoformat()}
    if isinstance(details, dict):
        if details.get("liters") is not None:
            history_entry["liters"] = details["liters"]
        if details.get("percent") is not None:
            history_entry["percent"] = details["percent"]
    history[m_type] = history_entry

    # A filter replacement implicitly resets the cleaning interval as well.
    if m_type == "filter_replace":
        history["filter_clean"] = dict(history_entry)

    if m_type in ("set_covered", "set_usage"):
        _append_context_history(history, now, pool_covered, usage_mode)
        return pool_covered, usage_mode, None

    if m_type in VISIBLE_ACTIVITY_TYPES:
        history["last_action"] = f"{action_text} am {ts_formatted}"
        activities = history.get("last_activities", [])
        activities = activities if isinstance(activities, list) else []
        activities.insert(0, {
            "type": m_type,
            "text": action_text,
            "amount": stored_amount,
            "time": ts_formatted,
            "raw_ts": now.isoformat(),
            "liters": history_entry.get("liters"),
            "percent": history_entry.get("percent"),
        })
        history["last_activities"] = activities[:5]

        if m_type == "filter_clean":
            msg = "Pool-Wartung: Filter gereinigt."
        elif m_type == "filter_replace":
            msg = "Pool-Wartung: Filter getauscht."
        else:
            msg = f"Pool-Pflege: {action_text}."

    return pool_covered, usage_mode, msg


def get_time_since_last_action(
    history: dict,
    action_key: str,
    in_hours: bool = False,
) -> int | None:
    """Calculate time since last action in hours or days."""
    last_action_data = history.get(action_key)
    if last_action_data and last_action_data.get("raw_ts"):
        last_ts = dt_util.parse_datetime(last_action_data["raw_ts"])
        if last_ts:
            diff = dt_util.now() - last_ts
            if in_hours:
                return int(diff.total_seconds() // 3600)
            return diff.days
    return None


def get_action_dt(
    history: dict,
    action_key: str,
    parse_ts: Callable[[str | None], datetime | None],
) -> datetime | None:
    """Return the aware timestamp of a stored maintenance action."""
    action_data = history.get(action_key)
    if isinstance(action_data, dict):
        return parse_ts(action_data.get("raw_ts"))
    return None


def get_filter_status(
    time_since: int | None,
    interval: int,
    yellow_threshold: int,
    red_threshold: int,
) -> str:
    """Determine filter status based on time since last action and thresholds."""
    if time_since is None:
        return "unknown"

    time_until_due = interval - time_since
    if time_until_due <= red_threshold:
        return "critical"
    if time_until_due <= yellow_threshold:
        return "warning"

    return "ok"


def _maintenance_label_and_unit(m_type: str | None) -> tuple[str, str]:
    if m_type == "chlor":
        return "Chlor", "g"
    if m_type == "ph_plus":
        return "PH-Plus", "g"
    if m_type == "ph_minus":
        return "PH-Minus", "ml"
    if m_type == "water_exchange":
        return "Wasser gewechselt", "l"
    if m_type == "filter_clean":
        return "Filter gereinigt", ""
    if m_type == "filter_replace":
        return "Filter getauscht", ""
    return "", ""


def _append_context_history(
    history: dict,
    now: datetime,
    pool_covered: bool,
    usage_mode: str,
) -> None:
    """Persist a compact timeline of context state changes for learning."""
    events = history.get(CONTEXT_HISTORY_KEY)
    events = list(events) if isinstance(events, list) else []
    event = {
        "raw_ts": now.isoformat(),
        "pool_covered": pool_covered,
        "usage_mode": usage_mode,
    }
    if events:
        previous = events[-1]
        if (
            isinstance(previous, dict)
            and previous.get("pool_covered") == pool_covered
            and previous.get("usage_mode") == usage_mode
        ):
            return
    events.append(event)
    history[CONTEXT_HISTORY_KEY] = events[-MAX_CONTEXT_HISTORY_ITEMS:]


def _bool_optional(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _clean_usage_mode(value: object) -> str | None:
    if isinstance(value, str) and value in {"none", "normal", "party"}:
        return value
    return None
