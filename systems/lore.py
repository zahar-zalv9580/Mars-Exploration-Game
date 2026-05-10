# Система лору і логів. Відповідає за зберігання інформації про всі логи, їх відкриття, а також за механіку дослідження і відкриття нових логів через лабораторію.
from __future__ import annotations
import random
from dataclasses import dataclass, field
from enum import Enum, auto


class LogType(Enum):
    STORY    = auto()
    RESEARCH = auto()
    SIGNAL   = auto()


class LogCategory(Enum):
    SYSTEM   = "СИСТЕМА"
    SIGNAL   = "СИГНАЛИ"
    RARK     = "R-ARK"
    OBSERVER = "СПОСТЕРІГАЧІ"
    CORRUPT  = "C0RRUPT"


class FragmentRarity(Enum):
    COMMON    = "common"
    RARE      = "rare"
    EPIC      = "epic"
    FORBIDDEN = "forbidden"


FRAGMENT_RARITY_CHANCES = [
    (FragmentRarity.COMMON,    0.60),
    (FragmentRarity.RARE,      0.25),
    (FragmentRarity.EPIC,      0.10),
    (FragmentRarity.FORBIDDEN, 0.05),
]

FRAGMENT_RARITY_COLOR = {
    FragmentRarity.COMMON:    (160, 160, 160),
    FragmentRarity.RARE:      (80,  160, 220),
    FragmentRarity.EPIC:      (180, 80,  220),
    FragmentRarity.FORBIDDEN: (220, 60,  40),
}

CATEGORY_COLOR = {
    LogCategory.SYSTEM:   (100, 180, 220),
    LogCategory.SIGNAL:   (140, 200, 140),
    LogCategory.RARK:     (220, 60,  40),
    LogCategory.OBSERVER: (180, 80,  220),
    LogCategory.CORRUPT:  (200, 140, 60),
}


@dataclass
class LogEntry:
    id:          str
    title:       str
    date:        str
    category:    LogCategory
    log_type:    LogType
    text:        list[str]     # рядки тексту
    unlock_day:  int = 0       # для STORY логів
    critical:    bool = False  # для secret ending
    corrupted:   bool = False  # glitch текст на пізніх днях
    discovered:  bool = False


#Всі логи гри

