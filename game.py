import os
import sys
import pygame
import random

pygame.init()
size = width, height = 1200, 800
screen = pygame.display.set_mode(size)
FPS = 50
clock = pygame.time.Clock()
all_sprites = pygame.sprite.Group()
font = pygame.font.SysFont('Arial', 40)
colors = {True: 'blue', False: 'red'}


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class Scene:
    def __init__(self):
        self.heroes = [None, None, None]
        self.heroes_bars = [None, None, None]

        self.enemies = [None, None, None]
        self.enemies_bars = [None, None, None]
        self.selected = None
        self.turning = 0

    def add_character(self, char):
        bar = HPBar(char.hp)
        if char.side:
            self.heroes[char.position] = char
            pygame.draw.circle(char.image, pygame.Color(colors[char.side]), (char.radius, char.radius), char.radius)
            char.rect = pygame.Rect(100, 400 + char.position * 120, 2 * char.radius, 2 * char.radius)

            self.heroes_bars[char.position] = bar
            pygame.draw.rect(bar.image, 'green', (2, 2, 246, 26))
            bar.rect = pygame.Rect(100, 40 + char.position * 40, 200, 20)

        else:
            self.enemies[char.position] = char
            pygame.draw.circle(char.image, pygame.Color(colors[char.side]), (char.radius, char.radius), char.radius)
            char.rect = pygame.Rect(1000, 400 + char.position * 120, 2 * char.radius, 2 * char.radius)

            self.enemies_bars[char.position] = bar
            pygame.draw.rect(bar.image, 'green', (2, 2, 246, 26))
            bar.rect = pygame.Rect(900, 40 + char.position * 40, 200, 20)


class Person(pygame.sprite.Sprite):
    def __init__(self, side, position, hero, hp=1000, damage=100, armor=5, speed=10):
        super().__init__(all_sprites)
        self.radius = 40
        self.hp = hp
        self.damage = damage
        self.armor = armor
        self.speed = speed
        self.position = position
        self.side = side
        self.hero = hero
        self.image = pygame.Surface((2 * self.radius, 2 * self.radius), pygame.SRCALPHA, 32)
        self.rect = None

    def attack(self, skill, target, bar):
        target.hp -= self.damage * skill.coefficient
        bar.hp -= self.damage * skill.coefficient

    def update(self, *args):
        if self.hp <= 0:
            self.kill()

        if args and args[0].type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(args[0].pos) and not self.side:
            scene.selected = scene.enemies.index(self)


class HPBar(pygame.sprite.Sprite):
    def __init__(self, hp):
        super().__init__(all_sprites)
        self.max_hp = hp
        self.hp = hp
        self.percent = 100
        self.image = pygame.Surface((250, 30))

    def update(self, *args):
        if self.hp <= 0:
            self.kill()

        self.percent = int(self.hp / self.max_hp * 100)
        pygame.draw.rect(self.image, 'red', (self.percent * 2.5, 2, 250 - self.percent * 2.5 - 2, 26))


class Skill(pygame.sprite.Sprite):
    def __init__(self, coefficient, to_enemy, to_hero, effect=None):
        super().__init__(all_sprites)
        self.coefficient = coefficient
        self.to_enemy = to_enemy
        self.to_hero = to_hero
        self.effect = effect
        self.image = pygame.Surface((50, 50))
        pygame.draw.rect(self.image, 'yellow', (2, 2, 46, 46))
        self.rect = pygame.Rect((575, 740, 50, 50))

    def update(self, *args):
        if scene.selected is not None and args and args[0].type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(args[0].pos):
            scene.heroes[1].attack(self, scene.enemies[scene.selected], scene.enemies_bars[scene.selected])


strike = Skill(1, True, False)


def next_turn():
    pass


def terminate():
    pygame.quit()
    sys.exit()


scene = Scene()
scene.add_character(Person(True, 0, False, 1000))
scene.add_character(Person(True, 1, True, 1500))
scene.add_character(Person(True, 2, False, 1000))
scene.add_character(Person(False, 0, False, 1000))
scene.add_character(Person(False, 1, False, 1000))
scene.add_character(Person(False, 2, False, 1000))


while True:
    for event in pygame.event.get():
        all_sprites.update(event)
        if event.type == pygame.QUIT:
            terminate()
    pygame.display.flip()
    screen.fill((255, 255, 255))
    pygame.draw.rect(screen, 'cyan', (0, 0, width, 300))
    pygame.draw.rect(screen, 'gray', (0, 300, width, height))
    all_sprites.draw(screen)
    next_turn()
    clock.tick(FPS)
