from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

import requests
from django.core.cache import cache
from django.utils.text import slugify

from accounts.models import City, State

logger = logging.getLogger(__name__)


class LocationResolutionError(Exception):
    """Base error for location resolution workflow."""


class CityNotCoveredError(LocationResolutionError):
    """Raised when the resolved coordinates point to a city we do not handle."""


@dataclass(frozen=True, slots=True)
class ReverseGeocodeResult:
    latitude: float
    longitude: float
    city_name: str | None
    state_name: str | None
    state_code: str | None
    country_code: str | None
    raw: dict[str, Any]


_SESSION = requests.Session()
_BASE_URL = os.getenv("GEOCODING_NOMINATIM_URL", "https://nominatim.openstreetmap.org/reverse")
_USER_AGENT = os.getenv("GEOCODING_USER_AGENT", "CityCare/1.0 (+https://example.com)")
_TIMEOUT = float(os.getenv("GEOCODING_TIMEOUT_SECONDS", "5"))
_CACHE_SECONDS = int(os.getenv("GEOCODING_CACHE_SECONDS", "86400"))
_CITY_KEYS = [
    "city",
    "town",
    "village",
    "municipality",
    "city_district",
    "county",
]


def reverse_geocode(latitude: Decimal | float, longitude: Decimal | float) -> ReverseGeocodeResult:
    """
    Resolve coordinates into city/state metadata using the Nominatim API.
    """
    lat = float(latitude)
    lon = float(longitude)
    cache_key = f"reverse_geo:{round(lat, 5):.5f}:{round(lon, 5):.5f}"
    cached = cache.get(cache_key)
    if cached:
        return ReverseGeocodeResult(**cached)

    params = {
        "format": "jsonv2",
        "lat": f"{lat:.6f}",
        "lon": f"{lon:.6f}",
        "zoom": os.getenv("GEOCODING_NOMINATIM_ZOOM", "13"),
        "addressdetails": 1,
    }
    headers = {
        "User-Agent": _USER_AGENT,
        "Accept": "application/json",
        "Accept-Language": os.getenv("GEOCODING_ACCEPT_LANGUAGE", "pt-BR,en"),
    }

    try:
        response = _SESSION.get(_BASE_URL, params=params, headers=headers, timeout=_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:  # pragma: no cover - network failure path
        logger.warning("Reverse geocoding failed: %s", exc)
        raise LocationResolutionError("Nao foi possivel consultar o servico de geocodificacao.") from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - invalid JSON
        logger.warning("Reverse geocoding returned invalid JSON: %s", exc)
        raise LocationResolutionError("Resposta invalida do servico de geocodificacao.") from exc

    address = payload.get("address") or {}
    result = ReverseGeocodeResult(
        latitude=lat,
        longitude=lon,
        city_name=_extract_city_name(address),
        state_name=address.get("state"),
        state_code=_extract_state_code(address),
        country_code=_safe_upper(address.get("country_code")),
        raw=payload,
    )
    cache.set(cache_key, asdict(result), timeout=_CACHE_SECONDS)
    return result


def resolve_city_from_coordinates(latitude, longitude) -> City:
    """
    Reverse geocode and map the result to a City persisted in our database.
    """
    result = reverse_geocode(latitude, longitude)
    if not result.city_name:
        raise CityNotCoveredError("Nao foi possivel identificar a cidade das coordenadas informadas.")

    state = _find_state(result)
    if not state:
        raise CityNotCoveredError("Estado nao suportado ou nao configurado na plataforma.")

    city = _find_city(state, result.city_name)
    if not city:
        raise CityNotCoveredError(
            "Cidade fora da cobertura configurada. Contate o suporte para adicionar essa localidade."
        )
    return city


def _find_state(result: ReverseGeocodeResult) -> State | None:
    if result.state_code:
        abbreviations = (
            clean
            for clean in (
                result.state_code.upper(),
                result.state_code.split("-")[-1].upper() if "-" in result.state_code else None,
            )
            if clean
        )
        for abbr in abbreviations:
            match = State.objects.filter(abbreviation__iexact=abbr).first()
            if match:
                return match

    if result.state_name:
        match = State.objects.filter(name__iexact=result.state_name).first()
        if match:
            return match
    return None


def _find_city(state: State, target_name: str) -> City | None:
    exact = City.objects.filter(state=state, name__iexact=target_name).first()
    if exact:
        return exact

    normalized_target = _normalize_name(target_name)
    for city in City.objects.filter(state=state):
        if _normalize_name(city.name) == normalized_target:
            return city
    return None


def _normalize_name(value: str) -> str:
    return slugify(value or "").replace("-", "")


def _extract_city_name(address: dict[str, Any]) -> str | None:
    for key in _CITY_KEYS:
        value = address.get(key)
        if value:
            return value
    return None


def _extract_state_code(address: dict[str, Any]) -> str | None:
    for key in ("state_code", "ISO3166-2-lvl4", "ISO3166-2-lvl6"):
        value = address.get(key)
        if value:
            cleaned = value.split("-")[-1]
            if len(cleaned) == 2:
                return cleaned.upper()
            return value.upper()
    return None


def _safe_upper(value: str | None) -> str | None:
    if value:
        return value.upper()
    return None
