from dataclasses import dataclass, field
from enum import Enum, auto
from systems.resources import Resource


class BuildingType(Enum):
    HUB        = "hub"
    HABITAT    = "habitat"
    GREENHOUSE = "greenhouse"
    SOLAR      = "solar"
    EXTRACTOR  = "extractor"
    STORAGE    = "storage"
    FACTORY    = "factory"
    LABORATORY = "laboratory"
    JAMMER     = "jammer"
    BATTERY    = "battery"
    REACTOR    = "reactor"


class BuildingState(Enum):
    ACTIVE       = auto()   # нормальна робота
    INACTIVE     = auto()   # немає енергії або відключено
    NO_RESOURCE  = auto()   # не вистачає ресурсу
    DISCONNECTED = auto()   # не підключено до хабу
    DAMAGED      = auto()   # пошкоджено
    CONSTRUCTING = auto()   # будується, але ще не працює


# Кольори рамки для кожного стану (юху!)
STATE_BORDER_COLOR: dict[BuildingState, tuple[int,int,int]] = {
    BuildingState.ACTIVE:       (80,  220, 80),
    BuildingState.INACTIVE:     (80,  80,  80),
    BuildingState.NO_RESOURCE:  (220, 180, 30),
    BuildingState.DISCONNECTED: (60,  120, 220),
    BuildingState.DAMAGED:      (220, 60,  60),
    BuildingState.CONSTRUCTING: (160, 160, 60),
}


@dataclass
class BuildingDef:
    type:        BuildingType
    label:       str
    description: str
    cost:        dict[Resource, float]
    produces:    dict[Resource, float]
    consumes:    dict[Resource, float]
    max_hp:      float = 100.0
    is_hub:      bool  = False
    gives_storage: bool = False
    # Анімації: список назв ефектів які підтримує ця будівля
    # Значення: 'pulse', 'smoke', 'glow', 'blink'
    fx: list[str] = field(default_factory=list)


BUILDING_DEFS: dict[BuildingType, BuildingDef] = {

    BuildingType.HUB: BuildingDef(
        type=BuildingType.HUB,
        label="Головний Купол",
        description="Центр колонії. Знищення = поразка.",
        cost={Resource.IRON: 0},
        produces={},
        consumes={Resource.ENERGY: 2.0},
        max_hp=200.0,
        is_hub=True,
        fx=["pulse"],         # мигає купол
    ),
    BuildingType.HABITAT: BuildingDef(
        type=BuildingType.HABITAT,
        label="Модуль Проживання",
        description="Збільшує місткість населення.",
        cost={Resource.IRON: 30.0},
        produces={},
        consumes={Resource.ENERGY: 1.0, Resource.FOOD: 0.5},
        fx=["blink"],
    ),
    BuildingType.GREENHOUSE: BuildingDef(
        type=BuildingType.GREENHOUSE,
        label="Теплиця",
        description="Виробляє їжу з води та енергії.",
        cost={Resource.IRON: 25.0, Resource.WATER: 10.0},
        produces={Resource.FOOD: 2.0},
        consumes={Resource.ENERGY: 1.5, Resource.WATER: 0.5},
        fx=["glow"],
    ),
    BuildingType.SOLAR: BuildingDef(
        type=BuildingType.SOLAR,
        label="Сонячна Панель",
        description="Генерує енергію. Краще на висотах.",
        cost={Resource.IRON: 20.0, Resource.SILICON: 10.0},
        produces={},
        consumes={},
        fx=[],
    ),
    BuildingType.EXTRACTOR: BuildingDef(
        type=BuildingType.EXTRACTOR,
        label="Бур",
        description="Видобуває ресурси залежно від біома плитки.",
        cost={Resource.IRON: 40.0},
        produces={},
        consumes={Resource.ENERGY: 2.0},
        fx=["smoke"],
    ),
    BuildingType.STORAGE: BuildingDef(
        type=BuildingType.STORAGE,
        label="Склад",
        description="Збільшує місткість сховища ресурсів.",
        cost={Resource.IRON: 35.0},
        produces={},
        consumes={Resource.ENERGY: 0.5},
        gives_storage=True,
        fx=[],
    ),
    BuildingType.FACTORY: BuildingDef(
        type=BuildingType.FACTORY,
        label="Фабрика",
        description="Виготовляє креслення та компоненти.",
        cost={Resource.IRON: 50.0, Resource.SILICON: 15.0},
        produces={},
        consumes={Resource.ENERGY: 3.0},
        fx=["smoke"],
    ),
    BuildingType.LABORATORY: BuildingDef(
        type=BuildingType.LABORATORY,
        label="Лабораторія",
        description="Розблоковує лор (підказка - це важливо).",
        cost={Resource.IRON: 45.0, Resource.SILICON: 20.0},
        produces={},
        consumes={Resource.ENERGY: 2.0},
        fx=["blink"],
    ),
    BuildingType.BATTERY: BuildingDef(
        type=BuildingType.BATTERY,
        label="Батарея",
        description="Збільшує місткість сховища енергії на 100.",
        cost={Resource.IRON: 30.0, Resource.SILICON: 20.0},
        produces={},
        consumes={},
        fx=["blink"],
    ),
    BuildingType.REACTOR: BuildingDef(
        type=BuildingType.REACTOR,
        label="АЕС",
        description="Генерує масивну енергію. Потребує уран.",          #ох боже... ЗБАГАЧЕНИЙ УРАН!?!?!?
        cost={Resource.IRON: 80.0, Resource.SILICON: 40.0, Resource.URANIUM: 10.0},
        produces={Resource.ENERGY: 18.0},
        consumes={Resource.URANIUM: 0.05},
        max_hp=150.0,
        fx=["pulse", "glow"],
    ),
    BuildingType.JAMMER: BuildingDef(
        type=BuildingType.JAMMER,
        label="Глушилка",
        description="Ховає колонію від Спостерігачів. Фінальна мета.",
        cost={},
        produces={},
        consumes={Resource.ENERGY: 20.0},
        fx=["pulse", "glow"],
    ),

}

INVENTORY_ORDER: list[BuildingType] = [                     # порядок для UI
    BuildingType.HUB,
    BuildingType.HABITAT,
    BuildingType.GREENHOUSE,
    BuildingType.SOLAR,
    BuildingType.EXTRACTOR,
    BuildingType.STORAGE,
    BuildingType.FACTORY,
    BuildingType.LABORATORY,
    BuildingType.BATTERY,
    BuildingType.REACTOR,
    BuildingType.JAMMER,
]


@dataclass
class Building:
    type:  BuildingType
    tx:    int
    ty:    int
    state: BuildingState = BuildingState.ACTIVE
    hp:    float = field(init=False)
    _anim_time: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self):
        self.hp = BUILDING_DEFS[self.type].max_hp

    @property
    def definition(self) -> BuildingDef:
        return BUILDING_DEFS[self.type]

    @property
    def is_active(self) -> bool:
        return self.state == BuildingState.ACTIVE

    @property
    def label(self) -> str:
        return self.definition.label

    @property
    def border_color(self) -> tuple[int,int,int]:
        return STATE_BORDER_COLOR[self.state]

    def update_anim(self, dt: float):
        self._anim_time += dt
