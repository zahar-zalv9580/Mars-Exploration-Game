"""
Inventory system:
  - Bottom bar: показує тільки blueprints що є в BlueprintInventory (динамічно)
  - E key: розширений інвентар (всі items + компоненти)
"""
from __future__ import annotations
import pygame
from ui import fonts
from systems.factory import BlueprintInventory, RECIPES, BUILDING_REQUIRES_BP
from entities.building import BuildingType, BUILDING_DEFS, INVENTORY_ORDER

SLOT_SIZE    = 56
SLOT_PADDING = 6
MARGIN_BOT   = 16

# Всі можливі items в розширеному інвентарі
ALL_ITEMS = [
    # Blueprints
    "bp_solar", "bp_greenhouse", "bp_extractor",
    "bp_storage", "bp_laboratory",
    # Components
    "metal_parts", "circuit_boards", "jammer_component",
]

ITEM_LABELS = {
    "bp_solar":        "Solar BP",
    "bp_greenhouse":   "Greenhouse BP",
    "bp_extractor":    "Extractor BP",
    "bp_storage":      "Storage BP",
    "bp_laboratory":   "Laboratory BP",
    "metal_parts":     "Metal Parts",
    "circuit_boards":  "Circuit Boards",
    "jammer_component":"Jammer Comp.",
}

ITEM_COLORS = {
    "bp_solar":        (80,  160, 220),
    "bp_greenhouse":   (80,  200, 80),
    "bp_extractor":    (180, 120, 60),
    "bp_storage":      (160, 140, 100),
    "bp_laboratory":   (120, 180, 220),
    "metal_parts":     (180, 130, 90),
    "circuit_boards":  (140, 200, 140),
    "jammer_component":(180, 80,  220),
}

# Blueprint -> BuildingType (для вибору при кліку)
BP_TO_BUILDING: dict[str, BuildingType] = {
    "bp_solar":      BuildingType.SOLAR,
    "bp_greenhouse": BuildingType.GREENHOUSE,
    "bp_extractor":  BuildingType.EXTRACTOR,
    "bp_storage":    BuildingType.STORAGE,
    "bp_laboratory": BuildingType.LABORATORY,
}

# Будівлі без blueprint (завжди доступні в нижньому барі)
FREE_BUILDINGS = [
    BuildingType.HUB,
    BuildingType.HABITAT,
    BuildingType.FACTORY,
    BuildingType.JAMMER,
]


