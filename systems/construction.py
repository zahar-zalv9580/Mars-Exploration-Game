"""
Система часу будівництва.

Базовий час залежить від типу будівлі.
Модифікатор від популяції: більше вільних workers = швидше.
  time_modifier = 1.0 / (1.0 + free_workers * 0.1)
  тобто 10 вільних workers = в 2 рази швидше, але не більше ніж x5.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from entities.building import BuildingType, BuildingState, Building

# Базовий час будівництва в секундах
BASE_BUILD_TIME: dict[BuildingType, float] = {
    BuildingType.HUB:        0.0,    # стартова — миттєво
    BuildingType.HABITAT:    20.0,
    BuildingType.GREENHOUSE: 15.0,
    BuildingType.SOLAR:      10.0,
    BuildingType.EXTRACTOR:  25.0,
    BuildingType.STORAGE:    15.0,
    BuildingType.FACTORY:    40.0,
    BuildingType.LABORATORY: 35.0,
    BuildingType.JAMMER:     120.0,
}

MIN_TIME_MOD = 0.2   # максимальне прискорення x5


@dataclass
class ConstructionQueue:
    """Зберігає будівлі що будуються і відстежує прогрес."""

    _queue: dict[tuple[int,int], float] = field(default_factory=dict)
    # (tx, ty) -> залишилось секунд

    def add(self, building: Building, free_workers: int):
        base = BASE_BUILD_TIME[building.type]
        if base == 0.0:
            building.state = BuildingState.ACTIVE
            return
        mod  = max(MIN_TIME_MOD, 1.0 / (1.0 + free_workers * 0.1))
        time = base * mod
        building.state = BuildingState.CONSTRUCTING
        self._queue[(building.tx, building.ty)] = time

    def tick(self, buildings: dict, dt: float) -> list[Building]:
        """Оновлює прогрес. Повертає список щойно добудованих будівель."""
        finished = []
        for key in list(self._queue):
            self._queue[key] -= dt
            if self._queue[key] <= 0:
                del self._queue[key]
                b = buildings.get(key)
                if b:
                    b.state = BuildingState.ACTIVE
                    finished.append(b)
        return finished

    def progress(self, tx: int, ty: int, building_type: BuildingType) -> float | None:
        """Прогрес 0.0-1.0, None якщо не будується."""
        remaining = self._queue.get((tx, ty))
        if remaining is None:
            return None
        total = BASE_BUILD_TIME[building_type]
        if total == 0:
            return None
        return max(0.0, 1.0 - remaining / total)
