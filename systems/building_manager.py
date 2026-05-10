from __future__ import annotations
import pygame
import math
import random
from entities.building import (
    Building, BuildingType, BuildingState,
    BUILDING_DEFS, INVENTORY_ORDER,
)
from systems.resources import ResourceSystem, Resource
from world.world import World
from core.camera import Camera
from systems.construction import ConstructionQueue
from systems.population import BUILDING_WORKERS, BUILDING_MIN_POP, PopulationManager
from systems.factory import BlueprintInventory

ICON_PATH    = "assets/textures/buildings/{}.png"
ICON_SIZE    = 56
GHOST_ALPHA  = 160
PLACE_RADIUS = 3

REACTOR_OUTPUT   = 18.0   # energy/tick
BATTERY_CAPACITY = 150.0  # додаткова ємність
BATTERY_CHARGE_RATE  = 3.0  # energy/tick зарядка
BATTERY_DISCHARGE_RATE = 6.0  # energy/tick розрядка при потребі


# ── Частинка диму ────────────────────────────────────────────────────────────
class _SmokeParticle:
    def __init__(self, x: float, y: float):
        self.x   = x + random.uniform(-6, 6)
        self.y   = y
        self.vy  = random.uniform(-18, -8)
        self.vx  = random.uniform(-4, 4)
        self.r   = random.uniform(3, 6)
        self.age = 0.0
        self.life = random.uniform(0.8, 1.6)
        self.alpha = random.randint(120, 200)

    @property
    def dead(self): return self.age >= self.life

    def update(self, dt: float):
        self.x   += self.vx * dt
        self.y   += self.vy * dt
        self.age += dt
        self.r   += 1.2 * dt

    def render(self, surf: pygame.Surface):
        a = int(self.alpha * (1 - self.age / self.life))
        if a <= 0 or self.r < 1:
            return
        s = pygame.Surface((int(self.r * 2 + 2),) * 2, pygame.SRCALPHA)
        pygame.draw.circle(s, (160, 140, 130, a),
                           (int(self.r + 1), int(self.r + 1)), int(self.r))
        surf.blit(s, (int(self.x - self.r), int(self.y - self.r)))


