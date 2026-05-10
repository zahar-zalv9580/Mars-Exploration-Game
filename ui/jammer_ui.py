from __future__ import annotations
import pygame
from ui import fonts
from entities.building import Building, BuildingType, BuildingState
from systems.resources import ResourceSystem, Resource
from systems.building_manager import BuildingManager


class JammerUI:
    REQUIRED_TIME = 90.0
    ENERGY_DRAIN_RATE = 10.0
    MIN_ENERGY_RATIO = 0.8
    CLOSE_KEYS = (pygame.K_ESCAPE, pygame.K_j)

    def __init__(self):
        self.visible = False
        self.progress = 0.0
        self.activating = False
        self._message = ""

    def toggle(self):
        self.visible = not self.visible
        if not self.visible:
            self.activating = False
            self.progress = 0.0
            self._message = ""

    def close(self):
        self.visible = False
        self.activating = False
        self.progress = 0.0
        self._message = ""

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in self.CLOSE_KEYS:
                self.close()
                return True
            if event.key == pygame.K_SPACE:
                self.activating = True
                self._message = "Activation started..."
                return True

        return self.visible

    def tick(
        self,
        dt: float,
        resources: ResourceSystem,
        crisis,
        building_manager: BuildingManager,
        jammer_building: Building | None = None,
    ) -> bool:
        if not self.visible:
            return False

        if jammer_building is None:
            self._message = "No active Jammer nearby."
            self.activating = False
            self.progress = 0.0
            return False

        if not self.activating:
            self._message = "Press [SPACE] to start Jammer activation."
            return False

        enough_energy = resources.ratio(Resource.ENERGY) >= self.MIN_ENERGY_RATIO
        has_workers = building_manager._workers_ok.get(
            (jammer_building.tx, jammer_building.ty), False
        )
        if not jammer_building.is_active or not enough_energy or not has_workers:
            self._message = "Activation interrupted. Requirements lost."
            self.activating = False
            self.progress = 0.0
            return False

        energy_drain = self.ENERGY_DRAIN_RATE * dt
        if not resources.consume(Resource.ENERGY, energy_drain):
            self._message = "Energy depleted. Activation failed."
            self.activating = False
            self.progress = 0.0
            return False

        self.progress += dt / self.REQUIRED_TIME
        self._message = "Activating Jammer..."
        if self.progress >= 1.0:
            self.progress = 1.0
            self.visible = False
            self.activating = False
            self._message = "Jammer activated."
            return True

        return False

    def render(self, screen: pygame.Surface):
        if not self.visible:
            return

        sw, sh = screen.get_size()
        w, h = 420, 200
        px = sw // 2 - w // 2
        py = sh // 2 - h // 2

        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((18, 12, 8, 220))
        pygame.draw.rect(panel, (180, 80, 30), pygame.Rect(0, 0, w, h), 2)
        screen.blit(panel, (px, py))

        title = fonts.get(18, bold=True).render("JAMMER ACTIVATION", True, (220, 180, 80))
        screen.blit(title, (px + 18, py + 16))

        desc = fonts.get(11).render(
            "KEEP ENERGY ABOVE 80% AND MAINTAIN CREW UNTIL COMPLETE.", True,
            (190, 190, 180)
        )
        screen.blit(desc, (px + 18, py + 48))

        msg = fonts.get(12).render(self._message, True, (200, 200, 200))
        screen.blit(msg, (px + 18, py + 80))

        # Progress bar
        bar_x = px + 18
        bar_y = py + 118
        bar_w = w - 36
        bar_h = 24
        pygame.draw.rect(screen, (40, 40, 40), pygame.Rect(bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(screen, (80, 220, 120),
                         pygame.Rect(bar_x, bar_y, int(bar_w * min(1.0, self.progress)), bar_h))
        pygame.draw.rect(screen, (180, 180, 180), pygame.Rect(bar_x, bar_y, bar_w, bar_h), 2)

        pct = fonts.get(13, bold=True).render(
            f"{int(self.progress * 100):d}%", True, (255, 255, 255)
        )
        screen.blit(pct, (px + w // 2 - pct.get_width() // 2, bar_y + bar_h // 2 - pct.get_height() // 2))

        hint = fonts.get(10).render(
            "[SPACE] START  |  [J/ESC] CANCEL", True, (140, 140, 140)
        )
        screen.blit(hint, (px + 18, py + h - 30))
