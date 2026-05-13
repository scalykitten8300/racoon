import os
import random
import pygame

WIDTH, HEIGHT = 640, 480
FPS = 60
MUSHROOM_SPEED = 5
BASE_CHEESE_SPEED = 2
MAX_CHEESE_SPEED = 7
SPAWN_INTERVAL = 5  # seconds between new cheese spawns
SPEED_INCREASE_INTERVAL = 10  # seconds between speed increases

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 220, 50)
ORANGE = (255, 140, 0)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
RED = (200, 50, 50)
GRAY = (180, 180, 180)
DARK_GRAY = (60, 60, 60)


def create_mushroom_surface():
    surface = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (240, 240, 240), (10, 20, 20, 20))
    pygame.draw.circle(surface, (255, 220, 50), (20, 14), 13)
    # eyes
    pygame.draw.circle(surface, BLACK, (15, 16), 2)
    pygame.draw.circle(surface, BLACK, (25, 16), 2)
    return surface


def create_cheese_surface():
    surface = pygame.Surface((36, 36), pygame.SRCALPHA)
    pygame.draw.polygon(surface, ORANGE, [(0, 0), (36, 18), (0, 36)])
    # holes
    pygame.draw.circle(surface, (200, 100, 0), (8, 12), 3)
    pygame.draw.circle(surface, (200, 100, 0), (8, 24), 3)
    return surface