ALL_LOGS: list[LogEntry] = [

    # STORY LOGS — автоматично
    LogEntry(
        id="s01", title="Колонія на зв'язку",
        date="DAY 01 / 2091", category=LogCategory.SYSTEM,
        log_type=LogType.STORY, unlock_day=1,
        text=[
            "КОЛОНІЯ НА МАРСІ АЛЬФА.",
            "ЗВ'ЯЗОК З ЗЕМЛЕЮ: LOST.",
            "<< останній сигнал отримано: 14 годин тому >>",
            "R-ARK-NET: працює успішно.",
            "Почати протокол видобування.",
        ]
    ),
    LogEntry(
        id="s02", title="Атмосферні збурення",
        date="DAY 05 / 2091", category=LogCategory.SYSTEM,
        log_type=LogType.STORY, unlock_day=5,
        text=[
            "Частота пилових бурь: ВИСОКА.",
            "Ефективність сонячних панелей зменшена на 40% під час подій.",
            "R-ARK-NET рекомендує будівництво реактора.",
            "<< білий шум >>",
        ]
    ),
    LogEntry(
        id="s03", title="АНОМАЛІЯ СИГНАЛУ R-ARK",
        date="DAY 10 / 2091", category=LogCategory.RARK,
        log_type=LogType.STORY, unlock_day=10, critical=True,
        text=[
            "R-ARK-NET: Невідомий патерн сигналу.",
            "Джерело: unknown. Частота: не стандартна.",
            "Рекомендація: ІГНОРУВАТИ.",
            "P.S.: ця рекомендація ОБОВ'ЯЗКОВА.",
        ]
    ),
    LogEntry(
        id="s04", title="Фрагмент Трансмітії",
        date="DAY 15 / 2091", category=LogCategory.SIGNAL,
        log_type=LogType.STORY, unlock_day=15, critical=True,
        text=[
            "...вони нас бачать...",
            "<< джерело сигналу: unidentified >>",
            "<< частота: matches no known satellite >>",
            "R-ARK-NET: БЕЗ АНОМАЛІЙ.",
            "                    [це точно не брехня =>...]",
        ]
    ),
    LogEntry(
        id="s05", title="Виявлення PCO",
        date="DAY 25 / 2091", category=LogCategory.OBSERVER,
        log_type=LogType.STORY, unlock_day=25, critical=True,
        text=[
            "ALERT: Planetary Correction Object помічено.",
            "Траекторія: MARS.",
            "Приблизне прибуття: ДЕНЬ 30.",
            "R-ARK-NET: ой.",
            "АКТИВУВАТИ ГЛУШИЛКУ. ПРЯМО ЗАРАЗ!",
        ]
    ),

    # RESEARCH LOGS — лабораторія
    LogEntry(
        id="r01", title="Red Arkorp — Internal Memo",
        date="12.03.2089", category=LogCategory.RARK,
        log_type=LogType.RESEARCH, critical=True,
        text=[
            "ПРІОРІТЕТ ██████████:",
            "Mars колонія > Earth стабільність.",
            "R-ARK-NET: розпочати проедуру.",
            "Влада: не інформовано.",
            "<< класифікація: FORBIDDEN >>",
        ]
    ),
    LogEntry(
        id="r02", title="R-ARK-NET архітектура",
        date="08.11.2088", category=LogCategory.RARK,
        log_type=LogType.RESEARCH,
        text=[
            "R-ARK-NET: ПЛАНЕТАРНА СИСТЕМА КООРДИНАЦІЇ.",
            "Зроблена для: оптимізації видобування ресурсів.",
            "Побічний ефект: збиття зв'язків",
            "не стандартні частоти.",
            "РИЗИК: #########.",
        ]
    ),
    LogEntry(
        id="r03", title="Таксонія Спостерігачів",
        date="unknown", category=LogCategory.OBSERVER,
        log_type=LogType.RESEARCH, critical=True,
        text=[
            "Класифікація істот: СПОСТЕРІГАЧІ.",
            "Ціль: моніторинг цивілізацій та корекція патернів поведінки.",
            "Мирні, якщо не провокувати (цього ж не буде, вірно?).",
            "МЕТОД: Planetary Correction Object.",            
        ]
    ),
    LogEntry(
        id="r04", title="ОСТАННІЙ СИГНАЛ ІЗ ЗЕМЛІ",
        date="DAY 00 / 2091", category=LogCategory.SYSTEM,
        log_type=LogType.RESEARCH, critical=True,
        text=[
            "Це Система Екстреного Сповіщення Alpha.",
            "R-ARK каскад став успішно неспраний.",         #що я пишу...
            "Спостерігачі: стартують корекцію Землі.",
            "Усім жителям Землі: вибачте. Ми зробили все, що могли.",
            "Коли ви отримаєте цей сигнал, то нас вже не буде.",
            "Всім колоніям Марсу: тепер ви самі.",
            "Успіхів.",
            "<< втрата сигналу >>",
        ]
    ),
    LogEntry(
        id="r05", title="Специфікації глушилки сигналів",
        date="09.07.2090", category=LogCategory.RARK,
        log_type=LogType.RESEARCH,
        text=[
            "Глушилка сигналів — характеристика.",
            "Ціль: заховати колонію від Спостерігачів.",
            "Кількість енергії: ВЕЛИЧЕЗНА.",
            "Компоненти: уран + силікон.",
            "Успіх: unknown.",
        ]
    ),

    # SIGNAL LOGS — знайдені ровером
    LogEntry(
        id="f01", title="Розбитий бортовий журнал",
        date="recovered", category=LogCategory.SIGNAL,
        log_type=LogType.SIGNAL,
        text=[
            "Щоденник — Dr. Vasquez.",
            "Евакуація із Землі: failed.",
            "Марс мав нас врятувати...",
            "Цікаво, чи прочитає це хтось?",
        ]
    ),
    LogEntry(
        id="f02", title="R-ARK супутник, фрашмент",
        date="recovered", category=LogCategory.RARK,
        log_type=LogType.SIGNAL, critical=True,
        text=[
            "R-ARK-NET ПОМИЛКОВИЙ LOG #4471:",
            "Спостерігачі знайдено в секторі 7.",
            "Протокол зупинки: FAILED.",
            "Рекомендація: евакуація.",
            "<< цей log був переміщений в смітник >>",
            "<< Елементи тут можна відновити, видалення через 30 днів >>",    #пародія на реальні повідомлення про видалення даних з серверів, які я бачив в інтернетах
        ]
    ),
    LogEntry(
        id="f03", title="Фрагмент сигналу Спостерігачів",
        date="recovered", category=LogCategory.OBSERVER,
        log_type=LogType.SIGNAL, critical=True,
        text=[
            "<< не людський сигнал >>",
            "АНОМАЛЬ ЗНАЙДЕНА.",
            "ПАТЕРН СИГНАЛУ: UNSTABLE.",
            "КОРЕКЦІЯ: SCHEDULED.",
            "<< кінець сигналу >>",
        ]
    ),
    LogEntry(
        id="f04", title="Коруптований фрагмент флешки",
        date="recovered", category=LogCategory.CORRUPT,
        log_type=LogType.SIGNAL, corrupted=True,
        text=[
            "ΞARTH STATUS: CØRRΞCTΞD.",
            "R-ARK PR0T0C0L: [███████]",
            "...вони хотіли добро...",
            "...ми всі хотіли...",
            "<< ██████████ >>",
        ]
    ),
    LogEntry(
        id="f05", title="Чорна скринька з розбитого корабля",
        date="recovered", category=LogCategory.SYSTEM,
        log_type=LogType.SIGNAL,
        text=[
            "Фінальний запис.",
            "Ми маємо фрагменти Jammer.",
            "Шторм.",
            "Компоненти розкидані.",
            "Сподіваюся, їх хтось знайде. Координати: ██, ██.",
        ]
    ),
]

