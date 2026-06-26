from __future__ import annotations
import pygame
import random
import math
import sys
import colorsys
from logic import Ball, GameState

# ── НАСТРОЙКИ ─────────────────────────────────────────────────────
BALL_COUNT = 10        # стартовое количество шариков
WIDTH, HEIGHT = 900, 650
FPS = 60
MAX_THROW_SPEED = 1500  # пикс/сек — ограничение скорости броска
# ──────────────────────────────────────────────────────────────────

BG_COLOR   = (255, 255, 255)
TEXT_COLOR = (120, 120, 140)
HINT_COLOR = (180, 180, 200)
DEL_COLOR  = (210, 40, 40)


def saturated_color() -> tuple:
    h = random.random()
    s = random.uniform(0.75, 1.0)
    v = random.uniform(0.75, 1.0)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def make_ball(width: int, height: int) -> Ball:
    r = random.randint(15, 28)
    angle = random.uniform(0, 2 * math.pi)
    speed = random.uniform(80, 200)
    return Ball(
        x=random.uniform(r + 85, width - r - 10),
        y=random.uniform(r + 10, height - r - 90),
        color=saturated_color(),
        radius=r,
        vx=math.cos(angle) * speed,
        vy=math.sin(angle) * speed,
    )


def draw_ball(surf: pygame.Surface, ball: Ball) -> None:
    cx, cy, r = int(ball.x), int(ball.y), int(ball.radius)

    # тень
    sh = pygame.Surface((r * 2 + 14, r * 2 + 14), pygame.SRCALPHA)
    pygame.draw.circle(sh, (0, 0, 0, 35), (r + 7, r + 9), r)
    surf.blit(sh, (cx - r - 7, cy - r - 7))

    # тело
    pygame.draw.circle(surf, ball.color, (cx, cy), r)

    # блик
    hl_r = max(3, r // 3)
    hl = pygame.Surface((hl_r * 2, hl_r * 2), pygame.SRCALPHA)
    pygame.draw.circle(hl, (255, 255, 255, 145), (hl_r, hl_r), hl_r)
    surf.blit(hl, (cx - r // 3 - hl_r, cy - r // 3 - hl_r))


def draw_delete_zone(surf: pygame.Surface, zone, pulse: float,
                     font: pygame.font.Font) -> None:
    alpha = int(38 + 28 * math.sin(pulse))
    zs = pygame.Surface((int(zone.width), int(zone.height)), pygame.SRCALPHA)
    zs.fill((255, 55, 55, alpha))
    surf.blit(zs, (int(zone.x), int(zone.y)))
    pygame.draw.rect(surf, DEL_COLOR,
                     (int(zone.x), int(zone.y), int(zone.width), int(zone.height)),
                     2, border_radius=10)
    label = font.render("[ УДАЛИТЬ ]", True, DEL_COLOR)
    surf.blit(label, (
        int(zone.x + (zone.width - label.get_width()) / 2),
        int(zone.y + (zone.height - label.get_height()) / 2),
    ))


def draw_inventory_panel(surf: pygame.Surface, inventory: list,
                         font: pygame.font.Font) -> None:
    panel_w = 68
    ps = pygame.Surface((panel_w, HEIGHT), pygame.SRCALPHA)
    ps.fill((232, 234, 250, 210))
    surf.blit(ps, (0, 0))

    title = font.render("ЗАПАС", True, (90, 95, 135))
    surf.blit(title, ((panel_w - title.get_width()) // 2, 10))

    y = 32
    for ball in inventory:
        r = min(int(ball.radius), 20)
        if y + r * 2 + 8 > HEIGHT:
            break
        pygame.draw.circle(surf, ball.color, (panel_w // 2, y + r), r)
        y += r * 2 + 10


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Шарики")
    clock = pygame.time.Clock()

    font_ui    = pygame.font.SysFont("Arial", 13, bold=True)
    font_small = pygame.font.SysFont("Arial", 12)

    game = GameState(WIDTH, HEIGHT)
    for _ in range(BALL_COUNT):
        game.add_ball(make_ball(WIDTH, HEIGHT))

    mouse_prev = pygame.mouse.get_pos()
    mouse_vel  = (0.0, 0.0)
    pulse_t    = 0.0

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        mx, my = pygame.mouse.get_pos()
        pulse_t += dt * 3.0

        if dt > 0:
            mouse_vel = ((mx - mouse_prev[0]) / dt,
                         (my - mouse_prev[1]) / dt)
        mouse_prev = (mx, my)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # ЛКМ: всосать шарик в пул
                game.suck(mx, my)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                # ПКМ: выпустить последний шарик из пула со скоростью мыши
                if game.inventory:
                    vx = clamp(mouse_vel[0], -MAX_THROW_SPEED, MAX_THROW_SPEED)
                    vy = clamp(mouse_vel[1], -MAX_THROW_SPEED, MAX_THROW_SPEED)
                    game.spit(mx, my, vx, vy)

        game.update(dt)

        # ── Отрисовка ──────────────────────────────────────────────
        screen.fill(BG_COLOR)

        draw_delete_zone(screen, game.delete_zone, pulse_t, font_ui)

        for ball in game.balls:
            draw_ball(screen, ball)

        if game.inventory:
            draw_inventory_panel(screen, game.inventory, font=font_small)

        # HUD — счётчик
        hud = font_small.render(
            f"Шариков: {len(game.balls)}   В запасе: {len(game.inventory)}",
            True, TEXT_COLOR,
        )
        screen.blit(hud, (WIDTH - hud.get_width() - 12, 10))

        # Подсказка
        hint = font_small.render(
            "ЛКМ на шарик — в пул   |   ПКМ — выпустить из пула",
            True, HINT_COLOR,
        )
        screen.blit(hint, ((WIDTH - hint.get_width()) // 2, HEIGHT - 22))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
