import pygame
from core.camera import Camera
from world.world import World
from entities.rover import Rover
from ui.ui import UI
from ui.menus import MainMenu, PauseMenu, GameOverScreen, EndingScreen
from systems.resources import ResourceSystem, Resource
from systems.building_manager import BuildingManager
from systems.exploration import ExplorationSystem
from systems.population import PopulationManager
from systems.factory import FactoryManager
from systems.day_cycle import DayCycle
from systems.crisis import CrisisManager
from systems.lore import LaboratoryManager
from systems.save_load import save_game, load_game, save_exists, delete_save
from systems.fragment_spawner import FragmentSpawner
from ui.laboratory_ui import LaboratoryUI
from ui.factory_ui import FactoryUI
from ui.weather_fx import WeatherFX
from ui.jammer_ui import JammerUI
from systems.day_cycle import DayCycle

# Стани гри
STATE_MAIN_MENU = "main_menu"
STATE_GAME      = "game"
STATE_PAUSE     = "pause"
STATE_GAME_OVER = "game_over"
STATE_ENDING    = "ending"

TICK_RATE = 1.0


class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen  = screen
        self.running = True
        self.state   = STATE_MAIN_MENU

        # Меню — завантажується одразу
        self._main_menu  = MainMenu(screen, has_save=save_exists())
        self._pause_menu: PauseMenu | None         = None
        self._game_over:  GameOverScreen | None    = None
        self._ending:     EndingScreen | None      = None

        # Ігрові об'єкти — створюються при старті гри
        self.world:     World | None           = None
        self.rover:     Rover | None           = None
        self.camera:    Camera | None          = None
        self.resources: ResourceSystem | None  = None
        self.buildings: BuildingManager | None = None
        self.ui:        UI | None              = None
        self._tick_timer = 0.0

    # ---------------------------------------------------------------- start

    def _start_game(self):
        sw, sh = self.screen.get_size()
        print("Loading world...")
        self.world = World(
            width=128, height=64,
            height_path="assets/maps/height.png",
            biome_path= "assets/maps/biome.png",
            map_path=   "assets/maps/map.png",
        )
        print("World loaded.")

        cx = self.world.width  * self.world.TILE_SIZE // 2
        cy = self.world.height * self.world.TILE_SIZE // 2
        self.rover     = Rover(cx, cy)
        self.rover.load_texture()
        self.camera    = Camera(sw, sh)
        self.camera.update(self.rover.x, self.rover.y, self.world)

        self.resources   = ResourceSystem()
        self.buildings   = BuildingManager()
        self.exploration = ExplorationSystem(self.world)
        self.population  = PopulationManager()
        self.factory     = FactoryManager()
        self.day         = DayCycle()
        self.crisis      = CrisisManager()
        self.lab         = LaboratoryManager()
        self.fragments   = FragmentSpawner(self.world)
        self._factory_ui = FactoryUI()
        self._lab_ui     = LaboratoryUI()
        self._weather_fx = WeatherFX(self.screen)
        self._jammer_ui  = JammerUI()
        self.buildings.load_icons()

        self.ui = UI(self.screen)
        self.ui.load_icons(self.buildings._icons)

        self._pause_menu = PauseMenu(self.screen)
        self._tick_timer = 0.0
        from systems.crisis import Modifiers
        self._mods = Modifiers()

        # Тестові ресурси
        self.resources.set(Resource.ENERGY,  120.0)
        self.resources.set(Resource.IRON,    100.0)
        self.resources.set(Resource.WATER,    15.0)
        self.resources.set(Resource.SILICON,  60.0)
        self.resources.set(Resource.FUEL,     30.0)
        self.resources.set(Resource.URANIUM,   5.0)
        self.resources.set(Resource.FOOD,     90.0)

        self.state = STATE_GAME

    def _go_game_over(self, reason: str = "hub"):
        self._game_over = GameOverScreen(self.screen, reason)
        self.state = STATE_GAME_OVER

    def _go_ending(self, ending: str = "good"):
        discovered = list(self.lab._discovered) if self.lab else []
        self._ending = EndingScreen(self.screen, ending, discovered_logs=discovered)
        self.state = STATE_ENDING

    def _go_main_menu(self):
        self._main_menu = MainMenu(self.screen, has_save=save_exists())
        self.state = STATE_MAIN_MENU

    # ---------------------------------------------------------------- events

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # ── Головне меню ──
            if self.state == STATE_MAIN_MENU:
                action = self._main_menu.handle_event(event)
                if action == "new_game":
                    self._start_game()
                elif action == "continue":
                    self._start_game()
                    load_game(self)
                elif action == "exit":
                    self.running = False

            # ── Пауза ──
            elif self.state == STATE_PAUSE:
                action = self._pause_menu.handle_event(event)
                if action == "resume":
                    self.state = STATE_GAME
                elif action == "save":
                    ok = save_game(self)
                    self.ui.hud.push_message(
                        '// GAME SAVED //' if ok else '// SAVE FAILED //'
                    )
                    self.state = STATE_GAME
                elif action == "main_menu":
                    self._go_main_menu()
                elif action == "exit":
                    self.running = False

            # ── Гра ──
            elif self.state == STATE_GAME:
                self._handle_game_event(event)

            # ── Game Over ──
            elif self.state == STATE_GAME_OVER:
                action = self._game_over.handle_event(event)
                if action == "new_game":
                    self._start_game()
                elif action == "main_menu":
                    self._go_main_menu()

            # ── Ending ──
            elif self.state == STATE_ENDING:
                action = self._ending.handle_event(event)
                if action == "new_game":
                    self._start_game()
                elif action == "main_menu":
                    self._go_main_menu()

    def _handle_game_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.buildings.is_placing:
                    self.buildings.cancel_placement()
                    self.ui.inventory.deselect()
                else:
                    self.state = STATE_PAUSE

            elif event.key == pygame.K_h:
                self.world.toggle_overlay()
            elif event.key == pygame.K_q:
                rover_tx = int(self.rover.x // self.world.TILE_SIZE)
                rover_ty = int(self.rover.y // self.world.TILE_SIZE)
                self.exploration.scan_tile(rover_tx, rover_ty)
            elif event.key == pygame.K_f:
                rover_tx = int(self.rover.x // self.world.TILE_SIZE)
                rover_ty = int(self.rover.y // self.world.TILE_SIZE)
                for (tx, ty), b in self.buildings._buildings.items():
                    if b.type.value == 'factory' and max(abs(tx-rover_tx), abs(ty-rover_ty)) <= 2:
                        self._factory_ui.toggle()
                        break
            elif event.key == pygame.K_l:
                rover_tx = int(self.rover.x // self.world.TILE_SIZE)
                rover_ty = int(self.rover.y // self.world.TILE_SIZE)
                for (tx, ty), b in self.buildings._buildings.items():
                    if b.type.value == 'laboratory' and max(abs(tx-rover_tx), abs(ty-rover_ty)) <= 2:
                        self._lab_ui.toggle()
                        break
            elif event.key == pygame.K_j:
                rover_tx = int(self.rover.x // self.world.TILE_SIZE)
                rover_ty = int(self.rover.y // self.world.TILE_SIZE)
                has_jammer = False
                for (tx, ty), b in self.buildings._buildings.items():
                    if b.type.value == 'jammer' and b.is_active and max(abs(tx-rover_tx), abs(ty-rover_ty)) <= 2:
                        has_jammer = True
                        break
                if has_jammer:
                    self._jammer_ui.toggle()
            elif event.key == pygame.K_r:
                # Collect fragment
                rover_tx = int(self.rover.x // self.world.TILE_SIZE)
                rover_ty = int(self.rover.y // self.world.TILE_SIZE)
                frag = self.fragments.try_collect(rover_tx, rover_ty)
                if frag:
                    self.lab.add_fragment(frag.rarity)
                    self.ui.hud.push_message(
                        f'// SIGNAL FRAGMENT RECOVERED: {frag.label} //'
                    )

            else:
                bt = self.ui.handle_key(event.key, self.buildings.blueprint_inv)
                if bt:
                    self.buildings.start_placement(bt)
                elif bt is None and self.buildings.is_placing:
                    self.buildings.cancel_placement()

            # DEV: тест кінцівок (видали пізніше)
            if event.key == pygame.K_F1:
                self._go_game_over("hub")
            if event.key == pygame.K_F2:
                self._go_ending("good")
            if event.key == pygame.K_F3:
                self._go_ending("secret")

        # Lab UI
        if self._lab_ui.visible:
            has_lab = any(
                b.type.value == 'laboratory' and b.is_active
                for b in self.buildings._buildings.values()
            )
            self._lab_ui.handle_event(event, self.lab, has_lab)
            return

        # Factory UI поглинає події якщо відкрита
        if self._factory_ui.visible:
            self._factory_ui.handle_event(
                event, self.factory,
                self.buildings.blueprint_inv, self.resources
            )
            return

        # Jammer UI поглинає події якщо відкрита
        if self._jammer_ui.visible:
            if self._jammer_ui.handle_event(event):
                return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if event.button == 1:
                if self.buildings.is_placing:
                    placed = self.buildings.try_place(
                        self.resources, self.world,
                        self.population,
                        self.population.workers_free
                    )
                    if placed:
                        # Якщо поставили Habitat — збільшуємо capacity
                        from entities.building import BuildingType
                        if self.ui.inventory.selected_type == BuildingType.HABITAT:
                            self.population.add_habitat()
                    self.ui.inventory.deselect()
                else:
                    result = self.ui.handle_click(mx, my, self.world, self.camera, self.buildings.blueprint_inv)
                    if result == 'inventory':
                        bt = self.ui.inventory.selected_type
                        if bt:
                            self.buildings.start_placement(bt)
            elif event.button == 3:
                self.buildings.cancel_placement()
                self.ui.inventory.deselect()

        if event.type == pygame.MOUSEMOTION and self.buildings.is_placing:
            mx, my = event.pos
            rover_tx = int(self.rover.x // self.world.TILE_SIZE)
            rover_ty = int(self.rover.y // self.world.TILE_SIZE)
            self.buildings.update_ghost(
                mx, my, self.world, self.camera, rover_tx, rover_ty
            )

    # ---------------------------------------------------------------- update

    def update(self, dt: float):
        if self.state == STATE_MAIN_MENU:
            self._main_menu.update(dt)

        elif self.state == STATE_PAUSE:
            self._pause_menu.update(dt)

        elif self.state == STATE_GAME:
            keys = pygame.key.get_pressed()
            self.rover.update(dt, keys, self.world)
            self.camera.update(self.rover.x, self.rover.y, self.world)
            rover_tx = int(self.rover.x // self.world.TILE_SIZE)
            rover_ty = int(self.rover.y // self.world.TILE_SIZE)
            self.exploration.explore_around(rover_tx, rover_ty)

            # День
            new_day = self.day.tick(dt)
            self.ui.hud.update(dt)
            for msg in self.day.new_messages:
                self.ui.hud.push_message(msg)
            self.day.new_messages.clear()
            # Кінець гри на день 30
            if self.day.is_final:
                has_jammer = any(
                    b.type.value == 'jammer' and b.is_active
                    for b in self.buildings._buildings.values()
                )
                all_logs = True  # TODO: перевірка логів лабораторії
                all_logs = self.lab.secret_ending_unlocked()
                if has_jammer and all_logs:
                    self._go_ending('secret')
                elif has_jammer:
                    self._go_ending('good')
                else:
                    self._go_ending('bad')
                return

            # Програш якщо нема Hub
            hub_alive = any(
                b.type.value == 'hub'
                for b in self.buildings._buildings.values()
            )
            if not hub_alive and self.buildings._buildings:
                self._go_game_over('hub')
                return

            # Програш якщо population == 0 більше 10 секунд
            if self.population.population <= 0:
                self._go_game_over('food')
                return

            # Кризи
            self._mods = self.crisis.tick(
                dt, self.day.phase, self.day.event_rate,
                self.population, self.resources
            )
            self._weather_fx.update(dt, self.crisis)
            for msg in self.crisis.new_messages:
                self.ui.hud.push_message(msg)

            # Лор
            self.lab.check_day_unlocks(self.day.day)
            has_lab = any(
                b.type.value == 'laboratory' and b.is_active
                for b in self.buildings._buildings.values()
            )
            has_energy = self.resources.amount(
                __import__('systems.resources', fromlist=['Resource']).Resource.ENERGY
            ) > 0
            self.lab.tick(TICK_RATE, has_lab, has_energy)
            for log_id in self.lab.new_discoveries:
                from systems.lore import LOG_BY_ID
                log = LOG_BY_ID.get(log_id)
                if log:
                    self.ui.hud.push_message(
                        f'// LOG DISCOVERED: {log.title} //'
                    )

            # Передаємо модифікатори роверу
            self.rover.speed_mod_external = self._mods.rover_speed

            # Повідомлення від популяції
            for msg in self.population.events[-1:]:
                self.ui.hud.push_message(msg)

            self._tick_timer += dt
            if self._tick_timer >= TICK_RATE:
                self._tick_timer -= TICK_RATE
                self.resources.snapshot()
                workers_map = self.population.assign_workers(self.buildings._buildings)
                self.buildings.tick(
                    self.resources, self.world, TICK_RATE,
                    workers_map, self._mods.solar_efficiency
                )
                self.population.tick(self.resources, TICK_RATE)
                # Factory tick
                has_factory = any(
                    b.type.value == 'factory' and b.is_active
                    for b in self.buildings._buildings.values()
                )
                if has_factory:
                    self.factory.tick(
                        self.buildings.blueprint_inv, TICK_RATE,
                        has_power=self.resources.amount(__import__('systems.resources', fromlist=['Resource']).Resource.ENERGY) > 0,
                        has_workers=True
                    )
                # Jammer activation processing
                if self._jammer_ui.tick(
                    TICK_RATE, self.resources, self.crisis,
                    self.buildings, self.lab
                ):
                    if self.lab.secret_ending_unlocked():
                        self._go_ending('secret')
                    else:
                        self._go_ending('good')
                    return

                self.resources.calc_delta()

        elif self.state == STATE_GAME_OVER:
            self._game_over.update(dt)

        elif self.state == STATE_ENDING:
            self._ending.update(dt)

    # ---------------------------------------------------------------- render

    def render(self):
        if self.state == STATE_MAIN_MENU:
            self._main_menu.render(self.screen)

        elif self.state == STATE_PAUSE:
            # Спочатку рендеримо гру, потім overlay паузи
            self._render_game()
            self._pause_menu.render(self.screen)

        elif self.state == STATE_GAME:
            self._render_game()

        elif self.state == STATE_GAME_OVER:
            self._render_game()
            self._game_over.render(self.screen)

        elif self.state == STATE_ENDING:
            self._ending.render(self.screen)

    def _render_game(self):
        self.screen.fill((10, 5, 2))
        self.world.render(self.screen, self.camera)
        self.buildings.render(self.screen, self.camera, self.world)
        self.rover.render(self.screen, self.camera)
        self._render_debug_coords()
        self._render_fragment_hint()
        # Рендер UI: Hud, панелі ресурсів, популяції, інвентар
        self.ui.render(
            res=self.resources,
            pop=self.population,
            bp_inv=self.buildings.blueprint_inv,
            day=self.day,
            crisis=self.crisis
        )
        # Рендер лабораторії, фабрики, погоди, Jammer UI, фрагментів
        self._lab_ui.render(
            self.screen, self.lab,
            any(b.type.value == 'laboratory' and b.is_active
                for b in self.buildings._buildings.values())
        )
        self._factory_ui.render(
            self.screen, self.factory,
            self.buildings.blueprint_inv, self.resources
        )
        self._weather_fx.render(self.screen, self._mods, self.crisis)
        self._jammer_ui.render(self.screen)
        self.fragments.render(self.screen, self.camera, self.world)

    def _render_fragment_hint(self):
        if not self.rover:
            return
        rover_tx = int(self.rover.x // self.world.TILE_SIZE)
        rover_ty = int(self.rover.y // self.world.TILE_SIZE)
        frag = self.fragments.nearby_fragment(rover_tx, rover_ty)
        if frag:
            from ui import fonts
            sw, sh = self.screen.get_size()
            hint = fonts.get(11, bold=True).render(
                f'[ R ] RECOVER {frag.label}', True, frag.color
            )
            self.screen.blit(hint, (
                sw // 2 - hint.get_width() // 2,
                sh // 2 + 40
            ))

    def _render_debug_coords(self):
        tx = int(self.rover.x // self.world.TILE_SIZE)
        ty = int(self.rover.y // self.world.TILE_SIZE)
        font = pygame.font.SysFont("consolas", 13)
        text = font.render(f"Rover tile: ({tx}, {ty})", True, (160, 160, 140))
        self.screen.blit(text, (10, 52))
