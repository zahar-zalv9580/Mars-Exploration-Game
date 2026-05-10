import pygame
from ui import fonts
from systems.population import PopulationManager


class PopulationPanel:

    WIDTH   = 220
    PADDING = 10
    HEIGHT  = 80

    BG_COLOR     = (12, 6, 3, 200)
    BORDER_COLOR = (120, 55, 20)
    TEXT_COLOR   = (210, 190, 160)
    GOOD_COLOR   = (100, 220, 100)
    WARN_COLOR   = (220, 180, 30)
    BAD_COLOR    = (220, 60,  40)

    def render(self, screen: pygame.Surface, pop: PopulationManager,
               margin_top: int):
        sw, _ = screen.get_size()
        x = sw - self.WIDTH - 8
        y = margin_top

        bg = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        bg.fill(self.BG_COLOR)
        screen.blit(bg, (x, y))
        pygame.draw.rect(screen, self.BORDER_COLOR,
                         pygame.Rect(x, y, self.WIDTH, self.HEIGHT), 1)

        f_bold = fonts.get(11, bold=True)
        f_text = fonts.get(11)

        # Заголовок
        title = f_bold.render("ПОПУЛЯЦІЯ", True, (180, 80, 30))
        screen.blit(title, (x + self.PADDING, y + 4))

        # Населення / місткість
        ratio = pop.population / pop.capacity if pop.capacity > 0 else 1.0
        color = (self.BAD_COLOR  if ratio >= 1.0 else
                 self.WARN_COLOR if ratio >= 0.8 else
                 self.GOOD_COLOR)
        pop_text = f_bold.render(
            f"{pop.population} / {pop.capacity}", True, color
        )
        screen.blit(pop_text, (x + self.PADDING, y + 22))

        # Workers
        w_text = f_text.render(
            f"Робітники: {pop.workers_used} використовуються  {pop.workers_free} вільні",
            True, self.TEXT_COLOR
        )
        screen.blit(w_text, (x + self.PADDING, y + 40))

        # Бар заповненості
        bar_x = x + self.PADDING
        bar_y = y + self.HEIGHT - 14
        bar_w = self.WIDTH - self.PADDING * 2
        pygame.draw.rect(screen, (35, 18, 8),
                         pygame.Rect(bar_x, bar_y, bar_w, 6))
        fill_w = int(bar_w * min(ratio, 1.0))
        if fill_w > 0:
            pygame.draw.rect(screen, color,
                             pygame.Rect(bar_x, bar_y, fill_w, 6))
        pygame.draw.rect(screen, self.BORDER_COLOR,
                         pygame.Rect(bar_x, bar_y, bar_w, 6), 1)


