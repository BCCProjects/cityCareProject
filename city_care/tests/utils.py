from __future__ import annotations

from accounts.models import City, Organization, State

_FORCED_CITY_ID: int | None = None


def ensure_location(name: str = "Brasilia"):
    state, _ = State.objects.get_or_create(
        abbreviation="DF",
        defaults={"name": "Distrito Federal"},
    )
    city, _ = City.objects.get_or_create(name=name, state=state)
    organization, _ = Organization.objects.get_or_create(name=f"{city.name} Org", city=city)
    return state, city, organization


def force_resolved_city(city: City):
    global _FORCED_CITY_ID
    _FORCED_CITY_ID = city.id
    return city


def get_forced_city() -> City:
    global _FORCED_CITY_ID
    if _FORCED_CITY_ID is None:
        _, city, _ = ensure_location("Default Test City")
        _FORCED_CITY_ID = city.id
    return City.objects.get(pk=_FORCED_CITY_ID)


def reset_forced_city():
    global _FORCED_CITY_ID
    _FORCED_CITY_ID = None
