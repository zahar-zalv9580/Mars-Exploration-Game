class Camera:
    def __init__(self, screen_w: int, screen_h: int):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.x = 0.0
        self.y = 0.0

    def update(self, target_x: float, target_y: float, world):
        map_w = world.width * world.TILE_SIZE
        map_h = world.height * world.TILE_SIZE

        # центруємо камеру на ровері
        self.x = target_x - self.screen_w / 2
        self.y = target_y - self.screen_h / 2

        # обмеження по краях карти
        self.x = max(0, min(self.x, map_w - self.screen_w))
        self.y = max(0, min(self.y, map_h - self.screen_h))

    def apply(self, world_x: float, world_y: float) -> tuple[int, int]:
        """Конвертує світові координати в екранні."""
        return int(world_x - self.x), int(world_y - self.y)

    def is_visible(self, world_x: float, world_y: float, size: int) -> bool:
        """Перевіряє чи об'єкт потрапляє на екран."""
        sx, sy = self.apply(world_x, world_y)
        return (
            -size < sx < self.screen_w + size
            and -size < sy < self.screen_h + size
        )
