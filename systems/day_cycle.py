"""
Day/Night cycle + game phase system.
1 day = 120 real seconds.
30 days total.
"""
from __future__ import annotations
from dataclasses import dataclass, field

DAY_DURATION = 120.0   # секунд

# Фази гри
PHASES = [
    (1,  5,  "EARLY",    "Establish base"),
    (6,  10, "EARLY+",   "Expand & survive"),
    (11, 20, "MID",      "Optimize colony"),
    (21, 24, "LATE",     "Prepare for threat"),
    (25, 29, "CRITICAL", "Observers incoming"),
    (30, 30, "FINAL",    "Last stand"),
]

# Події що відбуваються на початку конкретного дня
DAY_EVENTS: dict[int, list[str]] = {
    1:  ["// Зв'язок з колонією встановлено. Сигнал з Землі втрачено. //"],
    5:  ["// ПОПЕРЕДЖЕННЯ: Виявлено атмосферні збурення. //",
         "// R-ARK-NET: Система номінальна. //"],
    10: ["// R-ARK-NET: Виявлено аномальний паттерн сигналу. //",
         "// Журнал колонії: Дивна інтерференція на каналах зв'язку. //"],
    15: ["// R-ARK-NET: ПОМИЛКА — Невпізнаний підпис сутності. //"],
    20: ["// ПЕРЕДАЧА: '...вони спостерігають...' — джерело невідоме //",
         "// Посилання на спостерігачів виявлено в архівах R-ARK. //"],
    25: ["// ТРИВОГА: `Об'єкт планетарної корекції` виявлено на орбіті Марса. //",
         "// R-ARK-NET: КРИТИЧНО — Послідовність корекції ініційовано. //",
         "// У вас є 5 днів. Активуйте глушилку сигналів. //"],
    28: ["// Відстань ПКО: КРИТИЧНА. Глушилка сигналів потрібна НЕГАЙНО. //"],
    30: ["// День 30. Остаточний результат визначено. //"],
}

# Множник частоти подій по фазах (використовується CrisisSystem)
PHASE_EVENT_RATE: dict[str, float] = {
    "РАНО":    0.1,
    "РАНО+":   0.3,
    "СЕРЕДИНА":      0.5,
    "ПІЗНІЙ":     0.8,
    "КРИТИЧНО": 1.2,
    "ФІНАЛ":    1.5,
}


@dataclass
class DayCycle:
    day:          int   = 1
    time_in_day:  float = 0.0    # 0..DAY_DURATION
    _total_days:  int   = 30

    # Нові повідомлення що з'явились (читає game.py, потім очищає)
    new_messages: list[str] = field(default_factory=list)

    def tick(self, dt: float) -> bool:
        """Оновлює час. Повертає True якщо почався новий день."""
        self.time_in_day += dt
        if self.time_in_day >= DAY_DURATION:
            self.time_in_day -= DAY_DURATION
            self.day = min(self.day + 1, self._total_days)
            self._on_new_day()
            return True
        return False

    def _on_new_day(self):
        msgs = DAY_EVENTS.get(self.day, [])
        self.new_messages.extend(msgs)

    @property
    def progress(self) -> float:
        """Прогрес поточного дня 0.0-1.0."""
        return self.time_in_day / DAY_DURATION

    @property
    def phase(self) -> str:
        for start, end, name, _ in PHASES:
            if start <= self.day <= end:
                return name
        return "FINAL"

    @property
    def phase_label(self) -> str:
        for start, end, name, label in PHASES:
            if start <= self.day <= end:
                return label
        return ""

    @property
    def event_rate(self) -> float:
        return PHASE_EVENT_RATE.get(self.phase, 0.5)

    @property
    def is_critical(self) -> bool:
        return self.day >= 25

    @property
    def is_final(self) -> bool:
        return self.day >= 30

    @property
    def time_left_str(self) -> str:
        days_left = self._total_days - self.day
        return f"{days_left}d left"

    @property
    def time_in_day_str(self) -> str:
        secs = int(DAY_DURATION - self.time_in_day)
        m, s = divmod(secs, 60)
        return f"{m:02d}:{s:02d}"
