"""
PopulationManager — популяція як ресурс/workforce.

population       — поточна кількість людей
capacity         — максимум (залежить від Habitat)
workers_total    — всього робітників (= population)
workers_used     — зайнято будівлями
workers_free     — вільні

Кожен тік:
  - споживає food/water/energy на людину
  - якщо бракує — смерть колоністів
  - кожні ARRIVAL_INTERVAL днів — прибуває транспорт (якщо є місце/ресурси)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from systems.resources import ResourceSystem, Resource

# Споживання на людину за тік (1 тік = 1 секунда реального часу)
# В грі 1 день = DAY_DURATION секунд — масштабуємо при потребі
UPKEEP_PER_PERSON: dict[Resource, float] = {
    Resource.FOOD:   0.05,
    Resource.WATER:  0.03,
    Resource.ENERGY: 0.02,
}

# Базова місткість без жодного Habitat
BASE_CAPACITY = 0

# Скільки людей додає один Habitat рівня 1
HABITAT_CAPACITY = 5

# Інтервал прибуття транспорту (у секундах реального часу)
ARRIVAL_INTERVAL = 60.0   # раз на хвилину (~кілька ігрових днів)
ARRIVAL_COUNT    = 4       # скільки колоністів прибуває

# Вимоги до будівель (workers)
BUILDING_WORKERS: dict[str, int] = {
    "hub":        0,
    "habitat":    0,
    "greenhouse": 1,
    "solar":      0,
    "extractor":  2,
    "storage":    0,
    "factory":    3,
    "laboratory": 2,
    "jammer":     6,
}

# Мінімум населення для розблокування будівлі
BUILDING_MIN_POP: dict[str, int] = {
    "hub":        0,
    "habitat":    0,
    "greenhouse": 0,
    "solar":      0,
    "extractor":  0,
    "storage":    0,
    "factory":    5,
    "laboratory": 8,
    "jammer":     20,
}


@dataclass
class PopulationManager:
    population:    int   = 4      # стартова колонія
    capacity:      int   = 5      # базовий ліміт (перший Habitat вже є)
    _habitat_count: int  = 1

    _workers_used:  int  = 0
    _arrival_timer: float = 0.0

    # Логи подій (для UI)
    events: list[str] = field(default_factory=list)

    # ---------------------------------------------------------------- query

    @property
    def workers_free(self) -> int:
        return max(0, self.population - self._workers_used)

    @property
    def workers_used(self) -> int:
        return self._workers_used

    @property
    def is_at_capacity(self) -> bool:
        return self.population >= self.capacity

    def can_unlock(self, building_type_value: str) -> bool:
        return self.population >= BUILDING_MIN_POP.get(building_type_value, 0)

    def workers_needed(self, building_type_value: str) -> int:
        return BUILDING_WORKERS.get(building_type_value, 0)

    # ---------------------------------------------------------------- habitat

    def add_habitat(self, count: int = 1):
        self._habitat_count += count
        self.capacity = BASE_CAPACITY + self._habitat_count * HABITAT_CAPACITY

    def remove_habitat(self, count: int = 1):
        self._habitat_count = max(0, self._habitat_count - count)
        self.capacity = BASE_CAPACITY + self._habitat_count * HABITAT_CAPACITY
        # Люди не зникають миттєво — але нові не прибувають
        self.population = min(self.population, self.capacity)

    # ---------------------------------------------------------------- workers

    def assign_workers(self, buildings: dict) -> dict[tuple, bool]:
        """
        Розподіляє workers по будівлях (greedy — порядок розміщення).
        Повертає dict {(tx,ty): has_workers}.
        """
        available = self.population
        result    = {}
        used      = 0
        for (tx, ty), b in buildings.items():
            needed = BUILDING_WORKERS.get(b.type.value, 0)
            if available >= needed:
                available -= needed
                used      += needed
                result[(tx, ty)] = True
            else:
                result[(tx, ty)] = False
        self._workers_used = used
        return result

    # ---------------------------------------------------------------- tick

    def tick(self, resources: ResourceSystem, dt: float):
        if self.population <= 0:
            return

        # Споживання ресурсів
        shortage = False
        for r, rate in UPKEEP_PER_PERSON.items():
            total = rate * self.population * dt
            if not resources.consume(r, total):
                shortage = True

        # Смерть від нестачі
        if shortage:
            self.population = max(0, self.population - 1)
            cause = "starvation" if not resources.consume(Resource.FOOD, 0) else "resource shortage"
            self._log(f"COLONIST LOST — {cause.upper()}")

        # Прибуття транспорту
        self._arrival_timer += dt
        if self._arrival_timer >= ARRIVAL_INTERVAL:
            self._arrival_timer = 0.0
            self._try_arrival(resources)

    def _try_arrival(self, resources: ResourceSystem):
        space = self.capacity - self.population
        if space <= 0:
            return
        # Потрібні базові ресурси для прийому
        count = min(ARRIVAL_COUNT, space)
        has_food   = resources.amount(Resource.FOOD)   >= count * 5
        has_energy = resources.amount(Resource.ENERGY) >= count * 2
        if has_food and has_energy:
            self.population += count
            self._log(f"INCOMING SURVIVAL TRANSPORT — +{count} COLONISTS")
        else:
            self._log("TRANSPORT DIVERTED — INSUFFICIENT RESOURCES")

    def _log(self, msg: str):
        self.events.append(msg)
        if len(self.events) > 20:
            self.events.pop(0)
        print(f"[Population] {msg}")