# ── Менеджер будівель ─────────────────────────────────────────────────────────
class BuildingManager:

    def __init__(self):
        self._buildings:  dict[tuple[int,int], Building] = {}
        self._icons:      dict[BuildingType, pygame.Surface] = {}
        self._ghost_type: BuildingType | None = None
        self._ghost_tx    = 0
        self._ghost_ty    = 0
        self._ghost_valid = False
        self._smoke:      list[_SmokeParticle] = []
        self._smoke_timer: dict[tuple[int,int], float] = {}
        self._construction  = ConstructionQueue()
        self._workers_ok:   dict[tuple[int,int], bool] = {}
        self.blueprint_inv  = BlueprintInventory()
        self._battery_charge: dict[tuple[int,int], float] = {}  # поточний заряд

    # ---------------------------------------------------------------- icons

    def load_icons(self):
        for bt in BuildingType:
            path = ICON_PATH.format(bt.value)
            try:
                img = pygame.image.load(path).convert_alpha()
                self._icons[bt] = pygame.transform.scale(img, (ICON_SIZE, ICON_SIZE))
            except Exception:
                surf = pygame.Surface((ICON_SIZE, ICON_SIZE), pygame.SRCALPHA)
                # Заглушка з кольором і літерою
                colors = {
                    BuildingType.HUB:        (255, 255, 255),
                    BuildingType.HABITAT:    (180, 180, 220),
                    BuildingType.GREENHOUSE: (80,  200, 80),
                    BuildingType.SOLAR:      (80,  120, 220),
                    BuildingType.EXTRACTOR:  (180, 120, 60),
                    BuildingType.STORAGE:    (160, 140, 100),
                    BuildingType.FACTORY:    (200, 100, 60),
                    BuildingType.LABORATORY: (120, 180, 220),
                    BuildingType.JAMMER:     (180, 80,  220),
                    BuildingType.BATTERY:    (80,  180, 220),
                    BuildingType.REACTOR:    (130, 220, 100),
                }
                c = colors.get(bt, (150, 150, 150))
                pygame.draw.rect(surf, (*c, 200),
                                 pygame.Rect(3, 3, ICON_SIZE-6, ICON_SIZE-6))
                pygame.draw.rect(surf, (0, 0, 0, 255),
                                 pygame.Rect(3, 3, ICON_SIZE-6, ICON_SIZE-6), 2)
                font = pygame.font.SysFont("consolas", 20, bold=True)
                lbl  = font.render(bt.value[0].upper(), True, (0, 0, 0))
                surf.blit(lbl, lbl.get_rect(
                    center=(ICON_SIZE//2, ICON_SIZE//2)))
                self._icons[bt] = surf

    # ---------------------------------------------------------------- ghost

    def start_placement(self, bt: BuildingType):
        self._ghost_type = bt

    def cancel_placement(self):
        self._ghost_type = None

    @property
    def is_placing(self) -> bool:
        return self._ghost_type is not None

    def update_ghost(self, mx, my, world, camera, rover_tx, rover_ty):
        if not self.is_placing:
            return
        tx, ty = world.screen_to_tile(mx, my, camera)
        tile   = world.get_tile(tx, ty)
        dist   = max(abs(tx - rover_tx), abs(ty - rover_ty))
        self._ghost_tx    = tx
        self._ghost_ty    = ty
        self._ghost_valid = (
            tile is not None
            and tile.passable
            and (tx, ty) not in self._buildings
            and dist <= PLACE_RADIUS
        )

    def try_place(
        self,
        resources: ResourceSystem,
        world: World,
        population: PopulationManager,
        free_workers: int = 0,
    ) -> bool:
        if not self.is_placing or not self._ghost_valid:
            return False
        bt   = self._ghost_type
        defn = BUILDING_DEFS[bt]
        # Перевірка мінімальної популяції
        if not population.can_unlock(bt.value):
            return False
        # Перевірка blueprint
        if not self.blueprint_inv.can_build(bt.value):
            return False
        if not resources.consume_many(defn.cost):
            return False
        self.blueprint_inv.consume_for_build(bt.value)
        b = Building(type=bt, tx=self._ghost_tx, ty=self._ghost_ty)
        self._buildings[(self._ghost_tx, self._ghost_ty)] = b
        world.grid[self._ghost_ty][self._ghost_tx].building = bt.value
        if defn.gives_storage:
            resources.add_storage(1)
        self._construction.add(b, free_workers)
        self._update_connectivity(world)
        self.cancel_placement()
        return True

    # ---------------------------------------------------------------- tick

    def tick(self, resources: ResourceSystem, world: World, dt: float,
             workers_map: dict | None = None, mods_solar: float = 1.0):
        # Будівництво
        self._construction.tick(self._buildings, dt)
        # Workers map з PopulationManager
        if workers_map is not None:
            self._workers_ok = workers_map

        for (tx, ty), b in self._buildings.items():
            b.update_anim(dt)
            if b.state in (
                BuildingState.DISCONNECTED,
                BuildingState.DAMAGED,
                BuildingState.CONSTRUCTING,
            ):
                continue
            # Перевірка workers
            if not self._workers_ok.get((tx, ty), True):
                b.state = BuildingState.INACTIVE
                continue
            defn = b.definition
            energy_cost = defn.consumes.get(Resource.ENERGY, 0.0) * dt
            if energy_cost > 0 and not resources.consume(Resource.ENERGY, energy_cost):
                b.state = BuildingState.INACTIVE
                continue
            if b.type != BuildingType.REACTOR:
                other_costs = {
                    r: rate * dt for r, rate in defn.consumes.items()
                    if r != Resource.ENERGY
                }
                if other_costs and not resources.can_afford(other_costs):
                    b.state = BuildingState.NO_RESOURCE
                    continue
                for r, amount in other_costs.items():
                    resources.consume(r, amount)
            for r, rate in defn.produces.items():
                resources.add(r, rate * dt)

            tile = world.get_tile(b.tx, b.ty)
            if tile:
                if b.type == BuildingType.SOLAR:
                    solar_mod = tile.solar_modifier * mods_solar
                    resources.add(
                        Resource.ENERGY,
                        ResourceSystem.solar_output(solar_mod, dt)
                    )
                elif b.type == BuildingType.REACTOR:
                    # Реактор: споживає уран, генерує енергію
                    if resources.consume(Resource.URANIUM,
                                         BUILDING_DEFS[BuildingType.REACTOR]
                                         .consumes[Resource.URANIUM] * dt):
                        resources.add(Resource.ENERGY, REACTOR_OUTPUT * dt)
                    else:
                        b.state = BuildingState.NO_RESOURCE
                elif b.type == BuildingType.BATTERY:
                    # Батарея: заряджається коли є надлишок, розряджається при потребі
                    key = (b.tx, b.ty)
                    charge = self._battery_charge.get(key, 0.0)
                    energy_ratio = resources.ratio(Resource.ENERGY)
                    if energy_ratio > 0.8 and charge < BATTERY_CAPACITY:
                        # Заряджаємо
                        taken = min(BATTERY_CHARGE_RATE * dt,
                                    BATTERY_CAPACITY - charge)
                        if resources.consume(Resource.ENERGY, taken):
                            charge += taken
                    elif energy_ratio < 0.3 and charge > 0:
                        # Розряджаємо
                        give = min(BATTERY_DISCHARGE_RATE * dt, charge)
                        resources.add(Resource.ENERGY, give)
                        charge -= give
                    self._battery_charge[key] = charge
                elif b.type == BuildingType.EXTRACTOR:
                    for tile_res_name, richness in tile.resources.as_dict().items():
                        out_resource, out_amount = ResourceSystem.extractor_output(
                            tile_res_name, richness, dt
                        )
                        resources.add(out_resource, out_amount)
            # Відновлюємо стан якщо все добре
            if b.state in (BuildingState.INACTIVE, BuildingState.NO_RESOURCE):
                b.state = BuildingState.ACTIVE

        # Дим
        for key, b in self._buildings.items():
            if b.is_active and "smoke" in b.definition.fx:
                self._smoke_timer[key] = self._smoke_timer.get(key, 0.0) + dt
                if self._smoke_timer[key] >= 0.3:
                    self._smoke_timer[key] = 0.0
                    # Позиція диму буде розрахована при рендері
                    self._smoke.append(
                        _SmokeParticle(b.tx * 64 + 32, b.ty * 64 + 8)
                    )
        for p in self._smoke:
            p.update(dt)
        self._smoke = [p for p in self._smoke if not p.dead]

        self._update_connectivity(world)

    # ---------------------------------------------------------------- connectivity

    def _update_connectivity(self, world: World):
        hubs = [pos for pos, b in self._buildings.items() if b.type == BuildingType.HUB]
        if not hubs:
            for b in self._buildings.values():
                if b.type not in (BuildingType.SOLAR, BuildingType.EXTRACTOR, BuildingType.REACTOR):
                    b.state = BuildingState.DISCONNECTED
            return

        need_connection = {
            bt for bt in BuildingType
            if bt not in (BuildingType.SOLAR, BuildingType.EXTRACTOR, BuildingType.REACTOR, BuildingType.HUB)
        }

        for (tx, ty), b in self._buildings.items():
            if b.type not in need_connection:
                continue
            visited = set()
            queue = [(tx, ty)]
            connected = False
            while queue:
                cx, cy = queue.pop(0)
                if (cx, cy) in visited:
                    continue
                visited.add((cx, cy))
                if (cx, cy) in hubs:
                    connected = True
                    break
                if world.get_tile(cx, cy) is None or not world.get_tile(cx, cy).passable:
                    continue
                for nx, ny in [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]:
                    if (nx, ny) in self._buildings:
                        queue.append((nx, ny))
            if not connected:
                b.state = BuildingState.DISCONNECTED
            elif b.state == BuildingState.DISCONNECTED:
                b.state = BuildingState.ACTIVE

    # ---------------------------------------------------------------- query

    def get_at(self, tx: int, ty: int) -> Building | None:
        return self._buildings.get((tx, ty))

    def all(self):
        return self._buildings.values()

    # ---------------------------------------------------------------- render

    def render(self, screen: pygame.Surface, camera: Camera, world: World):
        ts     = world.TILE_SIZE
        offset = (ts - ICON_SIZE) // 2

        # Дим
        for p in self._smoke:
            sx, sy = camera.apply(p.x, p.y)
            # Тимчасово рендеримо відносно екрану
            p_screen_x = p.x - camera.x
            p_screen_y = p.y - camera.y
            _p = _SmokeParticle.__new__(_SmokeParticle)
            _p.x, _p.y = p_screen_x, p_screen_y
            _p.r, _p.age, _p.life, _p.alpha = p.r, p.age, p.life, p.alpha
            _p.render(screen)

        for (tx, ty), b in self._buildings.items():
            wx, wy = tx * ts, ty * ts
            if not camera.is_visible(wx, wy, ts):
                continue
            sx, sy = camera.apply(wx, wy)
            self._render_building(screen, b, sx, sy, offset, ts)

        self._render_ghost(screen, camera, world)

    def _render_building(
        self, screen, b: Building,
        sx: int, sy: int, offset: int, ts: int,
    ):
        icon = self._icons.get(b.type)
        t    = b._anim_time
        fx   = b.definition.fx

        # Стан overlay (неактивне — затемнення)
        if b.state == BuildingState.INACTIVE:
            dim = pygame.Surface((ts, ts), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 140))
            screen.blit(dim, (sx, sy))

        # Іконка
        if icon:
            render_icon = icon
            # Glow ефект (Greenhouse, Jammer) — мерехтіння яскравості
            if "glow" in fx and b.is_active:
                glow_alpha = int(180 + 60 * math.sin(t * 2.5))
                glow = pygame.Surface((ts, ts), pygame.SRCALPHA)
                c = (80, 220, 80) if b.type == BuildingType.GREENHOUSE else (180, 80, 220)
                pygame.draw.rect(glow, (*c, glow_alpha // 6), glow.get_rect())
                screen.blit(glow, (sx, sy))
            screen.blit(render_icon, (sx + offset, sy + offset))

        # Pulse (Hub) — зовнішнє кільце
        if "pulse" in fx and b.is_active:
            pulse_r = int(ts * 0.55 + 6 * math.sin(t * 1.8))
            pulse_a = int(120 + 80 * math.sin(t * 1.8))
            ps = pygame.Surface((pulse_r * 2 + 2,) * 2, pygame.SRCALPHA)
            pygame.draw.circle(ps, (255, 220, 80, pulse_a),
                               (pulse_r + 1, pulse_r + 1), pulse_r, 2)
            screen.blit(ps, (sx + ts // 2 - pulse_r - 1,
                              sy + ts // 2 - pulse_r - 1))

        # Blink (Laboratory, Habitat) — миготливий індикатор
        if "blink" in fx and b.is_active:
            blink_on = math.sin(t * 3.0) > 0
            if blink_on:
                c = (80, 180, 255) if b.type == BuildingType.LABORATORY else (255, 180, 80)
                pygame.draw.circle(screen, c,
                                   (sx + ts - 8, sy + 8), 4)

        # Прогрес-бар будівництва
        if b.state == BuildingState.CONSTRUCTING:
            progress = self._construction.progress(b.tx, b.ty, b.type)
            if progress is not None:
                bar_w = ts - 8
                pygame.draw.rect(screen, (30, 30, 30),
                                 pygame.Rect(sx + 4, sy + ts - 10, bar_w, 6))
                pygame.draw.rect(screen, (160, 200, 80),
                                 pygame.Rect(sx + 4, sy + ts - 10,
                                             int(bar_w * progress), 6))
                pygame.draw.rect(screen, (100, 140, 50),
                                 pygame.Rect(sx + 4, sy + ts - 10, bar_w, 6), 1)

        # Рамка стану
        pygame.draw.rect(screen, b.border_color,
                         pygame.Rect(sx, sy, ts, ts), 2)

        # Іконка стану (окрім ACTIVE)
        if b.state != BuildingState.ACTIVE:
            self._render_state_icon(screen, b.state, sx + ts - 18, sy + 2)

    def _render_state_icon(
        self, screen: pygame.Surface,
        state: BuildingState, x: int, y: int,
    ):
        icons = {
            BuildingState.INACTIVE:     ("!", (80, 80, 80)),
            BuildingState.NO_RESOURCE:  ("?", (220, 180, 30)),
            BuildingState.DISCONNECTED: ("X", (60, 120, 220)),
            BuildingState.DAMAGED:      ("!", (220, 60, 60)),
        }
        if state not in icons:
            return
        char, color = icons[state]
        font = pygame.font.SysFont("consolas", 13, bold=True)
        bg   = pygame.Surface((16, 16), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        screen.blit(bg, (x, y))
        lbl = font.render(char, True, color)
        screen.blit(lbl, (x + 3, y + 1))

    def _render_ghost(self, screen, camera, world):
        if not self.is_placing:
            return
        ts     = world.TILE_SIZE
        offset = (ts - ICON_SIZE) // 2
        sx, sy = camera.apply(self._ghost_tx * ts, self._ghost_ty * ts)

        color  = (80, 220, 80, 80) if self._ghost_valid else (220, 60, 60, 80)
        hl     = pygame.Surface((ts, ts), pygame.SRCALPHA)
        hl.fill(color)
        screen.blit(hl, (sx, sy))
        border = (80, 220, 80) if self._ghost_valid else (220, 60, 60)
        pygame.draw.rect(screen, border, pygame.Rect(sx, sy, ts, ts), 2)

        icon = self._icons.get(self._ghost_type)
        if icon:
            ghost = icon.copy()
            ghost.set_alpha(GHOST_ALPHA)
            screen.blit(ghost, (sx + offset, sy + offset))
