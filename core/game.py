import pygame
from core.camera import Camera
from world.world import World
from entities.rover import Rover
from ui.ui import UI

STATE_MENU  = "menu"
STATE_GAME  = "game"
STATE_PAUSE = "pause"


class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen  = screen
        self.running = True
        self.state   = STATE_GAME

        print("Loading world from maps...")
        self.world = World(
            width=128, height=64,
            height_path="assets/maps/height.png",
            biome_path= "assets/maps/biome.png",
            map_path=   "assets/maps/map.png",
        )
        print("World loaded.")

        cx = self.world.width  * self.world.TILE_SIZE // 2
        cy = self.world.height * self.world.TILE_SIZE // 2
        self.rover  = Rover(cx, cy)
        self.camera = Camera(screen.get_width(), screen.get_height())
        self.camera.update(self.rover.x, self.rover.y, self.world)

        self.ui = UI(screen)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == STATE_GAME:
                        self.state = STATE_PAUSE
                    elif self.state == STATE_PAUSE:
                        self.state = STATE_GAME
                if event.key == pygame.K_h:
                    self.world.toggle_overlay()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == STATE_GAME:
                    mx, my = event.pos
                    self.ui.handle_click(mx, my, self.world, self.camera)

    def update(self, dt: float):
        if self.state == STATE_GAME:
            keys = pygame.key.get_pressed()
            self.rover.update(dt, keys, self.world)
            self.camera.update(self.rover.x, self.rover.y, self.world)

    def render(self):
        self.screen.fill((10, 5, 2))

        if self.state in (STATE_GAME, STATE_PAUSE):
            self.world.render(self.screen, self.camera)
            self.rover.render(self.screen, self.camera)
            self._render_debug_coords()
            self.ui.render()

        if self.state == STATE_PAUSE:
            self._render_pause_overlay()

    def _render_debug_coords(self):
        tx = int(self.rover.x // self.world.TILE_SIZE)
        ty = int(self.rover.y // self.world.TILE_SIZE)
        font = pygame.font.SysFont("consolas", 13)
        text = font.render(f"Rover tile: ({tx}, {ty})", True, (160, 160, 140))
        self.screen.blit(text, (10, 10))

    def _render_pause_overlay(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        font = pygame.font.SysFont("consolas", 48, bold=True)
        text = font.render("PAUSED", True, (220, 100, 50))
        rect = text.get_rect(center=(self.screen.get_width() // 2,
                                     self.screen.get_height() // 2))
        self.screen.blit(text, rect)
        font2 = pygame.font.SysFont("consolas", 18)
        hint = font2.render("ESC to resume", True, (160, 100, 60))
        self.screen.blit(hint, hint.get_rect(center=(self.screen.get_width() // 2,
                                                      self.screen.get_height() // 2 + 50)))