LOG_BY_ID: dict[str, LogEntry] = {l.id: l for l in ALL_LOGS}
CRITICAL_LOG_IDS = {l.id for l in ALL_LOGS if l.critical}


#Фрагменти сигналу що ровер може збирати на карті. Вони відкривають SIGNAL логи в лабораторії.

@dataclass
class SignalFragment:
    tx:     int
    ty:     int
    rarity: FragmentRarity
    # Який лог він відкриє (тільки SIGNAL type)
    log_id: str | None = None

    @property
    def color(self) -> tuple:
        return FRAGMENT_RARITY_COLOR[self.rarity]

    @property
    def label(self) -> str:
        return f"{self.rarity.value.upper()} ФРАГМЕНТ"


def roll_fragment_rarity(rng: random.Random) -> FragmentRarity:
    r = rng.random()
    cumulative = 0.0
    for rarity, chance in FRAGMENT_RARITY_CHANCES:
        cumulative += chance
        if r < cumulative:
            return rarity
    return FragmentRarity.COMMON


# Менеджер лабораторії, що керує аналізом логів і відкриттям лору.

@dataclass
class LaboratoryManager:
    _discovered: set[str] = field(default_factory=set)
    _queue:      list[str] = field(default_factory=list)   # log ids
    _timer:      float = 0.0
    _busy:       bool  = False
    _current:    str | None = None

    # Signal fragments в інвентарі (rarity -> count)
    fragments:   dict[str, int] = field(default_factory=dict)

    new_discoveries: list[str] = field(default_factory=list)  # для HUD

    # Час аналізу по типу логу
    ANALYSIS_TIME = {
        LogType.RESEARCH: 45.0,
        LogType.SIGNAL:   30.0,
    }

    def __post_init__(self):
        for r in FragmentRarity:
            self.fragments[r.value] = 0


    @property
    def discovered_count(self) -> int:
        return len(self._discovered)

    @property
    def total_logs(self) -> int:
        return len(ALL_LOGS)

    @property
    def critical_found(self) -> int:
        return len(self._discovered & CRITICAL_LOG_IDS)

    @property
    def critical_total(self) -> int:
        return len(CRITICAL_LOG_IDS)

    def is_discovered(self, log_id: str) -> bool:
        return log_id in self._discovered

    def discovered_logs(self) -> list[LogEntry]:
        return [LOG_BY_ID[i] for i in self._discovered if i in LOG_BY_ID]

    @property
    def is_busy(self) -> bool:
        return self._busy

    @property
    def progress(self) -> float:
        if not self._busy or not self._current:
            return 0.0
        log = LOG_BY_ID.get(self._current)
        if not log:
            return 0.0
        total = self.ANALYSIS_TIME.get(log.log_type, 30.0)
        return max(0.0, 1.0 - self._timer / total)

    @property
    def time_left(self) -> float:
        return self._timer

    @property
    def current_log(self) -> LogEntry | None:
        return LOG_BY_ID.get(self._current) if self._current else None

    # Відкриття історії

    def check_day_unlocks(self, day: int):
        for log in ALL_LOGS:
            if (log.log_type == LogType.STORY
                    and log.unlock_day <= day
                    and log.id not in self._discovered):
                self._discover(log.id)

    # Аналіз логів в лабораторії

    def can_analyze(self, log_id: str, has_lab: bool,
                    has_fragment: bool = False) -> bool:
        log = LOG_BY_ID.get(log_id)
        if not log or log.id in self._discovered:
            return False
        if log.log_type == LogType.STORY:
            return False
        if not has_lab:
            return False
        if log.log_type == LogType.SIGNAL:
            return has_fragment
        return True

    def enqueue_research(self, log_id: str) -> bool:
        log = LOG_BY_ID.get(log_id)
        if not log or log.id in self._discovered:
            return False
        if log_id in self._queue or self._current == log_id:
            return False
        self._queue.append(log_id)
        if not self._busy:
            self._start_next()
        return True

    def enqueue_signal(self, rarity: FragmentRarity) -> bool:
        if self.fragments.get(rarity.value, 0) <= 0:
            return False
        # Знаходимо невідкритий SIGNAL лог для цієї рідкості
        candidates = [
            l for l in ALL_LOGS
            if l.log_type == LogType.SIGNAL
            and l.id not in self._discovered
            and l.id not in self._queue
        ]
        if not candidates:
            return False
        # Рідкісні фрагменти дають критичні логи
        if rarity in (FragmentRarity.EPIC, FragmentRarity.FORBIDDEN):
            critical = [l for l in candidates if l.critical]
            if critical:
                candidates = critical
        log = candidates[0]
        self.fragments[rarity.value] -= 1
        self._queue.append(log.id)
        if not self._busy:
            self._start_next()
        return True

    def add_fragment(self, rarity: FragmentRarity):
        self.fragments[rarity.value] = self.fragments.get(rarity.value, 0) + 1

    #Тік

    def tick(self, dt: float, has_lab: bool, has_power: bool):
        self.new_discoveries.clear()
        if not self._busy or not has_lab or not has_power:
            return
        self._timer -= dt
        if self._timer <= 0:
            if self._current:
                self._discover(self._current)
                self._current = None
                self._busy = False
            self._start_next()

    def _start_next(self):
        if self._queue:
            self._current = self._queue.pop(0)
            log = LOG_BY_ID.get(self._current)
            if log:
                self._timer = self.ANALYSIS_TIME.get(log.log_type, 30.0)
                self._busy = True

    def _discover(self, log_id: str):
        self._discovered.add(log_id)
        log = LOG_BY_ID.get(log_id)
        if log:
            self.new_discoveries.append(log_id)

    #Секретний фінал

    def secret_ending_unlocked(self) -> bool:
        return self.critical_found >= self.critical_total
