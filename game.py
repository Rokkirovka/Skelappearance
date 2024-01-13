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
moving = False
your_turn = False


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
        self.pers_turning = 0

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
    def __init__(self, side, position, hero, skills, hp=1000, damage=100, armor=5, speed=10):
        super().__init__(all_sprites)
        self.radius = 40
        self.hp = hp
        self.damage = damage
        self.armor = armor
        self.speed = speed
        self.position = position
        self.side = side
        self.hero = hero
        self.skills = skills
        self.image = pygame.Surface((2 * self.radius, 2 * self.radius), pygame.SRCALPHA, 32)
        self.rect = None

    def attack(self, skill, target):
        target.hp -= self.damage * skill.coefficient
        if target.side:
            bar = scene.heroes_bars[target.position]
        else:
            bar = scene.enemies_bars[target.position]
        bar.hp -= self.damage * skill.coefficient

    def update(self, *args):
        if self.hp <= 0:
            self.kill()
            if self in scene.heroes:
                scene.heroes[scene.heroes.index(self)] = None
            else:
                scene.enemies[scene.enemies.index(self)] = None

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
            if self in scene.heroes_bars:
                scene.heroes_bars[scene.heroes_bars.index(self)] = None
            else:
                scene.enemies_bars[scene.enemies_bars.index(self)] = None

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
        global your_turn, moving
        if your_turn:
            if scene.selected is not None and args and args[0].type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(args[0].pos):
                scene.heroes[1].attack(self, scene.enemies[scene.selected])
                your_turn = False
                scene.pers_turning += 1
                moving = False


strike = Skill(1, True, False)


def next_turn():
    global moving, your_turn
    moving = True
    if scene.pers_turning % 6 < 3:
        active = scene.heroes[scene.pers_turning % 3]
    else:
        active = scene.enemies[scene.pers_turning % 3]
    if active is not None:
        if not active.hero:
            if active.side:
                targets = [x for x in scene.enemies if x is not None]
            else:
                targets = [x for x in scene.heroes if x is not None]
            target = random.choice(targets)
            technique = random.choice(active.skills)
            active.attack(technique, target)
            scene.pers_turning += 1
            moving = False
        else:
            your_turn = True
    else:
        scene.pers_turning += 1
        moving = False


def terminate():
    pygame.quit()
    sys.exit()


scene = Scene()
scene.add_character(Person(True, 0, False, [strike]))
sonny = Person(True, 1, True, [strike], 1500)
scene.add_character(sonny)
scene.add_character(Person(True, 2, False, [strike]))
scene.add_character(Person(False, 0, False, [strike]))
scene.add_character(Person(False, 1, False, [strike]))
scene.add_character(Person(False, 2, False, [strike]))


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
    if not moving:
        scene.selected = None
        next_turn()
    clock.tick(FPS)
