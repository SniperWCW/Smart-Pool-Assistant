"""Notification helpers for Smart Pool Assistant."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    CONF_FILTER_CLEAN_INTERVAL,
    CONF_FILTER_CLEAN_RED_THRESHOLD,
    CONF_FILTER_CLEAN_YELLOW_THRESHOLD,
    CONF_FILTER_REPLACE_INTERVAL,
    CONF_FILTER_REPLACE_RED_THRESHOLD,
    CONF_FILTER_REPLACE_YELLOW_THRESHOLD,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_SERVICE_2,
    CONF_PERSISTENT_NOTIFICATION,
    DOMAIN,
)
from .maintenance import get_time_since_last_action


async def async_send_notification(
    hass: HomeAssistant,
    conf: dict,
    message: str,
    notification_id: str,
) -> None:
    """Send a persistent and/or service notification."""
    if conf.get(CONF_PERSISTENT_NOTIFICATION):
        await hass.services.async_call("persistent_notification", "create", {
            "title": "Smart Pool Assistant",
            "message": message,
            "notification_id": f"{DOMAIN}_{notification_id}",
        })

    for service in _notify_services(conf):
        domain, service_name = service.split(".", 1)
        await hass.services.async_call(domain, service_name, {
            "title": "Smart Pool Assistant",
            "message": message,
        })


async def async_send_follow_up(
    hass: HomeAssistant,
    conf: dict,
) -> None:
    """Send the chemical follow-up notification."""
    await async_send_notification(
        hass,
        conf,
        "Die Einwirkzeit ist um. Bitte Pool-Werte erneut pr\u00fcfen!",
        "follow_up",
    )


async def async_check_filter_notifications(
    hass: HomeAssistant,
    conf: dict,
    history: dict,
) -> None:
    """Check and send notifications for filter maintenance."""
    now = dt_util.now()

    hours_since_clean = get_time_since_last_action(history, "filter_clean", in_hours=True)
    if hours_since_clean is not None:
        clean_interval = conf.get(CONF_FILTER_CLEAN_INTERVAL, 24)
        clean_yellow = conf.get(CONF_FILTER_CLEAN_YELLOW_THRESHOLD, 4)
        clean_red = conf.get(CONF_FILTER_CLEAN_RED_THRESHOLD, 0)

        if hours_since_clean > 0 and (clean_interval - clean_yellow) <= hours_since_clean < clean_interval:
            last_notified = history.get("last_notified_clean_yellow")
            if _should_notify_daily(now, last_notified):
                await async_send_notification(
                    hass,
                    conf,
                    f"Filterreinigung bald f\u00e4llig! Vor {hours_since_clean} Stunden gereinigt. Empfohlen alle {clean_interval} Stunden.",
                    "filter_clean_yellow",
                )
                history["last_notified_clean_yellow"] = now.isoformat()

        if hours_since_clean >= (clean_interval + clean_red):
            last_notified = history.get("last_notified_clean_red")
            if _should_notify_daily(now, last_notified):
                await async_send_notification(
                    hass,
                    conf,
                    f"Filterreinigung \u00dcBERF\u00c4LLIG! Vor {hours_since_clean} Stunden gereinigt. Empfohlen alle {clean_interval} Stunden.",
                    "filter_clean_red",
                )
                history["last_notified_clean_red"] = now.isoformat()

    days_since_replace = get_time_since_last_action(history, "filter_replace")
    if days_since_replace is not None:
        replace_interval = conf.get(CONF_FILTER_REPLACE_INTERVAL, 180)
        replace_yellow = conf.get(CONF_FILTER_REPLACE_YELLOW_THRESHOLD, 30)
        replace_red = conf.get(CONF_FILTER_REPLACE_RED_THRESHOLD, 0)

        if days_since_replace > 0 and (replace_interval - replace_yellow) <= days_since_replace < replace_interval:
            last_notified = history.get("last_notified_replace_yellow")
            if _should_notify_daily(now, last_notified):
                await async_send_notification(
                    hass,
                    conf,
                    f"Filterwechsel bald f\u00e4llig! Vor {days_since_replace} Tagen gewechselt. Empfohlen alle {replace_interval} Tage.",
                    "filter_replace_yellow",
                )
                history["last_notified_replace_yellow"] = now.isoformat()

        if days_since_replace >= (replace_interval + replace_red):
            last_notified = history.get("last_notified_replace_red")
            if _should_notify_daily(now, last_notified):
                await async_send_notification(
                    hass,
                    conf,
                    f"Filterwechsel \u00dcBERF\u00c4LLIG! Vor {days_since_replace} Tagen gewechselt. Empfohlen alle {replace_interval} Tage.",
                    "filter_replace_red",
                )
                history["last_notified_replace_red"] = now.isoformat()


def _should_notify_daily(now, last_notified: str | None) -> bool:
    if not last_notified:
        return True

    last_notified_dt = dt_util.parse_datetime(last_notified)
    if last_notified_dt is None:
        return True

    return (now - last_notified_dt).days >= 1


def _notify_services(conf: dict) -> list[str]:
    """Return configured notify services without duplicates."""
    services = []
    for key in (CONF_NOTIFY_SERVICE, CONF_NOTIFY_SERVICE_2):
        service = conf.get(key)
        if service and service not in services:
            services.append(service)
    return services
