from __future__ import annotations
import pygame
import math
from ui import fonts
from systems.lore import (
    LaboratoryManager, LogEntry, LogType, LogCategory,
    FragmentRarity, ALL_LOGS, CATEGORY_COLOR,
    FRAGMENT_RARITY_COLOR, FRAGMENT_RARITY_CHANCES
)

W, H       = 640, 440
CAT_W      = 110
LIST_W     = 180
DETAIL_W   = W - CAT_W - LIST_W
PADDING    = 10

CATEGORIES = [
    LogCategory.SYSTEM,
    LogCategory.SIGNAL,
    LogCategory.RARK,
    LogCategory.OBSERVER,
    LogCategory.CORRUPT,
]

CAT_LABELS = {
    LogCategory.SYSTEM:   "СИСТЕМА",
    LogCategory.SIGNAL:   "СИГНАЛИ",
    LogCategory.RARK:     "R-ARK",
    LogCategory.OBSERVER: "СПОСТЕРІГАЧІ",
    LogCategory.CORRUPT:  "C0RRUPT",
}


class LaboratoryUI:
    BG     = (8, 4, 2, 235)
    BORDER = (180, 80, 30)
    TEXT   = (210, 190, 160)
    DIM    = (80, 60, 40)
    GOLD   = (255, 200, 50)
    GREEN  = (80, 200, 80)
    RED    = (220, 60, 40)

    def __init__(self):
        self._visible  = False
        self._category = LogCategory.SYSTEM
        self._selected: str | None = None   # log id
        self._scroll   = 0
        self._time     = 0.0

    @property
    def visible(self) -> bool:
        return self._visible

    def open(self):  self._visible = True
    def close(self): self._visible = False

    def toggle(self):
        self._visible = not self._visible

    #ПОДІЇ

    def handle_event(self, event: pygame.event.Event,
                     lab: LaboratoryManager,
                     has_lab: bool) -> bool:
        if not self._visible:
            return False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_l:
            self.close()
            return True

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            sw, sh = pygame.display.get_surface().get_size()
            px = sw // 2 - W // 2
            py = sh // 2 - H // 2

            if not pygame.Rect(px, py, W, H).collidepoint(mx, my):
                self.close()
                return True

            # Категорія
            for i, cat in enumerate(CATEGORIES):
                ry = py + 40 + i * 30
                if pygame.Rect(px + 2, ry, CAT_W - 4, 26).collidepoint(mx, my):
                    self._category = cat
                    self._selected = None
                    self._scroll   = 0
                    return True

            # Список логів
            list_logs = self._filtered_logs(lab)
            lx = px + CAT_W
            for i, log in enumerate(list_logs):
                ry = py + 40 + i * 28 - self._scroll
                if py + 38 <= ry <= py + H - 60:
                    if pygame.Rect(lx + 2, ry, LIST_W - 4, 26).collidepoint(mx, my):
                        self._selected = log.id
                        return True

            # Кнопки
            bx = px + CAT_W + LIST_W + PADDING
            by = py + H - 52

            # ANALYZE (research logs)
            analyze_rect = pygame.Rect(bx, by, 130, 34)
            if analyze_rect.collidepoint(mx, my) and self._selected:
                log = next((l for l in ALL_LOGS if l.id == self._selected), None)
                if log and log.log_type == LogType.RESEARCH and has_lab:
                    lab.enqueue_research(self._selected)
                return True

            # Fragment analysis buttons
            for i, (rarity, _) in enumerate(FRAGMENT_RARITY_CHANCES):
                fr_rect = pygame.Rect(bx + 140 + i * 76, by, 70, 34)
                if fr_rect.collidepoint(mx, my):
                    lab.enqueue_signal(rarity)
                    return True

        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, self._scroll - event.y * 20)

        return self._visible

    #РЕНДЕР

    def render(self, screen: pygame.Surface, lab: LaboratoryManager,
               has_lab: bool):
        if not self._visible:
            return
        self._time += 1 / 60

        sw, sh = screen.get_size()
        px = sw // 2 - W // 2
        py = sh // 2 - H // 2

        # Фон
        bg = pygame.Surface((W, H), pygame.SRCALPHA)
        bg.fill(self.BG)
        screen.blit(bg, (px, py))
        pygame.draw.rect(screen, self.BORDER, pygame.Rect(px, py, W, H), 2)

        # Заголовок
        title = fonts.get(15, bold=True).render(
            "// ЛАБОРАТОРІЯ - АНАЛІЗ ЛОРУ //", True, self.GOLD
        )
        screen.blit(title, (px + W//2 - title.get_width()//2, py + 8))

        # Прогрес логів
        prog = fonts.get(10).render(
            f"ЛОГИ: {lab.discovered_count}/{lab.total_logs}  "
            f"КРИТИЧНІ: {lab.critical_found}/{lab.critical_total}",
            True, self.DIM
        )
        screen.blit(prog, (px + W - prog.get_width() - PADDING, py + 10))

        pygame.draw.line(screen, self.BORDER,
                         (px + PADDING, py + 32),
                         (px + W - PADDING, py + 32), 1)

        # Вертикальні роздільники
        pygame.draw.line(screen, self.BORDER,
                         (px + CAT_W, py + 32), (px + CAT_W, py + H - 56), 1)
        pygame.draw.line(screen, self.BORDER,
                         (px + CAT_W + LIST_W, py + 32),
                         (px + CAT_W + LIST_W, py + H - 56), 1)
        pygame.draw.line(screen, self.BORDER,
                         (px, py + H - 56), (px + W, py + H - 56), 1)

        self._render_categories(screen, px, py, lab)
        self._render_log_list(screen, px, py, lab)
        self._render_detail(screen, px, py, lab)
        self._render_bottom(screen, px, py, lab, has_lab)

    # Панелі

    def _render_categories(self, screen, px, py, lab):
        for i, cat in enumerate(CATEGORIES):
            ry  = py + 40 + i * 30
            sel = (cat == self._category)
            color = CATEGORY_COLOR.get(cat, self.TEXT)

            if sel:
                bg = pygame.Surface((CAT_W - 4, 26), pygame.SRCALPHA)
                bg.fill((*color, 30))
                screen.blit(bg, (px + 2, ry))
                pygame.draw.rect(screen, color,
                                 pygame.Rect(px + 2, ry, CAT_W - 4, 26), 1)

            lbl = fonts.get(10, bold=True).render(
                CAT_LABELS[cat], True, color if sel else self.DIM
            )
            screen.blit(lbl, (px + 6, ry + 6))

            # Кількість знайдених
            found = sum(1 for l in ALL_LOGS
                        if l.category == cat and lab.is_discovered(l.id))
            total = sum(1 for l in ALL_LOGS if l.category == cat)
            cnt = fonts.get(8).render(f"{found}/{total}", True, self.DIM)
            screen.blit(cnt, (px + CAT_W - cnt.get_width() - 4, ry + 8))

    def _filtered_logs(self, lab: LaboratoryManager) -> list[LogEntry]:
        return [l for l in ALL_LOGS if l.category == self._category]

    def _render_log_list(self, screen, px, py, lab):
        logs = self._filtered_logs(lab)
        lx   = px + CAT_W
        clip = screen.subsurface(
            pygame.Rect(lx + 1, py + 33, LIST_W - 2, H - 90)
        )
        surf = pygame.Surface((LIST_W - 2, H - 90), pygame.SRCALPHA)

        for i, log in enumerate(logs):
            ry      = i * 28 - self._scroll
            discovered = lab.is_discovered(log.id)
            sel     = (log.id == self._selected)
            color   = CATEGORY_COLOR.get(log.category, self.TEXT)

            if sel:
                bg = pygame.Surface((LIST_W - 4, 26), pygame.SRCALPHA)
                bg.fill((*color, 25))
                surf.blit(bg, (2, ry))
                pygame.draw.rect(surf, color,
                                 pygame.Rect(2, ry, LIST_W - 4, 26), 1)

            if discovered:
                title_color = color if not log.corrupted else (200, 140, 60)
                title_text  = log.title
            else:
                title_color = self.DIM
                title_text  = "[ ENCRYPTED ]"
                if log.log_type == LogType.RESEARCH:
                    title_text = "[ Потрібна лабораторія ]"
                elif log.log_type == LogType.SIGNAL:
                    title_text = "[ Фрагмент ]"

            lbl = fonts.get(10).render(title_text[:22], True, title_color)
            surf.blit(lbl, (6, ry + 4))

            if log.critical and discovered:
                star = fonts.get(9).render("★", True, self.GOLD)
                surf.blit(star, (LIST_W - 16, ry + 5))

        clip.blit(surf, (0, 0))

    def _render_detail(self, screen, px, py, lab):
        dx = px + CAT_W + LIST_W + PADDING
        dy = py + 38
        dw = DETAIL_W - PADDING * 2

        if not self._selected:
            hint = fonts.get(10).render("Виберіть лог.", True, self.DIM)
            screen.blit(hint, (dx, dy + 20))
            return

        log = next((l for l in ALL_LOGS if l.id == self._selected), None)
        if not log:
            return

        discovered = lab.is_discovered(log.id)
        cat_color  = CATEGORY_COLOR.get(log.category, self.TEXT)

        # Заголовок
        if discovered:
            t = fonts.get(12, bold=True).render(log.title, True, cat_color)
        else:
            t = fonts.get(12, bold=True).render("[ ENCRYPTED ]", True, self.DIM)
        screen.blit(t, (dx, dy))
        dy += 18

        # Дата + тип
        meta = fonts.get(9).render(
            f"{log.date}  [{log.log_type.name}]", True, self.DIM
        )
        screen.blit(meta, (dx, dy))
        dy += 18

        pygame.draw.line(screen, self.BORDER,
                         (dx, dy), (dx + dw, dy), 1)
        dy += 8

        if discovered:
            for line in log.text:
                # Corruption glitch effect
                if log.corrupted and self._time % 2 < 0.1:
                    line = line.replace('E', 'Ξ').replace('O', 'Ø').replace('A', 'Λ')
                lbl = fonts.get(10).render(line, True,
                                            (200, 140, 60) if log.corrupted
                                            else self.TEXT)
                screen.blit(lbl, (dx, dy))
                dy += 16

            if log.critical:
                dy += 4
                cr = fonts.get(9, bold=True).render(
                    "★ КРИТИЧНИЙ ЛОГ", True, self.GOLD
                )
                screen.blit(cr, (dx, dy))
        else:
            # Зашифровано
            for line in ["[ENCRYPTED DATA]", "[ACCESS DENIED]",
                          "[ANALYZE TO DECRYPT]"]:
                lbl = fonts.get(10).render(line, True, self.DIM)
                screen.blit(lbl, (dx, dy))
                dy += 16

        # Якщо в черзі або аналізується
        if lab.is_busy and lab.current_log and lab.current_log.id == self._selected:
            dy += 8
            bar_w = dw
            pygame.draw.rect(screen, (30, 15, 5),
                             pygame.Rect(dx, dy, bar_w, 8))
            pygame.draw.rect(screen, cat_color,
                             pygame.Rect(dx, dy, int(bar_w * lab.progress), 8))
            pygame.draw.rect(screen, self.BORDER,
                             pygame.Rect(dx, dy, bar_w, 8), 1)
            dy += 12
            tl = fonts.get(9).render(
                f"ANALYZING... {lab.time_left:.0f}s", True, self.DIM
            )
            screen.blit(tl, (dx, dy))

    def _render_bottom(self, screen, px, py, lab, has_lab):
        bx = px + CAT_W + LIST_W + PADDING
        by = py + H - 50

        # ANALYZE кнопка
        log = next((l for l in ALL_LOGS if l.id == self._selected), None)
        can_analyze = (
            log is not None
            and not lab.is_discovered(log.id)
            and log.log_type == LogType.RESEARCH
            and has_lab
            and self._selected not in [lab.current_log.id if lab.current_log else None]
        )
        btn_color = self.GREEN if can_analyze else (40, 30, 20)
        pygame.draw.rect(screen, btn_color,
                         pygame.Rect(bx, by, 130, 34))
        pygame.draw.rect(screen, self.BORDER,
                         pygame.Rect(bx, by, 130, 34), 1)
        btn_lbl = fonts.get(11, bold=True).render("ANALYZE", True,
                                                    (0, 0, 0) if can_analyze
                                                    else self.DIM)
        screen.blit(btn_lbl, btn_lbl.get_rect(
            center=pygame.Rect(bx, by, 130, 34).center))

        # Fragment кнопки
        for i, (rarity, _) in enumerate(FRAGMENT_RARITY_CHANCES):
            fx = bx + 140 + i * 76
            cnt = lab.fragments.get(rarity.value, 0)
            c   = FRAGMENT_RARITY_COLOR[rarity]
            has = cnt > 0 and has_lab
            pygame.draw.rect(screen, c if has else (20, 12, 6),
                             pygame.Rect(fx, by, 70, 34))
            pygame.draw.rect(screen, self.BORDER,
                             pygame.Rect(fx, by, 70, 34), 1)
            r_lbl = fonts.get(9, bold=True).render(
                rarity.value[:4].upper(), True,
                (0, 0, 0) if has else self.DIM
            )
            screen.blit(r_lbl, r_lbl.get_rect(
                center=(fx + 35, by + 12)))
            cnt_lbl = fonts.get(9).render(f"x{cnt}", True,
                                           self.TEXT if has else self.DIM)
            screen.blit(cnt_lbl, cnt_lbl.get_rect(center=(fx + 35, by + 26)))

        # Hint
        hint = fonts.get(9).render("L — close", True, self.DIM)
        screen.blit(hint, (px + W - hint.get_width() - PADDING, py + H - 16))
