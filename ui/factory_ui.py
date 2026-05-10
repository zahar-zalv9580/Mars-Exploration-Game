"""
Factory UI — відкривається при кліку на фабрику поруч з ровером.
"""
from __future__ import annotations
import pygame
from ui import fonts
from systems.factory import FactoryManager, BlueprintInventory, RECIPES, RECIPE_ORDER
from systems.resources import ResourceSystem, Resource

# Кольори категорій
CATEGORY_COLORS = {
    "blueprint": (80,  160, 220),
    "component": (180, 130, 60),
    "endgame":   (180, 80,  220),
}

RES_COLORS: dict[Resource, tuple] = {
    Resource.ENERGY:  (255, 220, 50),
    Resource.IRON:    (180, 130, 90),
    Resource.WATER:   (80,  160, 220),
    Resource.SILICON: (140, 200, 140),
    Resource.FUEL:    (220, 120, 50),
    Resource.URANIUM: (130, 220, 100),
    Resource.FOOD:    (180, 220, 80),
}

W, H = 560, 400
RECIPE_W = 220
PADDING  = 12


class FactoryUI:
    BG          = (10, 5, 2, 230)
    BORDER      = (180, 80, 30)
    SEL_BG      = (40, 20, 8)
    SEL_BORDER  = (220, 150, 40)
    TEXT        = (210, 190, 160)
    DIM         = (100, 80, 60)
    CRAFT_OK    = (80,  200, 80)
    CRAFT_NO    = (120, 60,  40)
    TITLE       = (255, 160, 60)

    def __init__(self):
        self._visible   = False
        self._selected  = 0    # індекс у RECIPE_ORDER
        self._scroll    = 0

    # ---------------------------------------------------------------- public

    @property
    def visible(self) -> bool:
        return self._visible

    def open(self):
        self._visible = True

    def close(self):
        self._visible = False

    def toggle(self):
        self._visible = not self._visible

    def handle_event(
        self, event: pygame.event.Event,
        factory: FactoryManager,
        blueprint_inv: BlueprintInventory,
        resources: ResourceSystem,
    ) -> bool:
        """Повертає True якщо подія поглинута."""
        if not self._visible:
            return False

        if event.type == pygame.KEYDOWN and event.key in (pygame.K_f, pygame.K_ESCAPE):
            self.close()
            return True

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            sw, sh = pygame.display.get_surface().get_size()
            px = sw // 2 - W // 2
            py = sh // 2 - H // 2

            # Клік поза панеллю — закрити
            if not pygame.Rect(px, py, W, H).collidepoint(mx, my):
                self.close()
                return True

            # Клік по рецепту
            list_y = py + 40
            for i, rid in enumerate(RECIPE_ORDER):
                ry = list_y + i * 36 - self._scroll
                if py + 36 <= ry <= py + H - 12 and \
                   pygame.Rect(px + PADDING, ry, RECIPE_W - PADDING, 32).collidepoint(mx, my):
                    self._selected = i
                    return True

            # Кнопка CRAFT
            craft_rect = pygame.Rect(px + RECIPE_W + PADDING,
                                     py + H - 52, 160, 36)
            if craft_rect.collidepoint(mx, my):
                rid = RECIPE_ORDER[self._selected]
                factory.enqueue(rid, resources)
                return True

            # Кнопка скасування першого в черзі
            cancel_rect = pygame.Rect(px + RECIPE_W + PADDING + 170,
                                      py + H - 52, 100, 36)
            if cancel_rect.collidepoint(mx, my) and factory.queue:
                factory.remove_from_queue(0)
                return True

        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, self._scroll - event.y * 20)

        return self._visible   # поглинаємо всі події поки відкрито

    def render(
        self, screen: pygame.Surface,
        factory: FactoryManager,
        blueprint_inv: BlueprintInventory,
        resources: ResourceSystem,
    ):
        if not self._visible:
            return

        sw, sh = screen.get_size()
        px = sw // 2 - W // 2
        py = sh // 2 - H // 2

        # Фон
        panel = pygame.Surface((W, H), pygame.SRCALPHA)
        panel.fill(self.BG)
        screen.blit(panel, (px, py))
        pygame.draw.rect(screen, self.BORDER, pygame.Rect(px, py, W, H), 2)

        # Заголовок
        title = fonts.get(16, bold=True).render("// FACTORY //", True, self.TITLE)
        screen.blit(title, (px + W // 2 - title.get_width() // 2, py + 8))
        pygame.draw.line(screen, self.BORDER,
                         (px + PADDING, py + 34),
                         (px + W - PADDING, py + 34), 1)

        # Вертикальний роздільник
        pygame.draw.line(screen, self.BORDER,
                         (px + RECIPE_W, py + 34),
                         (px + RECIPE_W, py + H), 1)

        # ── Список рецептів (ліво) ────────────────────────────────────────
        clip = screen.subsurface(pygame.Rect(px + 1, py + 36,
                                             RECIPE_W - 1, H - 38))
        clip_surf = pygame.Surface((RECIPE_W - 1, H - 38), pygame.SRCALPHA)

        for i, rid in enumerate(RECIPE_ORDER):
            recipe  = RECIPES[rid]
            ry      = i * 36 - self._scroll
            if ry + 36 < 0 or ry > H - 38:
                continue

            selected = (i == self._selected)
            can_craft = factory.can_craft(rid, resources)
            cat_color = CATEGORY_COLORS.get(recipe.category, self.TEXT)

            # Фон рядка
            row_rect = pygame.Rect(0, ry, RECIPE_W - 2, 34)
            if selected:
                pygame.draw.rect(clip_surf, self.SEL_BG, row_rect)
                pygame.draw.rect(clip_surf, self.SEL_BORDER, row_rect, 1)
            else:
                pygame.draw.rect(clip_surf, (0, 0, 0, 0), row_rect)

            # Назва рецепту
            color = cat_color if can_craft else self.DIM
            lbl = fonts.get(11, bold=True).render(recipe.label, True, color)
            clip_surf.blit(lbl, (6, ry + 4))

            # Count у інвентарі
            cnt = blueprint_inv.count(rid)
            if cnt > 0:
                c = fonts.get(10).render(f"x{cnt}", True, (160, 220, 160))
                clip_surf.blit(c, (RECIPE_W - 30, ry + 4))

            # Час
            t = fonts.get(9).render(f"{recipe.craft_time:.0f}s", True, self.DIM)
            clip_surf.blit(t, (6, ry + 20))

        clip.blit(clip_surf, (0, 0))

        # ── Деталі вибраного рецепту (право) ─────────────────────────────
        rx = px + RECIPE_W + PADDING
        ry = py + 40
        recipe = RECIPES[RECIPE_ORDER[self._selected]]
        can_craft = factory.can_craft(RECIPE_ORDER[self._selected], resources)

        # Назва
        name = fonts.get(13, bold=True).render(recipe.label, True, self.TITLE)
        screen.blit(name, (rx, ry))
        ry += 22

        # Опис
        desc = fonts.get(10).render(recipe.description, True, self.DIM)
        screen.blit(desc, (rx, ry))
        ry += 20

        # Час крафту
        t = fonts.get(11).render(f"Craft time: {recipe.craft_time:.0f}s",
                                  True, self.TEXT)
        screen.blit(t, (rx, ry))
        ry += 24

        # Витрати
        inp_title = fonts.get(11, bold=True).render("ПОТРІБНО:", True, self.TEXT)
        screen.blit(inp_title, (rx, ry))
        ry += 18
        for res, amt in recipe.inputs:
            have = resources.amount(res)
            color = self.CRAFT_OK if have >= amt else self.CRAFT_NO
            line  = fonts.get(11).render(
                f"  {res.value.capitalize():10s} {int(amt):4d}  (have {int(have)})",
                True, color
            )
            screen.blit(line, (rx, ry))
            ry += 17

        ry += 8
        # Вихід
        out_title = fonts.get(11, bold=True).render("ВИХІД:", True, self.TEXT)
        screen.blit(out_title, (rx, ry))
        ry += 18
        out_color = CATEGORY_COLORS.get(recipe.category, self.TEXT)
        out_line  = fonts.get(11).render(
            f"  {recipe.output_item}  x{recipe.output_count}", True, out_color
        )
        screen.blit(out_line, (rx, ry))
        ry += 24

        # ── Поточний крафт ────────────────────────────────────────────────
        pygame.draw.line(screen, self.BORDER,
                         (rx, ry), (px + W - PADDING, ry), 1)
        ry += 8

        if factory.is_busy and factory.current_recipe:
            cur = factory.current_recipe
            now = fonts.get(11, bold=True).render(
                f"NOW: {cur.label}", True, (160, 200, 80)
            )
            screen.blit(now, (rx, ry))
            ry += 18

            # Прогрес-бар
            bar_w = W - RECIPE_W - PADDING * 2
            pygame.draw.rect(screen, (30, 30, 30),
                             pygame.Rect(rx, ry, bar_w, 10))
            pygame.draw.rect(screen, (80, 180, 80),
                             pygame.Rect(rx, ry, int(bar_w * factory.progress), 10))
            pygame.draw.rect(screen, self.BORDER,
                             pygame.Rect(rx, ry, bar_w, 10), 1)
            ry += 14

            tl = fonts.get(10).render(
                f"{factory.time_left:.1f}s left", True, self.DIM
            )
            screen.blit(tl, (rx, ry))
            ry += 18
        else:
            idle = fonts.get(11).render("СТІЙ — оберіть рецепт і КРАФТ",
                                         True, self.DIM)
            screen.blit(idle, (rx, ry))
            ry += 20

        # Черга
        if factory.queue:
            q_title = fonts.get(10).render(
                f"QUEUE ({len(factory.queue)}):", True, self.DIM
            )
            screen.blit(q_title, (rx, ry))
            ry += 16
            for qid in factory.queue[:3]:
                q_lbl = fonts.get(10).render(
                    f"  - {RECIPES[qid].label}", True, self.DIM
                )
                screen.blit(q_lbl, (rx, ry))
                ry += 14

        # ── Кнопки ────────────────────────────────────────────────────────
        btn_y = py + H - 52
        craft_rect  = pygame.Rect(rx, btn_y, 160, 36)
        cancel_rect = pygame.Rect(rx + 170, btn_y, 100, 36)

        craft_color = self.CRAFT_OK if can_craft else self.CRAFT_NO
        pygame.draw.rect(screen, craft_color, craft_rect)
        pygame.draw.rect(screen, self.BORDER, craft_rect, 1)
        c_lbl = fonts.get(13, bold=True).render("КРАФТ", True, (0, 0, 0))
        screen.blit(c_lbl, c_lbl.get_rect(center=craft_rect.center))

        if factory.queue:
            pygame.draw.rect(screen, (60, 30, 10), cancel_rect)
            pygame.draw.rect(screen, self.BORDER, cancel_rect, 1)
            x_lbl = fonts.get(11).render("СКАСУВАТИ", True, self.TEXT)
            screen.blit(x_lbl, x_lbl.get_rect(center=cancel_rect.center))

        # Підказка
        hint = fonts.get(9).render("F — закрити", True, self.DIM)
        screen.blit(hint, (px + W - hint.get_width() - PADDING, py + H - 18))