def draw_text_centered(surface, text, font, color, y):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=(WIDTH // 2, y))
    surface.blit(rendered, rect)


def draw_grass_background(surface):
    surface.fill((34, 100, 34))
    for i in range(0, WIDTH, 40):
        for j in range(0, HEIGHT, 40):
            shade = random.randint(-10, 10)
            r = max(0, min(255, 34 + shade))
            g = max(0, min(255, 100 + shade))
            b = max(0, min(255, 34 + shade))
            pygame.draw.rect(surface, (r, g, b), (i, j, 40, 40))


def make_background(width, height):
    bg = pygame.Surface((width, height))
    rng = random.Random(42)
    for i in range(0, width, 40):
        for j in range(0, height, 40):
            shade = rng.randint(-15, 15)
            r = max(0, min(255, 30 + shade))
            g = max(0, min(255, 110 + shade))
            b = max(0, min(255, 30 + shade))
            pygame.draw.rect(bg, (r, g, b), (i, j, 40, 40))
    return bg


class Cheese:
    def __init__(self, surface, speed):
        self.surface = surface
        edge = random.choice(["top", "bottom", "left", "right"])
        if edge == "top":
            x, y = random.randint(0, WIDTH), -20
        elif edge == "bottom":
            x, y = random.randint(0, WIDTH), HEIGHT + 20
        elif edge == "left":
            x, y = -20, random.randint(0, HEIGHT)
        else:
            x, y = WIDTH + 20, random.randint(0, HEIGHT)
        self.rect = surface.get_rect(center=(x, y))
        self.speed = speed

    def update(self, target_rect):
        dx = target_rect.centerx - self.rect.centerx
        dy = target_rect.centery - self.rect.centery
        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist > 0:
            self.rect.x += int(self.speed * dx / dist)
            self.rect.y += int(self.speed * dy / dist)


def show_title_screen(screen, font_big, font_med, mushroom_surf, cheese_surf):
    clock = pygame.time.Clock()
    bg = make_background(WIDTH, HEIGHT)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return True

        screen.blit(bg, (0, 0))
        screen.blit(mushroom_surf, mushroom_surf.get_rect(center=(WIDTH // 2 - 30, HEIGHT // 2 - 20)))
        screen.blit(cheese_surf, cheese_surf.get_rect(center=(WIDTH // 2 + 30, HEIGHT // 2 - 20)))
        draw_text_centered(screen, "Mushroom Escape", font_big, YELLOW, HEIGHT // 4)
        draw_text_centered(screen, "Dodge the cheese as long as you can!", font_med, WHITE, HEIGHT // 2 + 40)
        draw_text_centered(screen, "Arrow keys to move", font_med, GRAY, HEIGHT // 2 + 75)
        draw_text_centered(screen, "Press SPACE or ENTER to start", font_med, WHITE, HEIGHT * 3 // 4)
        pygame.display.flip()
        clock.tick(FPS)


def show_game_over(screen, font_big, font_med, score, high_score, bg):
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False

        screen.blit(bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        draw_text_centered(screen, "GAME OVER", font_big, RED, HEIGHT // 4)
        draw_text_centered(screen, f"You survived: {score:.1f}s", font_med, WHITE, HEIGHT // 2 - 20)
        if score >= high_score:
            draw_text_centered(screen, "New High Score!", font_med, YELLOW, HEIGHT // 2 + 20)
        else:
            draw_text_centered(screen, f"Best: {high_score:.1f}s", font_med, GRAY, HEIGHT // 2 + 20)
        draw_text_centered(screen, "SPACE / ENTER to play again", font_med, WHITE, HEIGHT * 3 // 4 - 10)
        draw_text_centered(screen, "ESC to quit", font_med, GRAY, HEIGHT * 3 // 4 + 25)
        pygame.display.flip()
        clock.tick(FPS)


def run_game(screen, font_med, mushroom_surf, cheese_surf, bg):
    mushroom_rect = mushroom_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    cheeses = [Cheese(cheese_surf, BASE_CHEESE_SPEED)]

    clock = pygame.time.Clock()
    start_ticks = pygame.time.get_ticks()
    last_spawn = 0
    last_speed_up = 0
    cheese_speed = BASE_CHEESE_SPEED
    running = True

    while running:
        dt = clock.tick(FPS)
        elapsed = (pygame.time.get_ticks() - start_ticks) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return elapsed, True  # signal quit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return elapsed, False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            mushroom_rect.x -= MUSHROOM_SPEED
        if keys[pygame.K_RIGHT]:
            mushroom_rect.x += MUSHROOM_SPEED
        if keys[pygame.K_UP]:
            mushroom_rect.y -= MUSHROOM_SPEED
        if keys[pygame.K_DOWN]:
            mushroom_rect.y += MUSHROOM_SPEED

        # Clamp mushroom inside screen
        mushroom_rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

        # Spawn new cheese every SPAWN_INTERVAL seconds
        if elapsed - last_spawn >= SPAWN_INTERVAL:
            cheeses.append(Cheese(cheese_surf, cheese_speed))
            last_spawn = elapsed

        # Increase speed every SPEED_INCREASE_INTERVAL seconds
        if elapsed - last_speed_up >= SPEED_INCREASE_INTERVAL:
            cheese_speed = min(cheese_speed + 0.5, MAX_CHEESE_SPEED)
            for c in cheeses:
                c.speed = min(c.speed + 0.5, MAX_CHEESE_SPEED)
            last_speed_up = elapsed

        for c in cheeses:
            c.update(mushroom_rect)
            if mushroom_rect.colliderect(c.rect):
                running = False

        # Draw
        screen.blit(bg, (0, 0))
        for c in cheeses:
            screen.blit(c.surface, c.rect)
        screen.blit(mushroom_surf, mushroom_rect)

        # HUD
        score_surf = font_med.render(f"Time: {elapsed:.1f}s  |  Chasers: {len(cheeses)}", True, WHITE)
        screen.blit(score_surf, (8, 8))

        pygame.display.flip()

    return elapsed, False


def main(test_mode=False):
    pygame.init()
    if os.environ.get("SDL_VIDEODRIVER") == "dummy":
        pygame.display.set_mode((1, 1))
    else:
        pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Mushroom Escape")

    screen = pygame.display.get_surface()

    if test_mode:
        # Minimal headless run — just check startup and a few frames
        mushroom_surf = create_mushroom_surface()
        cheese_surf = create_cheese_surface()
        mushroom_rect = mushroom_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        cheeses = [Cheese(cheese_surf, BASE_CHEESE_SPEED)]
        clock = pygame.time.Clock()
        for _ in range(15):
            for event in pygame.event.get():
                pass
            for c in cheeses:
                c.update(mushroom_rect)
            screen.fill(BLACK)
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()
        return

    font_big = pygame.font.SysFont(None, 56)
    font_med = pygame.font.SysFont(None, 30)
    mushroom_surf = create_mushroom_surface()
    cheese_surf = create_cheese_surface()
    bg = make_background(WIDTH, HEIGHT)

    high_score = 0.0

    while True:
        if not show_title_screen(screen, font_big, font_med, mushroom_surf, cheese_surf):
            break

        score, quit_requested = run_game(screen, font_med, mushroom_surf, cheese_surf, bg)
        if score > high_score:
            high_score = score

        if quit_requested:
            break

        if not show_game_over(screen, font_big, font_med, score, high_score, bg):
            break

    pygame.quit()


if __name__ == "__main__":
    test_mode = bool(os.environ.get("HEADLESS_TEST"))
    main(test_mode=test_mode)
