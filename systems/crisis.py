"""
Crisis & Weather system.
Events: Dust Storm, Cold Snap, Solar Flare, Radiation Wave, Signal Interference
Colony crises: Power Failure, Food Shortage, Water Failure
"""
from __future__ import annotations
import random
import math
from dataclasses import dataclass, field
from enum import Enum, auto


class EventType(Enum):
    # Погода
    DUST_STORM           = auto()
    COLD_SNAP            = auto()
    SOLAR_FLARE          = auto()
    RADIATION_WAVE       = auto()
    SIGNAL_INTERFERENCE  = auto()
    # Correction phase (день 25+)
    ORBITAL_SHADOW       = auto()
    OBSERVER_PING        = auto()


# Іконки для HUD (emoji-стиль текст)
EVENT_ICON: dict[EventType, str] = {
    EventType.DUST_STORM:          "🌪",
    EventType.COLD_SNAP:           "❄",
    EventType.SOLAR_FLARE:         "☀",
    EventType.RADIATION_WAVE:      "☢",
    EventType.SIGNAL_INTERFERENCE: "📡",
    EventType.ORBITAL_SHADOW:      "🌑",
    EventType.OBSERVER_PING:       "👁",
}

EVENT_LABEL: dict[EventType, str] = {
    EventType.DUST_STORM:          "DUST STORM",
    EventType.COLD_SNAP:           "COLD SNAP",
    EventType.SOLAR_FLARE:         "SOLAR FLARE",
    EventType.RADIATION_WAVE:      "RADIATION WAVE",
    EventType.SIGNAL_INTERFERENCE: "SIGNAL INTERFERENCE",
    EventType.ORBITAL_SHADOW:      "ORBITAL SHADOW",
    EventType.OBSERVER_PING:       "OBSERVER PING",
}

EVENT_COLOR: dict[EventType, tuple] = {
    EventType.DUST_STORM:          (200, 140, 60),
    EventType.COLD_SNAP:           (120, 180, 220),
    EventType.SOLAR_FLARE:         (255, 220, 50),
    EventType.RADIATION_WAVE:      (130, 220, 100),
    EventType.SIGNAL_INTERFERENCE: (180, 80,  220),
    EventType.ORBITAL_SHADOW:      (60,  60,  80),
    EventType.OBSERVER_PING:       (220, 60,  40),
}

# Тривалість (min, max) секунд
EVENT_DURATION: dict[EventType, tuple[float, float]] = {
    EventType.DUST_STORM:          (60.0, 120.0),
    EventType.COLD_SNAP:           (45.0, 90.0),
    EventType.SOLAR_FLARE:         (20.0, 40.0),
    EventType.RADIATION_WAVE:      (30.0, 60.0),
    EventType.SIGNAL_INTERFERENCE: (25.0, 50.0),
    EventType.ORBITAL_SHADOW:      (80.0, 160.0),
    EventType.OBSERVER_PING:       (15.0, 30.0),
}

# Пул подій по фазах
PHASE_EVENT_POOL: dict[str, list[EventType]] = {
    "EARLY":    [EventType.DUST_STORM],
    "EARLY+":   [EventType.DUST_STORM, EventType.COLD_SNAP],
    "MID":      [EventType.DUST_STORM, EventType.COLD_SNAP,
                 EventType.SOLAR_FLARE, EventType.RADIATION_WAVE],
    "LATE":     [EventType.DUST_STORM, EventType.COLD_SNAP,
                 EventType.SOLAR_FLARE, EventType.RADIATION_WAVE,
                 EventType.SIGNAL_INTERFERENCE],
    "CRITICAL": [EventType.DUST_STORM, EventType.RADIATION_WAVE,
                 EventType.SIGNAL_INTERFERENCE, EventType.ORBITAL_SHADOW,
                 EventType.OBSERVER_PING],
    "FINAL":    [EventType.DUST_STORM, EventType.RADIATION_WAVE,
                 EventType.SIGNAL_INTERFERENCE, EventType.ORBITAL_SHADOW,
                 EventType.OBSERVER_PING],
}

