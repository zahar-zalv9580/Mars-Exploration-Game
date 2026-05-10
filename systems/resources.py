from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class Resource(Enum):
    ENERGY  = "energy"
    IRON    = "iron"
    WATER   = "water"
    SILICON = "silicon"
    FUEL    = "fuel"
    URANIUM = "uranium"
    FOOD    = "food"


BASE_CAPACITY: dict[Resource, float] = {
    Resource.ENERGY:  200.0,
    Resource.IRON:    150.0,
    Resource.WATER:   100.0,
    Resource.SILICON: 100.0,
    Resource.FUEL:     50.0,
    Resource.URANIUM:  20.0,
    Resource.FOOD:    120.0,
}

STORAGE_BONUS: dict[Resource, float] = {
    Resource.ENERGY:   0.0,
    Resource.IRON:    200.0,
    Resource.WATER:   150.0,
    Resource.SILICON: 150.0,
    Resource.FUEL:    100.0,
    Resource.URANIUM:  50.0,
    Resource.FOOD:    150.0,
}

# Базова виробка екстрактора по ресурсу
EXTRACTOR_BASE: dict[str, float] = {
    "iron":    1.5,
    "water":   1.2,
    "silicon": 1.0,
    "fuel":    0.8,
    "uranium": 0.3,
}

# Відповідність назви ресурсу клітинки до Resource enum
TILE_RESOURCE_MAP: dict[str, Resource] = {
    "iron":    Resource.IRON,
    "water":   Resource.WATER,
    "silicon": Resource.SILICON,
    "fuel":    Resource.FUEL,
    "uranium": Resource.URANIUM,
}

SOLAR_BASE_OUTPUT = 5.0   # базова виробка сонячної панелі (до solar_modifier)


@dataclass
class ResourceSystem:
    _amounts:       dict[Resource, float] = field(default_factory=dict)
    _capacity:      dict[Resource, float] = field(default_factory=dict)
    _storage_count: int = 0

    # Дельти за останній тік (для відображення ±)
    _delta:  dict[Resource, float] = field(default_factory=dict)
    _prev:   dict[Resource, float] = field(default_factory=dict)

    def __post_init__(self):
        for r in Resource:
            self._amounts[r]  = 0.0
            self._capacity[r] = BASE_CAPACITY[r]
            self._delta[r]    = 0.0
            self._prev[r]     = 0.0

    # ---------------------------------------------------------------- query

    def amount(self, r: Resource) -> float:
        return self._amounts[r]

    def capacity(self, r: Resource) -> float:
        return self._capacity[r]

    def ratio(self, r: Resource) -> float:
        cap = self._capacity[r]
        return self._amounts[r] / cap if cap > 0 else 0.0

    def delta(self, r: Resource) -> float:
        """Зміна за останній тік (+/-)."""
        return self._delta[r]

    def can_afford(self, costs: dict[Resource, float]) -> bool:
        return all(self._amounts[r] >= v for r, v in costs.items())

    # ---------------------------------------------------------------- modify

    def add(self, r: Resource, amount: float) -> float:
        space = self._capacity[r] - self._amounts[r]
        added = min(amount, space)
        self._amounts[r] += added
        return added

    def consume(self, r: Resource, amount: float) -> bool:
        if self._amounts[r] < amount:
            return False
        self._amounts[r] -= amount
        return True

    def consume_many(self, costs: dict[Resource, float]) -> bool:
        if not self.can_afford(costs):
            return False
        for r, v in costs.items():
            self._amounts[r] -= v
        return True

    def set(self, r: Resource, value: float):
        self._amounts[r] = max(0.0, min(value, self._capacity[r]))

    # ---------------------------------------------------------------- storage

    def add_storage(self, count: int = 1):
        self._storage_count += count
        self._recalc_capacity()

    def remove_storage(self, count: int = 1):
        self._storage_count = max(0, self._storage_count - count)
        self._recalc_capacity()
        for r in Resource:
            self._amounts[r] = min(self._amounts[r], self._capacity[r])

    def _recalc_capacity(self):
        for r in Resource:
            self._capacity[r] = BASE_CAPACITY[r] + STORAGE_BONUS[r] * self._storage_count

    # ---------------------------------------------------------------- delta tracking

    def snapshot(self):
        """Викликати перед тіком."""
        for r in Resource:
            self._prev[r] = self._amounts[r]

    def calc_delta(self):
        """Викликати після тіку."""
        for r in Resource:
            self._delta[r] = self._amounts[r] - self._prev[r]

    # ---------------------------------------------------------------- extractor output

    @staticmethod
    def extractor_output(tile_res_name: str, richness: int, dt: float) -> tuple[Resource, float]:
        """Розраховує виробку екстрактора на клітинці."""
        base    = EXTRACTOR_BASE.get(tile_res_name, 1.0)
        res     = TILE_RESOURCE_MAP[tile_res_name]
        amount  = base * richness * dt
        return res, amount

    # ---------------------------------------------------------------- solar output

    @staticmethod
    def solar_output(solar_modifier: float, dt: float) -> float:
        """Виробка сонячної панелі залежно від висоти тайлу."""
        return SOLAR_BASE_OUTPUT * solar_modifier * dt
