"""
Factory system — recipe queue, blueprint inventory, crafting timer.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from systems.resources import ResourceSystem, Resource


# ── Рецепти ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Recipe:
    id:          str
    label:       str
    description: str
    inputs:      tuple[tuple[Resource, float], ...]
    output_item: str          # що додається в BlueprintInventory
    output_count: int = 1
    craft_time:  float = 20.0
    category:    str  = "blueprint"   # blueprint | component | endgame


RECIPES: dict[str, Recipe] = {r.id: r for r in [

    # ── Basic blueprints (стартові) ──────────────────────────────────────
    Recipe(
        id="bp_solar", label="Solar Panel Blueprint",
        description="Enables solar panel construction.",
        inputs=((Resource.IRON, 8),),
        output_item="bp_solar", craft_time=15.0, category="blueprint",
    ),
    Recipe(
        id="bp_greenhouse", label="Greenhouse Blueprint",
        description="Enables greenhouse construction.",
        inputs=((Resource.IRON, 10), (Resource.SILICON, 4)),
        output_item="bp_greenhouse", craft_time=20.0, category="blueprint",
    ),
    Recipe(
        id="bp_extractor", label="Extractor Blueprint",
        description="Enables extractor construction.",
        inputs=((Resource.IRON, 12),),
        output_item="bp_extractor", craft_time=18.0, category="blueprint",
    ),

    # ── Advanced blueprints ───────────────────────────────────────────────
    Recipe(
        id="bp_storage", label="Storage Blueprint",
        description="Enables storage construction.",
        inputs=((Resource.IRON, 15), (Resource.SILICON, 5)),
        output_item="bp_storage", craft_time=25.0, category="blueprint",
    ),
    Recipe(
        id="bp_laboratory", label="Laboratory Blueprint",
        description="Enables laboratory construction.",
        inputs=((Resource.IRON, 20), (Resource.SILICON, 15)),
        output_item="bp_laboratory", craft_time=35.0, category="blueprint",
    ),

    # ── Components ────────────────────────────────────────────────────────
    Recipe(
        id="metal_parts", label="Metal Parts",
        description="Refined iron parts for advanced construction.",
        inputs=((Resource.IRON, 20),),
        output_item="metal_parts", output_count=3,
        craft_time=12.0, category="component",
    ),
    Recipe(
        id="circuit_boards", label="Circuit Boards",
        description="Silicon+iron electronics.",
        inputs=((Resource.SILICON, 15), (Resource.IRON, 10)),
        output_item="circuit_boards", output_count=2,
        craft_time=18.0, category="component",
    ),

    # ── Endgame ───────────────────────────────────────────────────────────
    Recipe(
        id="bp_battery", label="Battery Blueprint",
        description="Enables battery array construction.",
        inputs=((Resource.IRON, 15), (Resource.SILICON, 10)),
        output_item="bp_battery", craft_time=20.0, category="blueprint",
    ),
    Recipe(
        id="bp_reactor", label="Reactor Blueprint",
        description="Enables nuclear reactor construction.",
        inputs=((Resource.IRON, 40), (Resource.SILICON, 25), (Resource.URANIUM, 5)),
        output_item="bp_reactor", craft_time=50.0, category="blueprint",
    ),
    Recipe(
        id="bp_battery", label="Battery Array Blueprint",
        description="Enables battery array construction.",
        inputs=((Resource.IRON, 15), (Resource.SILICON, 10)),
        output_item="bp_battery", craft_time=20.0, category="blueprint",
    ),
    Recipe(
        id="jammer_component", label="Jammer Component",
        description="Core component for the Signal Jammer.",
        inputs=((Resource.URANIUM, 5), (Resource.SILICON, 20), (Resource.IRON, 15)),
        output_item="jammer_component", craft_time=60.0, category="endgame",
    ),
]}

# Порядок для UI
RECIPE_ORDER = [
    "bp_solar", "bp_greenhouse", "bp_extractor",
    "bp_storage", "bp_laboratory", "bp_battery", "bp_reactor",
    "metal_parts", "circuit_boards",
    "jammer_component",
]

# Будівлі що вимагають blueprint
BUILDING_REQUIRES_BP: dict[str, str | None] = {
    "hub":        None,
    "habitat":    None,
    "greenhouse": "bp_greenhouse",
    "solar":      "bp_solar",
    "extractor":  "bp_extractor",
    "storage":    "bp_storage",
    "factory":    None,
    "laboratory": "bp_laboratory",
    "battery":    "bp_battery",
    "reactor":    "bp_reactor",
    "jammer":     "jammer_component",
}


# ── Blueprint Inventory ───────────────────────────────────────────────────────

class BlueprintInventory:
    """Зберігає blueprints і components що були виготовлені."""

    def __init__(self):
        self._items: dict[str, int] = {}
        # Стартові blueprints
        for item in ("bp_solar", "bp_extractor"):
            self._items[item] = 2

    def add(self, item: str, count: int = 1):
        self._items[item] = self._items.get(item, 0) + count

    def has(self, item: str, count: int = 1) -> bool:
        return self._items.get(item, 0) >= count

    def consume(self, item: str, count: int = 1) -> bool:
        if not self.has(item, count):
            return False
        self._items[item] -= count
        return True

    def count(self, item: str) -> int:
        return self._items.get(item, 0)

    def can_build(self, building_type_value: str) -> bool:
        required = BUILDING_REQUIRES_BP.get(building_type_value)
        if required is None:
            return True
        return self.has(required)

    def consume_for_build(self, building_type_value: str) -> bool:
        required = BUILDING_REQUIRES_BP.get(building_type_value)
        if required is None:
            return True
        return self.consume(required)


# ── Factory Manager ───────────────────────────────────────────────────────────

@dataclass
class FactoryManager:
    """Керує чергою крафту для всіх фабрик."""

    _queue:       list[str]  = field(default_factory=list)   # recipe ids
    _timer:       float      = 0.0
    _busy:        bool       = False
    _current:     str | None = None
    finished:     list[str]  = field(default_factory=list)   # щойно виготовлені

    @property
    def is_busy(self) -> bool:
        return self._busy

    @property
    def current_recipe(self) -> Recipe | None:
        return RECIPES.get(self._current) if self._current else None

    @property
    def queue(self) -> list[str]:
        return list(self._queue)

    @property
    def progress(self) -> float:
        """0.0 - 1.0"""
        if not self._busy or not self._current:
            return 0.0
        total = RECIPES[self._current].craft_time
        return max(0.0, 1.0 - self._timer / total) if total > 0 else 1.0

    @property
    def time_left(self) -> float:
        return self._timer if self._busy else 0.0

    def can_craft(self, recipe_id: str, resources: ResourceSystem) -> bool:
        recipe = RECIPES.get(recipe_id)
        if not recipe:
            return False
        return all(resources.amount(r) >= amt for r, amt in recipe.inputs)

    def enqueue(self, recipe_id: str, resources: ResourceSystem) -> bool:
        """Додає рецепт у чергу якщо є ресурси. Знімає ресурси одразу."""
        recipe = RECIPES.get(recipe_id)
        if not recipe:
            return False
        costs = {r: amt for r, amt in recipe.inputs}
        if not resources.consume_many(costs):
            return False
        self._queue.append(recipe_id)
        if not self._busy:
            self._start_next()
        return True

    def remove_from_queue(self, index: int):
        """Видаляє елемент з черги (ресурси НЕ повертаються — вже списані)."""
        if 0 <= index < len(self._queue):
            self._queue.pop(index)

    def tick(self, blueprint_inv: BlueprintInventory, dt: float,
             has_power: bool = True, has_workers: bool = True):
        self.finished.clear()
        if not self._busy or not self._current:
            return
        if not has_power or not has_workers:
            return   # пауза без втрати прогресу

        self._timer -= dt
        if self._timer <= 0:
            recipe = RECIPES[self._current]
            blueprint_inv.add(recipe.output_item, recipe.output_count)
            self.finished.append(self._current)
            self._current = None
            self._busy    = False
            self._start_next()

    def _start_next(self):
        if self._queue:
            self._current = self._queue.pop(0)
            self._timer   = RECIPES[self._current].craft_time
            self._busy    = True
