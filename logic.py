from __future__ import annotations
import math
import colorsys
import cmath


class Ball:
    def __init__(self, x: float, y: float, color: tuple,
                 radius: float = 20, vx: float = 0.0, vy: float = 0.0):
        self.x = x
        self.y = y
        self.color = color  # (R, G, B), каждый компонент 0–255
        self.radius = radius
        self.vx = vx
        self.vy = vy

    def move(self, dt: float, width: int, height: int) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx = abs(self.vx)
        elif self.x + self.radius > width:
            self.x = width - self.radius
            self.vx = -abs(self.vx)

        if self.y - self.radius < 0:
            self.y = self.radius
            self.vy = abs(self.vy)
        elif self.y + self.radius > height:
            self.y = height - self.radius
            self.vy = -abs(self.vy)

    def distance_to(self, other: Ball) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def overlaps(self, other: Ball) -> bool:
        return self.distance_to(other) < self.radius + other.radius

    def contains_point(self, px: float, py: float) -> bool:
        return math.hypot(self.x - px, self.y - py) < self.radius


class DeleteZone:
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def contains(self, ball: Ball) -> bool:
        return (self.x <= ball.x <= self.x + self.width and
                self.y <= ball.y <= self.y + self.height)


class GameState:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.balls: list[Ball] = []
        self.inventory: list[Ball] = []
        self.delete_zone = DeleteZone(
            x=width - 120, y=height - 80,
            width=110, height=70
        )
        # Пары шариков, которые сейчас касаются — чтобы не смешивать каждый кадр
        self._active_contacts: set[frozenset] = set()

    def add_ball(self, ball: Ball) -> None:
        self.balls.append(ball)

    def update(self, dt: float) -> None:
        """Основной игровой тик. dt — время в секундах с прошлого кадра."""
        for ball in self.balls:
            ball.move(dt, self.width, self.height)
        self._handle_collisions()
        self._check_delete_zone()

    def _handle_collisions(self) -> None:
        new_contacts: set[frozenset] = set()

        for i, a in enumerate(self.balls):
            for b in self.balls[i + 1:]:
                pair = frozenset((id(a), id(b)))
                if a.overlaps(b):
                    new_contacts.add(pair)
                    if pair not in self._active_contacts:
                        # Новое касание — смешиваем цвет один раз
                        mixed = mix_colors(a.color, b.color)
                        a.color = mixed
                        b.color = mixed

        self._active_contacts = new_contacts

    def _check_delete_zone(self) -> None:
        self.balls = [b for b in self.balls
                      if not self.delete_zone.contains(b)]

    def suck(self, mx: float, my: float) -> Ball | None:
        """Всосать шарик под курсором в инвентарь. Возвращает шарик или None."""
        for ball in self.balls:
            if ball.contains_point(mx, my):
                ball.vx = 0.0
                ball.vy = 0.0
                self.inventory.append(ball)
                self.balls.remove(ball)
                return ball
        return None

    def spit(self, x: float, y: float,
             vx: float = 0.0, vy: float = 0.0) -> Ball | None:
        """Выплюнуть последний шарик из инвентаря. Возвращает шарик или None."""
        if not self.inventory:
            return None
        ball = self.inventory.pop()
        ball.x = x
        ball.y = y
        ball.vx = vx
        ball.vy = vy
        self.balls.append(ball)
        return ball

    def spit_index(self, index: int, x: float, y: float,
                   vx: float = 0.0, vy: float = 0.0) -> Ball | None:
        """Выплюнуть шарик из инвентаря по индексу (0 — первый добавленный)."""
        if not (0 <= index < len(self.inventory)):
            return None
        ball = self.inventory.pop(index)
        ball.x = x
        ball.y = y
        ball.vx = vx
        ball.vy = vy
        self.balls.append(ball)
        return ball


def mix_colors(c1: tuple, c2: tuple) -> tuple:
    """
    Смешивает два цвета через HSV-пространство.

    Оттенки усредняются по цветовому кругу (без артефакта 0°/360°).
    Дополнительные цвета (противоположные на круге) дают тёмный результат,
    как настоящие краски — вместо белого или серого.
    """
    h1, s1, v1 = colorsys.rgb_to_hsv(c1[0] / 255, c1[1] / 255, c1[2] / 255)
    h2, s2, v2 = colorsys.rgb_to_hsv(c2[0] / 255, c2[1] / 255, c2[2] / 255)

    # Единичные векторы на цветовом круге — корректно обрабатывают переход 360°→0°
    avg = (cmath.exp(2j * math.pi * h1) + cmath.exp(2j * math.pi * h2)) / 2
    magnitude = abs(avg)

    if magnitude < 0.15:
        # Дополнительные цвета: результат тёмный и насыщенный (как смешение красок)
        h_mixed = h1
        s_mixed = 0.8
        v_mixed = (v1 + v2) / 2 * 0.4
    else:
        h_mixed = cmath.phase(avg) / (2 * math.pi)
        if h_mixed < 0:
            h_mixed += 1
        s_mixed = min(1.0, (s1 + s2) / 2 * 1.15)  # чуть усиливаем насыщенность
        v_mixed = (v1 + v2) / 2

    r, g, b = colorsys.hsv_to_rgb(h_mixed, s_mixed, v_mixed)
    return (int(r * 255), int(g * 255), int(b * 255))