# Лор-повідомлення при старті події
EVENT_MESSAGES: dict[EventType, list[str]] = {
    EventType.DUST_STORM:
        ["// ПОПЕРЕДЖЕННЯ ПРО ПОГОДУ: Наближається пилова буря. Ефективність сонячних батарей критична. //",
         "// ПОПЕРЕДЖЕННЯ ПРО БУРЮ: Зменшіть роботу ровера. //"],
    EventType.COLD_SNAP:
        ["// ЗНИЖЕННЯ ТЕМПЕРАТУРИ: Споживання енергії збільшено. //"],
    EventType.SOLAR_FLARE:
        ["// ВИЯВЛЕНО СОНЯЧНИЙ СПАЛАХ: Очікуйте системні збої. //",
         "// R-ARK-NET: Електромагнітні перешкоди на всіх каналах. //"],
    EventType.RADIATION_WAVE:
        ["// ПІК РАДІАЦІЇ: Цілісність колонії під загрозою. //",
         "// ПОПЕРЕДЖЕННЯ: Здоров'я колоністів в небезпеці. //"],
    EventType.SIGNAL_INTERFERENCE:
        ["// R-ARK-NET: Виявлено корупцію сигналу. //",
         "// ПОПЕРЕДЖЕННЯ: ЗАГРОЗИ НЕ ВИЯВЛЕНО  [ц̵̭̓̑̐͘е̵͈̜̳̫̽̾̍ ̸̧͚̊̃̊н̷̙͇̱̹̄е̸̨̮̞͓͑̈͆ ̵̳̩̪̔̈́͛п̵͇͎̥́͂р̴͔̏а̷̺͊͜͠в̷͖̱̌д̷̹̘̎̚͘а̷̢̲̘̜̿̀] //"],
    EventType.ORBITAL_SHADOW:
        ["// ТІНЬ З ОРБІТИ ПКО: Вихід сонячної енергії сильно зменшено. //",
         "// Об'єкт ближчий, ніж очікувалося. //"],
    EventType.OBSERVER_PING:
        ["// ОТРИМАНО НЕВІДОМИЙ СИГНАЛ. //",
         "// Виявлено спостерігача, що перехопив сигнал колонії. Потрібен джаммер. //"],
}


@dataclass
class ActiveEvent:
    type:     EventType
    duration: float
    severity: float    # 0.5 - 1.0
    timer:    float = 0.0

    @property
    def progress(self) -> float:
        return self.timer / self.duration if self.duration > 0 else 1.0

    @property
    def is_done(self) -> bool:
        return self.timer >= self.duration

    @property
    def label(self) -> str:
        return EVENT_LABEL[self.type]

    @property
    def icon(self) -> str:
        return EVENT_ICON.get(self.type, "?")

    @property
    def color(self) -> tuple:
        return EVENT_COLOR.get(self.type, (200, 200, 200))


@dataclass
class Modifiers:
    """Активні модифікатори від подій."""
    solar_efficiency:  float = 1.0
    rover_speed:       float = 1.0
    habitat_energy:    float = 1.0   # множник споживання
    radiation_damage:  float = 0.0   # шкода за тік
    signal_glitch:     bool  = False
    screen_overlay:    tuple | None = None   # RGBA колір накладення
    overlay_alpha:     float = 0.0


