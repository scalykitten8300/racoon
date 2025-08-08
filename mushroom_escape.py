import os
import random
import pygame

WIDTH, HEIGHT = 640, 480
FPS = 60
MUSHROOM_SPEED = 5
CHEESE_SPEED = 3


def create_mushroom_surface():
    surface = pygame.Surface((40, 40), pygame.SRCALPHA)
    # Draw body
    pygame.draw.ellipse(surface, (255, 255, 255), (10, 20, 20, 20))
    # Draw blonde bowl cut (yellow circle on top)
    pygame.draw.circle(surface, (255, 255, 0), (20, 10), 10)
    return surface


def create_cheese_surface():
    surface = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.polygon(surface, (255, 165, 0), [(0, 0), (40, 20), (0, 40)])
    return surface


def main(test_mode=False):
    pygame.init()
    if os.environ.get("SDL_VIDEODRIVER") == "dummy":
        # Avoid window when running headless tests
        pygame.display.set_mode((1, 1))
    else:
        pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Mushroom Escape")

    screen = pygame.display.get_surface()
    mushroom = create_mushroom_surface()
    mushroom_rect = mushroom.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    cheese = create_cheese_surface()
    cheese_rect = cheese.get_rect(center=(random.randint(0, WIDTH), random.randint(0, HEIGHT)))

    clock = pygame.time.Clock()
    running = True
    frame_count = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            mushroom_rect.x -= MUSHROOM_SPEED
        if keys[pygame.K_RIGHT]:
            mushroom_rect.x += MUSHROOM_SPEED
        if keys[pygame.K_UP]:
            mushroom_rect.y -= MUSHROOM_SPEED
        if keys[pygame.K_DOWN]:
            mushroom_rect.y += MUSHROOM_SPEED

        if cheese_rect.x < mushroom_rect.x:
            cheese_rect.x += CHEESE_SPEED
        elif cheese_rect.x > mushroom_rect.x:
            cheese_rect.x -= CHEESE_SPEED
        if cheese_rect.y < mushroom_rect.y:
            cheese_rect.y += CHEESE_SPEED
        elif cheese_rect.y > mushroom_rect.y:
            cheese_rect.y -= CHEESE_SPEED

        if mushroom_rect.colliderect(cheese_rect):
            running = False

        screen.fill((0, 0, 0))
        screen.blit(mushroom, mushroom_rect)
        screen.blit(cheese, cheese_rect)
        pygame.display.flip()
        clock.tick(FPS)

        frame_count += 1
        if test_mode and frame_count > 10:
            break

    pygame.quit()


if __name__ == "__main__":
    test_mode = bool(os.environ.get("HEADLESS_TEST"))
    main(test_mode=test_mode)
