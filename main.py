import pygame
from core.game import Game

def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("MARS: R-ARK PROTOCOL")
    clock = pygame.time.Clock()

    game = Game(screen)

    while game.running:
        dt = clock.tick(60) / 1000.0
        game.handle_events()
        game.update(dt)
        game.render()
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
