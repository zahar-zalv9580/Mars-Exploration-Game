"""
Lore system: logs, signal fragments, laboratory analysis queue.

Log types:
  STORY  — автоматично по днях
  RESEARCH — через лабораторію (energy + workers + time)
  SIGNAL — знайдені ровером, аналізуються в лабораторії

Fragment rarity: COMMON / RARE / EPIC / FORBIDDEN
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from enum import Enum, auto


class LogType(Enum):
    STORY    = auto()
    RESEARCH = auto()
    SIGNAL   = auto()


class LogCategory(Enum):
    SYSTEM   = "SYSTEM"
    SIGNAL   = "SIGNALS"
    RARK     = "R-ARK"
    OBSERVER = "OBSERVER"
    CORRUPT  = "CORRUPTION"


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


# ── Всі логи гри ─────────────────────────────────────────────────────────────

ALL_LOGS: list[LogEntry] = [

    # STORY LOGS — автоматично
    LogEntry(
        id="s01", title="Colony Uplink Established",
        date="DAY 01 / 2091", category=LogCategory.SYSTEM,
        log_type=LogType.STORY, unlock_day=1,
        text=[
            "Mars Colony Alpha — uplink confirmed.",
            "Earth communication: LOST.",
            "<< last signal received 14 hours ago >>",
            "R-ARK-NET: operating normally.",
            "Begin resource extraction protocol.",
        ]
    ),
    LogEntry(
        id="s02", title="Atmospheric Warning",
        date="DAY 05 / 2091", category=LogCategory.SYSTEM,
        log_type=LogType.STORY, unlock_day=5,
        text=[
            "Dust storm frequency: ELEVATED.",
            "Solar efficiency reduced by 40% during events.",
            "R-ARK-NET recommends reactor construction.",
            "<< static >>",
        ]
    ),
    LogEntry(
        id="s03", title="R-ARK Signal Anomaly",
        date="DAY 10 / 2091", category=LogCategory.RARK,
        log_type=LogType.STORY, unlock_day=10, critical=True,
        text=[
            "R-ARK-NET: Unrecognized signal pattern detected.",
            "Source: unknown. Frequency: non-standard.",
            "Executive recommendation: IGNORE.",
            "Note: this recommendation is mandatory.",
        ]
    ),
    LogEntry(
        id="s04", title="Transmission Fragment",
        date="DAY 15 / 2091", category=LogCategory.SIGNAL,
        log_type=LogType.STORY, unlock_day=15, critical=True,
        text=[
            "...they are watching...",
            "<< transmission source: unidentified >>",
            "<< frequency: matches no known satellite >>",
            "R-ARK-NET: NO ANOMALY DETECTED.",
            "                    [this may be false]",
        ]
    ),
    LogEntry(
        id="s05", title="PCO Detection",
        date="DAY 25 / 2091", category=LogCategory.OBSERVER,
        log_type=LogType.STORY, unlock_day=25, critical=True,
        text=[
            "ALERT: Planetary Correction Object detected.",
            "Orbital trajectory: MARS.",
            "Estimated arrival: DAY 30.",
            "R-ARK-NET: CORRECTION SEQUENCE INITIATED.",
            "Activate Signal Jammer immediately.",
        ]
    ),

    # RESEARCH LOGS — лабораторія
    LogEntry(
        id="r01", title="Red Arkorp — Internal Memo",
        date="12.03.2089", category=LogCategory.RARK,
        log_type=LogType.RESEARCH, critical=True,
        text=[
            "INTERNAL PRIORITY DIRECTIVE:",
            "Mars Continuity > Earth Stability.",
            "R-ARK-NET deployment: proceed regardless.",
            "Earth governments: not informed.",
            "<< document classification: FORBIDDEN >>",
        ]
    ),
    LogEntry(
        id="r02", title="R-ARK-NET Architecture",
        date="08.11.2088", category=LogCategory.RARK,
        log_type=LogType.RESEARCH,
        text=[
            "R-ARK-NET: planetary coordination system.",
            "Designed to: optimize resource extraction.",
            "Side effect: signal amplification across",
            "non-standard frequencies.",
            "Risk assessment: CLASSIFIED.",
        ]
    ),
    LogEntry(
        id="r03", title="Observer Taxonomy",
        date="unknown", category=LogCategory.OBSERVER,
        log_type=LogType.RESEARCH, critical=True,
        text=[
            "Entities classification: OBSERVERS.",
            "Purpose: correction of civilizations",
            "producing anomalous signal patterns.",
            "Method: Planetary Correction Object.",
            "Previous corrections: [DATA EXPUNGED]",
        ]
    ),
    LogEntry(
        id="r04", title="Earth Last Broadcast",
        date="DAY 00 / 2091", category=LogCategory.SYSTEM,
        log_type=LogType.RESEARCH, critical=True,
        text=[
            "This is Emergency Broadcast Alpha.",
            "R-ARK cascade failure confirmed.",
            "Observer response: initiated.",
            "All Mars colonies: you are on your own.",
            "Good luck.",
            "<< signal lost >>",
        ]
    ),
    LogEntry(
        id="r05", title="Jammer Specifications",
        date="09.07.2090", category=LogCategory.RARK,
        log_type=LogType.RESEARCH,
        text=[
            "Signal Jammer — prototype specs.",
            "Purpose: mask colony from Observer sensors.",
            "Power requirement: MASSIVE.",
            "Components: uranium core + silicon array.",
            "Success probability: unknown.",
        ]
    ),

    # SIGNAL LOGS — знайдені ровером
    LogEntry(
        id="f01", title="Crashed Probe — Civilian",
        date="recovered", category=LogCategory.SIGNAL,
        log_type=LogType.SIGNAL,
        text=[
            "Personal log — Dr. Vasquez.",
            "Earth evacuation: failed.",
            "Mars was supposed to save us.",
            "I wonder if anyone will read this.",
        ]
    ),
    LogEntry(
        id="f02", title="R-ARK Satellite Fragment",
        date="recovered", category=LogCategory.RARK,
        log_type=LogType.SIGNAL, critical=True,
        text=[
            "R-ARK-NET ERROR LOG #4471:",
            "Observer signature confirmed in sector 7.",
            "Suppression protocol: FAILED.",
            "Recommendation: evacuation.",
            "<< this log was marked for deletion >>",
        ]
    ),
    LogEntry(
        id="f03", title="Observer Signal Fragment",
        date="recovered", category=LogCategory.OBSERVER,
        log_type=LogType.SIGNAL, critical=True,
        text=[
            "<< non-human origin >>",
            "ANOMALOUS CIVILIZATION DETECTED.",
            "SIGNAL PATTERN: UNSTABLE.",
            "CORRECTION: SCHEDULED.",
            "<< end transmission >>",
        ]
    ),
    LogEntry(
        id="f04", title="Corrupted Drive — Unknown",
        date="recovered", category=LogCategory.CORRUPT,
        log_type=LogType.SIGNAL, corrupted=True,
        text=[
            "ΞARTH STATUS: CØRRΞCTΞD.",
            "R-ARK PR0T0C0L: [███████]",
            "...they meant well...",
            "...we all did...",
            "<< data unrecoverable >>",
        ]
    ),
    LogEntry(
        id="f05", title="Black Box — Cargo Ship",
        date="recovered", category=LogCategory.SYSTEM,
        log_type=LogType.SIGNAL,
        text=[
            "Final entry — Cargo Ship Prometheus.",
            "We were carrying Jammer components.",
            "Storm took us down on approach.",
            "Components are somewhere out there.",
            "Hope someone finds this.",
        ]
    ),
]

LOG_BY_ID: dict[str, LogEntry] = {l.id: l for l in ALL_LOGS}
CRITICAL_LOG_IDS = {l.id for l in ALL_LOGS if l.critical}


# ── Signal Fragment ───────────────────────────────────────────────────────────

@dataclass
class SignalFragment:
    """Фізичний об'єкт на карті що ровер може підібрати."""
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
        return f"{self.rarity.value.upper()} FRAGMENT"


def roll_fragment_rarity(rng: random.Random) -> FragmentRarity:
    r = rng.random()
    cumulative = 0.0
    for rarity, chance in FRAGMENT_RARITY_CHANCES:
        cumulative += chance
        if r < cumulative:
            return rarity
    return FragmentRarity.COMMON


# ── Laboratory Manager ────────────────────────────────────────────────────────

@dataclass
class LaboratoryManager:
    """Керує аналізом логів і відкриттям лору."""

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

    # ---------------------------------------------------------------- query

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

    # ---------------------------------------------------------------- story unlock

    def check_day_unlocks(self, day: int):
        """Автоматично відкриває STORY логи по дню."""
        for log in ALL_LOGS:
            if (log.log_type == LogType.STORY
                    and log.unlock_day <= day
                    and log.id not in self._discovered):
                self._discover(log.id)

    # ---------------------------------------------------------------- research queue

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
        """Аналізує signal fragment з інвентарю."""
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

    # ---------------------------------------------------------------- tick

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

    # ---------------------------------------------------------------- secret ending

    def secret_ending_unlocked(self) -> bool:
        return self.critical_found >= self.critical_total
