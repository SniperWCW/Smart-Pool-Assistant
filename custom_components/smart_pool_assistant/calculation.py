"""Chemistry calculation helpers for Smart Pool Assistant."""
from __future__ import annotations

from datetime import datetime

from .const import (
    CONF_CHLOR_CONTENT,
    CONF_CHLOR_TARGET,
    CONF_PH_DOWN_DOSAGE,
    CONF_PH_TARGET,
    CONF_PH_UP_DOSAGE,
    CONF_POOL_VOLUME,
)


def calculate_pool_chemistry(
    conf: dict,
    c_ist: float | None,
    ph_ist: float | None,
    temp_ist: float | None,
    pool_covered: bool,
    usage_mode: str,
    weather_today: dict | None,
) -> dict:
    """Calculate dosage recommendations and detailed chemistry breakdowns."""
    volumen = conf.get(CONF_POOL_VOLUME, 1.0)
    c_ziel = conf.get(CONF_CHLOR_TARGET, 1.5)
    ph_ziel = conf.get(CONF_PH_TARGET, 7.2)
    wirkstoff = conf.get(CONF_CHLOR_CONTENT, 0.56)

    if wirkstoff <= 0:
        wirkstoff = 0.56

    volume_m3 = max(float(volumen), 0.0)

    c_diff = max(float(c_ziel) - float(c_ist), 0) if c_ist is not None else 0

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

    base_target_with_conditions = float(c_ziel) + temp_target_extra + env_target_extra + uv_target_extra
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

    if c_ist is not None and c_ist >= c_ziel:
        s_g = 0.0
    else:
        s_g = round(min(max(raw_chlor, min_dose), max_dose), 1) if c_ist is not None else 0.0

    weather_note = None
    if weather_today and weather_today.get("has_forecast"):
        rain_probability = weather_today.get("precipitation_probability")
        rain_amount = weather_today.get("precipitation_amount")
        if (rain_amount is not None and rain_amount >= 10.0) or (
            rain_probability is not None and rain_probability >= 70.0
        ):
            weather_note = "Regen erwartet: Danach moeglichst erneut messen."

    ph_diff = ph_ziel - ph_ist if ph_ist is not None else 0
    ph_diff_abs = abs(ph_diff)

    ph_senker_ml = 0.0
    ph_erhoeher_g = 0.0

    if ph_diff < 0:
        factor = conf[CONF_PH_DOWN_DOSAGE] / 10.0 / 0.2
        ph_senker_ml = round(ph_diff_abs * factor * volumen, 1)
    elif ph_diff > 0:
        factor = conf[CONF_PH_UP_DOSAGE] / 10.0 / 0.1
        ph_erhoeher_g = round(ph_diff_abs * factor * volumen, 1)

    return {
        "chlor_dose": s_g,
        "chlor_pre": round(max(s_g * 0.3, 1.0 * volume_m3), 1) if s_g > 0 else 0.0,
        "ph_senker_total": ph_senker_ml,
        "ph_erhoeher_total": ph_erhoeher_g,
        "ph_diff": ph_diff,
        "is_shock": (c_ist is not None and c_ist < 0.5),
        "chlor_target": c_ziel,
        "ph_target": ph_ziel,
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

    awaiting_retest = bool(chemistry_actions_covered) and all(chemistry_actions_covered)

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
    ph_ziel: float,
    c_ziel: float,
    chlor_dose: float,
) -> str:
    """Build the user-facing recommendation text."""
    warnings = []

    current_ph = float(ph_ist) if ph_ist is not None else None
    target_ph = float(ph_ziel)
    current_c = float(c_ist) if c_ist is not None else None
    target_c = float(c_ziel)

    if current_ph is not None:
        if current_ph > (target_ph + 0.1):
            warnings.append("pH zu hoch")
        elif current_ph < (target_ph - 0.1):
            warnings.append("pH zu niedrig")

    if current_c is not None:
        if current_c < 0.5:
            warnings.append("Sto\u00dfchlorung empfohlen")
        elif current_c > (target_c + 0.2):
            warnings.append("Chlor zu hoch")
        elif current_c < (target_c - 0.2) and chlor_dose > 0:
            warnings.append("Chlor nachdosieren")

    if awaiting_retest:
        return "\u23f3 Warten auf erneute Messung"
    if not warnings:
        return "\u2705 Alle Werte im Zielbereich"
    return "\u26a0\ufe0f " + " & ".join(warnings)
