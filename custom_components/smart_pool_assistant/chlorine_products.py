"""Helpers for chlorine product defaults and normalization."""
from __future__ import annotations


ORGANIC_DEFAULT_CHLOR_CONTENT = 0.56
INORGANIC_DEFAULT_CHLOR_CONTENT = 0.65


def normalize_chlor_product_type(value: object) -> str:
    """Return a supported chlorine product type."""
    return value if value in {"organic", "inorganic"} else "organic"


def default_chlor_content_for_product_type(product_type: object) -> float:
    """Return the default active-chlorine fraction for the configured product type."""
    if normalize_chlor_product_type(product_type) == "inorganic":
        return INORGANIC_DEFAULT_CHLOR_CONTENT
    return ORGANIC_DEFAULT_CHLOR_CONTENT


def resolve_chlor_content(product_type: object, chlor_content: object) -> float:
    """Return a positive active-chlorine fraction with product-type fallback."""
    try:
        value = float(chlor_content)
    except (TypeError, ValueError):
        value = 0.0
    if value > 0:
        return value
    return default_chlor_content_for_product_type(product_type)
