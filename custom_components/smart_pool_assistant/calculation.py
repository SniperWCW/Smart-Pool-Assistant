"""Chemistry calculation helpers for Smart Pool Assistant."""
from __future__ import annotations

from datetime import datetime

from .const import (
    CONF_CHLOR_CONTENT,
    CONF_CHLOR_MAX,
    CONF_CHLOR_MIN,
    CONF_CHLOR_TARGET,
    CONF_PH_DOWN_DOSAGE,
    CONF_PH_MAX,
    CONF_PH_MIN,
    CONF_PH_TARGET,
    CONF_PH_UP_DOSAGE,
    CONF_POOL_VOLUME,
)

MEASURING_SPOON_SIZES = (1.0, 2.5, 5.0, 7.5, 15.0)


def round_to_measuring_spoons(amount: float | int | None) -> float:
    """Round down to a conservative, practical amount buildable from the spoons."""
    if amount is None:
        return 0.0

    amount = float(amount)
    if amount < min(MEASURING_SPOON_SIZES):
        return 0.0

    # Keep combinations practical: any number of 15 g/ml spoons plus up to two
    # smaller spoons. This keeps 8 g conservative at 7.5 g instead of 8.5 g.
    candidates = {0.0}
    max_large_spoons = int(amount // 15.0)
    small_spoons = (0.0, *MEASURING_SPOON_SIZES)
    for large_count in range(max_large_spoons + 1):
        base = large_count * 15.0
        for first in small_spoons:
            for second in small_spoons:
                candidate = base + first + second
                if candidate <= amount + 1e-9:
                    candidates.add(candidate)

    return max(candidates)


def _target_range(conf: dict, min_key: str, max_key: str, legacy_key: str, default: float) -> tuple[float, float]:
    """Return an ordered min/max target range with legacy single-target fallback."""
    legacy_target = float(conf.get(legacy_key, default))
    low = float(conf.get(min_key, legacy_target))
    high = float(conf.get(max_key, legacy_target))
    return (low, high) if low <= high else (high, low)


def calculate_pool_chemistry(
    conf: dict,
    c_ist: float | None,
    ph_ist: float | None,
    temp_ist: float | None,
    pool_covered: bool,
    usage_mode: str,
    weather_today: dict | None,
    chlor_dose_factor: float | None = None,
) -> dict:
    """Calculate dosage recommendations and detailed chemistry breakdowns."""
    volumen = conf.get(CONF_POOL_VOLUME, 1.0)
    c_min, c_max = _target_range(conf, CONF_CHLOR_MIN, CONF_CHLOR_MAX, CONF_CHLOR_TARGET, 1.5)
    ph_min, ph_max = _target_range(conf, CONF_PH_MIN, CONF_PH_MAX, CONF_PH_TARGET, 7.2)
    wirkstoff = conf.get(CONF_CHLOR_CONTENT, 0.56)

    if wirkstoff <= 0:
        wirkstoff = 0.56
    if chlor_dose_factor and chlor_dose_factor > 0:
        wirkstoff *= chlor_dose_factor

    volume_m3 = max(float(volumen), 0.0)

    c_diff = max(float(c_min) - float(c_ist), 0) if c_ist is not None else 0

    temp_target_extra = 0.0
    if temp_ist is not None:
        if float(temp_ist) > 32:
            temp_target_extra = 0.7
        elif float(temp_ist) > 28:
            temp_target_extra = 0.3

    env_target_extra = 0.0 if pool_covered else 0.3

    uv_target_extra = 0.0
    if weather_today and weather_today.get("has_forecast"):
        uv_index = weather_today.get("uv_index")
        if uv_index is not None:
            if uv_index >= 8:
                uv_target_extra = 0.6
            elif uv_index >= 6:
                uv_target_extra = 0.3

    bather_target_extra = 0.0
    if usage_mode == "normal":
        bather_target_extra = 0.5
    elif usage_mode == "party":
        bather_target_extra = 1.0

    shock_target = 0.0
    if c_ist is not None:
        if float(c_ist) < 0.1:
            shock_target = 5.0
        elif float(c_ist) < 0.3:
            shock_target = 4.0
        elif float(c_ist) < 0.6:
            shock_target = 3.0
        elif float(c_ist) < 1.0:
            shock_target = 2.0

    base_target_with_conditions = float(c_min) + temp_target_extra + env_target_extra + uv_target_extra
    effective_target = base_target_with_conditions + bather_target_extra
    if shock_target > 0:
        effective_target = max(base_target_with_conditions, shock_target) + bather_target_extra

    min_dose = 2.0 * volume_m3
    if c_ist is not None:
        if float(c_ist) < 0.3:
            min_dose = 6.0 * volume_m3
        elif float(c_ist) < 0.8:
            min_dose = 3.0 * volume_m3

    max_target = 10.0
    max_dose = max(max_target - float(c_ist or 0.0), 0.0) * volume_m3 / wirkstoff

    chlor_base_amount_raw = c_diff * volume_m3 / wirkstoff
    chlor_breakdown_temp_adj_raw = temp_target_extra * volume_m3 / wirkstoff
    chlor_breakdown_env_adj_raw = env_target_extra * volume_m3 / wirkstoff
    chlor_breakdown_uv_adj_raw = uv_target_extra * volume_m3 / wirkstoff
    chlor_breakdown_bather_adj_raw = bather_target_extra * volume_m3 / wirkstoff
    chlor_breakdown_shock_adj_raw = max(shock_target - base_target_with_conditions, 0.0) * volume_m3 / wirkstoff
    target_diff = max(effective_target - float(c_ist), 0.0) if c_ist is not None else 0.0
    raw_chlor = target_diff * volume_m3 / wirkstoff

    if c_ist is not None and c_ist >= c_min:
        s_g = 0.0
    else:
        s_g = (
            round_to_measuring_spoons(min(max(raw_chlor, min_dose), max_dose))
            if c_ist is not None
            else 0.0
        )

    weather_note = None
    if weather_today and weather_today.get("has_forecast"):
        rain_probability = weather_today.get("precipitation_probability")
        rain_amount = weather_today.get("precipitation_amount")
        if (rain_amount is not None and rain_amount >= 10.0) or (
            rain_probability is not None and rain_probability >= 70.0
        ):
            weather_note = "Regen erwartet: Danach moeglichst erneut messen."

    ph_diff = 0.0
    if ph_ist is not None:
        if ph_ist < ph_min:
            ph_diff = ph_min - ph_ist
        elif ph_ist > ph_max:
            ph_diff = ph_max - ph_ist
    ph_diff_abs = abs(ph_diff)

    ph_senker_ml = 0.0
    ph_erhoeher_g = 0.0

    if ph_diff < 0:
        factor = conf[CONF_PH_DOWN_DOSAGE] / 10.0 / 0.2
        ph_senker_ml = round_to_measuring_spoons(ph_diff_abs * factor * volumen)
    elif ph_diff > 0:
        factor = conf[CONF_PH_UP_DOSAGE] / 10.0 / 0.1
        ph_erhoeher_g = round_to_measuring_spoons(ph_diff_abs * factor * volumen)

    return {
        "chlor_dose": s_g,
        "chlor_pre": round_to_measuring_spoons(max(s_g * 0.3, 1.0 * volume_m3)) if s_g > 0 else 0.0,
        "ph_senker_total": ph_senker_ml,
        "ph_erhoeher_total": ph_erhoeher_g,
        "ph_diff": ph_diff,
        "is_shock": (c_ist is not None and 3.0 <= float(c_ist) <= 5.0),
        "chlor_target": c_min,
        "chlor_min": c_min,
        "chlor_max": c_max,
        "ph_target": ph_min,
        "ph_min": ph_min,
        "ph_max": ph_max,
        "chlor_breakdown_base": round(chlor_base_amount_raw, 2),
        "chlor_breakdown_shock_adj": round(chlor_breakdown_shock_adj_raw, 2),
        "chlor_breakdown_temp_adj": round(chlor_breakdown_temp_adj_raw, 2),
        "chlor_breakdown_env_adj": round(chlor_breakdown_env_adj_raw, 2),
        "chlor_breakdown_uv_adj": round(chlor_breakdown_uv_adj_raw, 2),
        "chlor_breakdown_bather_adj": round(chlor_breakdown_bather_adj_raw, 2),
        "chlor_breakdown_sum_raw": round(raw_chlor, 2),
        "chlor_breakdown_min_dose_applied": round(min_dose, 2) if (s_g > 0 and raw_chlor < min_dose) else 0.0,
        "weather_note": weather_note,
        "volume_m3": volume_m3,
        "volume_liters": round(volume_m3 * 1000.0, 0),
        "effective_chlor_content": round(wirkstoff, 3),
    }


def calculate_retest_status(
    chlor_dose: float,
    ph_senker_total: float,
    ph_erhoeher_total: float,
    dt_last_meas: datetime | None,
    dt_last_chlor_action: datetime | None,
    dt_last_ph_plus_action: datetime | None,
    dt_last_ph_minus_action: datetime | None,
) -> dict:
    """Determine whether logged maintenance actions require a new measurement."""
    chlor_logged_after_measurement = bool(
        dt_last_meas and dt_last_chlor_action and dt_last_chlor_action > dt_last_meas
    )
    ph_plus_logged_after_measurement = bool(
        dt_last_meas and dt_last_ph_plus_action and dt_last_ph_plus_action > dt_last_meas
    )
    ph_minus_logged_after_measurement = bool(
        dt_last_meas and dt_last_ph_minus_action and dt_last_ph_minus_action > dt_last_meas
    )

    awaiting_retest_chlor = chlor_dose > 0 and chlor_logged_after_measurement
    awaiting_retest_ph = (
        (ph_senker_total > 0 and ph_minus_logged_after_measurement)
        or (ph_erhoeher_total > 0 and ph_plus_logged_after_measurement)
    )

    chemistry_actions_covered = []
    relevant_action_dts = []
    if chlor_dose > 0:
        chemistry_actions_covered.append(chlor_logged_after_measurement)
        if dt_last_chlor_action:
            relevant_action_dts.append(dt_last_chlor_action)
    if ph_senker_total > 0:
        chemistry_actions_covered.append(ph_minus_logged_after_measurement)
        if dt_last_ph_minus_action:
            relevant_action_dts.append(dt_last_ph_minus_action)
    if ph_erhoeher_total > 0:
        chemistry_actions_covered.append(ph_plus_logged_after_measurement)
        if dt_last_ph_plus_action:
            relevant_action_dts.append(dt_last_ph_plus_action)

    awaiting_retest = awaiting_retest_chlor or awaiting_retest_ph

    return {
        "awaiting_retest": awaiting_retest,
        "awaiting_retest_chlor": awaiting_retest_chlor,
        "awaiting_retest_ph": awaiting_retest_ph,
        "awaiting_retest_since": max(relevant_action_dts).isoformat()
        if awaiting_retest and relevant_action_dts
        else None,
    }


def build_recommendation(
    awaiting_retest: bool,
    ph_ist: float | None,
    c_ist: float | None,
    ph_min: float,
    ph_max: float,
    c_min: float,
    c_max: float,
    chlor_dose: float,
) -> str:
    """Build the user-facing recommendation text."""
    warnings = []

    current_ph = float(ph_ist) if ph_ist is not None else None
    target_ph_min = float(ph_min)
    target_ph_max = float(ph_max)
    current_c = float(c_ist) if c_ist is not None else None
    target_c_min = float(c_min)
    target_c_max = float(c_max)

    if current_ph is not None:
        if current_ph > (target_ph_max + 0.1):
            warnings.append("pH zu hoch")
        elif current_ph < (target_ph_min - 0.1):
            warnings.append("pH zu niedrig")

    if current_c is not None:
        if 3.0 <= current_c <= 5.0:
            warnings.append("Chlor im Sto\u00dfchlorbereich")
        elif current_c < 0.5:
            warnings.append("Sto\u00dfchlorung empfohlen")
        elif current_c > (target_c_max + 0.2):
            warnings.append("Chlor zu hoch")
        elif current_c < (target_c_min - 0.2) and chlor_dose > 0:
            warnings.append("Chlor nachdosieren")

    if awaiting_retest:
        return "\u23f3 Warten auf erneute Messung"
    if not warnings:
        return "\u2705 Alle Werte im Zielbereich"
    return "\u26a0\ufe0f " + " & ".join(warnings)