class CrisisManager:
    """Керує погодними подіями і застосовує модифікатори."""

    def __init__(self):
        self._active:  list[ActiveEvent] = []
        self._cooldown: float = 30.0    # пауза між подіями
        self._rng = random.Random()
        self.new_messages: list[str] = []

    # ---------------------------------------------------------------- tick

    def tick(self, dt: float, phase: str, event_rate: float,
             population, resources) -> Modifiers:
        self.new_messages.clear()

        # Оновлюємо активні події
        for ev in self._active:
            ev.timer += dt
        self._active = [ev for ev in self._active if not ev.is_done]

        # Спроба запустити нову подію
        self._cooldown -= dt
        if self._cooldown <= 0 and not self._has_event(EventType.DUST_STORM):
            self._cooldown = self._rng.uniform(
                40.0 / max(event_rate, 0.1),
                90.0 / max(event_rate, 0.1)
            )
            pool = PHASE_EVENT_POOL.get(phase, [])
            if pool:
                et = self._rng.choice(pool)
                self._start_event(et)

        # Застосовуємо ефекти
        mods = self._compute_modifiers(dt, population, resources)
        return mods

    # ---------------------------------------------------------------- events

    def _start_event(self, et: EventType):
        dmin, dmax = EVENT_DURATION[et]
        duration = self._rng.uniform(dmin, dmax)
        severity = self._rng.uniform(0.5, 1.0)
        ev = ActiveEvent(type=et, duration=duration, severity=severity)
        self._active.append(ev)
        msgs = EVENT_MESSAGES.get(et, [])
        self.new_messages.extend(self._rng.sample(msgs, min(1, len(msgs))))

    def _has_event(self, et: EventType) -> bool:
        return any(ev.type == et for ev in self._active)

    def force_event(self, et: EventType):
        """Для тестування або скриптованих подій."""
        self._start_event(et)

    # ---------------------------------------------------------------- modifiers

    def _compute_modifiers(self, dt: float, population, resources) -> Modifiers:
        from systems.resources import Resource
        mods = Modifiers()

        for ev in self._active:
            s = ev.severity
            fade = math.sin(math.pi * ev.progress) if ev.progress < 1 else 0

            if ev.type == EventType.DUST_STORM:
                mods.solar_efficiency *= max(0.1, 1.0 - 0.8 * s)
                mods.rover_speed      *= max(0.3, 1.0 - 0.5 * s)
                intensity = int(80 * s * fade)
                mods.screen_overlay = (180, 120, 40)
                mods.overlay_alpha  = max(mods.overlay_alpha, intensity)

            elif ev.type == EventType.COLD_SNAP:
                mods.habitat_energy *= 1.0 + 0.5 * s
                mods.screen_overlay = (60, 100, 160)
                mods.overlay_alpha  = max(mods.overlay_alpha, int(30 * s))

            elif ev.type == EventType.SOLAR_FLARE:
                mods.solar_efficiency *= 1.3   # короткий буст потім glitch
                mods.signal_glitch = True
                mods.screen_overlay = (255, 220, 50)
                mods.overlay_alpha  = max(mods.overlay_alpha, int(25 * s * fade))

            elif ev.type == EventType.RADIATION_WAVE:
                mods.radiation_damage += 0.002 * s * dt
                if mods.radiation_damage > 0.05 and population.population > 0:
                    if self._rng.random() < 0.001 * s:
                        population.population = max(0, population.population - 1)
                        self.new_messages.append(
                            "// КОЛОНІСТИ ВТРАЧЕНІ — РАДІАЦІЯ //"
                        )
                mods.screen_overlay = (60, 180, 60)
                mods.overlay_alpha  = max(mods.overlay_alpha, int(20 * s))

            elif ev.type == EventType.SIGNAL_INTERFERENCE:
                mods.signal_glitch = True

            elif ev.type == EventType.ORBITAL_SHADOW:
                mods.solar_efficiency *= 0.15
                mods.screen_overlay = (20, 20, 40)
                mods.overlay_alpha  = max(mods.overlay_alpha, int(60 * s))

            elif ev.type == EventType.OBSERVER_PING:
                mods.signal_glitch = True
                mods.screen_overlay = (180, 40, 40)
                mods.overlay_alpha  = max(mods.overlay_alpha, int(15 * s * fade))

        return mods

    # ---------------------------------------------------------------- query

    @property
    def active_events(self) -> list[ActiveEvent]:
        return list(self._active)

    @property
    def has_dust_storm(self) -> bool:
        return self._has_event(EventType.DUST_STORM)

    @property
    def weather_icon(self) -> str:
        """Іконка для HUD — найважливіша активна подія."""
        priority = [
            EventType.OBSERVER_PING, EventType.ORBITAL_SHADOW,
            EventType.RADIATION_WAVE, EventType.DUST_STORM,
            EventType.SOLAR_FLARE, EventType.SIGNAL_INTERFERENCE,
            EventType.COLD_SNAP,
        ]
        for et in priority:
            if self._has_event(et):
                return EVENT_ICON.get(et, "?")
        return "☀"   # ясна погода