class Inventory:
    """Bottom bar + розширений інвентар (E)."""

    BG_COLOR      = (12, 6, 3, 210)
    BORDER_COLOR  = (100, 50, 15)
    SELECT_COLOR  = (220, 150, 40)
    HOTKEY_COLOR  = (160, 140, 110)
    LABEL_COLOR   = (210, 190, 160)
    DIM_COLOR     = (60, 40, 20, 180)

    def __init__(self):
        self._selected_bt: BuildingType | None = None
        self._icons: dict[BuildingType, pygame.Surface] = {}
        self._expanded = False   # E — розширений інвентар

    def load_icons(self, icons: dict[BuildingType, pygame.Surface]):
        self._icons = icons

    # ---------------------------------------------------------------- slots

    def _active_slots(self, bp_inv: BlueprintInventory) -> list[tuple]:
        """
        Повертає список (label, BuildingType | None, icon_key, hotkey_str, count)
        для нижнього бару — тільки доступні.
        """
        slots = []
        idx = 1

        # Будівлі без blueprint
        for bt in FREE_BUILDINGS:
            if bt == BuildingType.JAMMER and not bp_inv.has("jammer_component"):
                continue
            slots.append((bt.value, bt, bt, str(idx), 0))
            idx += 1

        # Blueprint будівлі — тільки якщо є хоч один
        for bp_id, bt in BP_TO_BUILDING.items():
            cnt = bp_inv.count(bp_id)
            if cnt > 0:
                slots.append((ITEM_LABELS[bp_id], bt, bt, str(idx), cnt))
                idx += 1

        return slots

    # ---------------------------------------------------------------- input

    def handle_key(self, key: int, bp_inv: BlueprintInventory) -> BuildingType | None:
        slots = self._active_slots(bp_inv)
        for i, k in enumerate([
            pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
            pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9,
        ]):
            if key == k and i < len(slots):
                return self._select(slots[i][1])
        if key == pygame.K_e:
            self._expanded = not self._expanded
        return None

    def handle_click(self, mx: int, my: int, sw: int, sh: int,
                     bp_inv: BlueprintInventory) -> BuildingType | None:
        slots = self._active_slots(bp_inv)
        if not slots:
            return None
        total_w = len(slots) * (SLOT_SIZE + SLOT_PADDING) - SLOT_PADDING
        px = (sw - total_w) // 2
        py = sh - SLOT_SIZE - MARGIN_BOT - 18
        for i, slot in enumerate(slots):
            rx = px + i * (SLOT_SIZE + SLOT_PADDING)
            if pygame.Rect(rx, py, SLOT_SIZE, SLOT_SIZE).collidepoint(mx, my):
                return self._select(slot[1])
        return None

    def deselect(self):
        self._selected_bt = None

    def close_expanded(self):
        self._expanded = False

    @property
    def selected_type(self) -> BuildingType | None:
        return self._selected_bt

    @property
    def expanded_open(self) -> bool:
        return self._expanded

    # ---------------------------------------------------------------- render

    def render(self, screen: pygame.Surface, bp_inv: BlueprintInventory):
        slots = self._active_slots(bp_inv)
        if slots:
            self._render_bottom_bar(screen, slots)
        if self._expanded:
            self._render_expanded(screen, bp_inv)

    def _render_bottom_bar(self, screen: pygame.Surface, slots: list):
        sw, sh = screen.get_size()
        slot_w  = SLOT_SIZE + SLOT_PADDING
        total_w = len(slots) * slot_w - SLOT_PADDING
        px = (sw - total_w) // 2
        py = sh - SLOT_SIZE - MARGIN_BOT - 18

        for i, (label, bt, icon_key, hotkey, count) in enumerate(slots):
            rx = px + i * slot_w
            selected = (bt == self._selected_bt)
            self._render_slot(screen, label, bt, icon_key, hotkey,
                              count, rx, py, selected)

    def _render_slot(self, screen, label, bt, icon_key, hotkey,
                     count, x, y, selected):
        # Фон
        bg = pygame.Surface((SLOT_SIZE, SLOT_SIZE), pygame.SRCALPHA)
        bg.fill(self.BG_COLOR)
        screen.blit(bg, (x, y))

        # Іконка
        icon = self._icons.get(icon_key)
        if icon:
            screen.blit(icon, (x, y))

        # Рамка
        border = self.SELECT_COLOR if selected else self.BORDER_COLOR
        width  = 2 if selected else 1
        pygame.draw.rect(screen, border,
                         pygame.Rect(x, y, SLOT_SIZE, SLOT_SIZE), width)

        # Хоткей
        hk = fonts.get(9, bold=True).render(hotkey, True, self.HOTKEY_COLOR)
        screen.blit(hk, (x + 3, y + 3))

        # Кількість blueprints (якщо є)
        if count > 0:
            cnt = fonts.get(10, bold=True).render(f"x{count}", True, (160, 220, 160))
            screen.blit(cnt, (x + SLOT_SIZE - cnt.get_width() - 3, y + 3))

        # Назва під слотом
        lbl = fonts.get(9).render(label[:12], True, self.LABEL_COLOR)
        screen.blit(lbl, (x + (SLOT_SIZE - lbl.get_width()) // 2,
                          y + SLOT_SIZE + 2))

    # ---------------------------------------------------------------- expanded

    def _render_expanded(self, screen: pygame.Surface, bp_inv: BlueprintInventory):
        sw, sh = screen.get_size()
        W, H = 420, 300
        px = sw // 2 - W // 2
        py = sh - H - SLOT_SIZE - MARGIN_BOT - 30

        bg = pygame.Surface((W, H), pygame.SRCALPHA)
        bg.fill((10, 5, 2, 230))
        screen.blit(bg, (px, py))
        pygame.draw.rect(screen, (180, 80, 30),
                         pygame.Rect(px, py, W, H), 2)

        title = fonts.get(13, bold=True).render("// ІНВЕНТАР //", True, (255, 160, 60))
        screen.blit(title, (px + W // 2 - title.get_width() // 2, py + 8))
        pygame.draw.line(screen, (180, 80, 30),
                         (px + 10, py + 28), (px + W - 10, py + 28), 1)

        # Blueprints
        cy = py + 36
        bp_title = fonts.get(11, bold=True).render("БЛЮПРИНТИ", True, (80, 160, 220))
        screen.blit(bp_title, (px + 10, cy))
        cy += 18

        bp_items = [i for i in ALL_ITEMS if i.startswith("bp_")]
        comp_items = [i for i in ALL_ITEMS if not i.startswith("bp_")]

        cols = 3
        col_w = (W - 20) // cols
        for idx, item_id in enumerate(bp_items):
            cnt = bp_inv.count(item_id)
            col = idx % cols
            row = idx // cols
            ix  = px + 10 + col * col_w
            iy  = cy + row * 22
            color = ITEM_COLORS.get(item_id, (200, 200, 200))
            if cnt == 0:
                color = (60, 50, 40)
            lbl = fonts.get(10).render(
                f"{ITEM_LABELS[item_id]}: {cnt}", True, color
            )
            screen.blit(lbl, (ix, iy))

        cy += (len(bp_items) // cols + 1) * 22 + 8

        # Components
        pygame.draw.line(screen, (100, 50, 20),
                         (px + 10, cy), (px + W - 10, cy), 1)
        cy += 6
        comp_title = fonts.get(11, bold=True).render("КОМПОНЕНТИ", True, (180, 130, 60))
        screen.blit(comp_title, (px + 10, cy))
        cy += 18

        for idx, item_id in enumerate(comp_items):
            cnt = bp_inv.count(item_id)
            col = idx % cols
            row = idx // cols
            ix  = px + 10 + col * col_w
            iy  = cy + row * 22
            color = ITEM_COLORS.get(item_id, (200, 200, 200))
            if cnt == 0:
                color = (60, 50, 40)
            lbl = fonts.get(10).render(
                f"{ITEM_LABELS[item_id]}: {cnt}", True, color
            )
            screen.blit(lbl, (ix, iy))

        # Підказка
        hint = fonts.get(9).render("E — закрити", True, (80, 60, 40))
        screen.blit(hint, (px + W - hint.get_width() - 10, py + H - 16))

    # ---------------------------------------------------------------- private

    def _select(self, bt: BuildingType) -> BuildingType | None:
        if self._selected_bt == bt:
            self._selected_bt = None
            return None
        self._selected_bt = bt
        return bt
