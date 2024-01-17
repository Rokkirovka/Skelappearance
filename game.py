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
background_sprites = pygame.sprite.Group()
characters_sprites = pygame.sprite.Group()
bars_sprites = pygame.sprite.Group()
skills_sprites = pygame.sprite.Group()
spells_sprites = pygame.sprite.Group()
main_sprites = pygame.sprite.Group()
bar_font = pygame.font.SysFont('Sans', 25)
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
        bar = HPBar(char.name, char.hp)
        if char.side:
            self.heroes[char.position] = char
            char.place = (200 - char.position * 40, height - 250 - 150 * (2 - char.position))

            self.heroes_bars[char.position] = bar
            bar.rect = pygame.Rect(100, 40 + char.position * 40, 250, 20)

        else:
            self.enemies[char.position] = char
            char.place = (width - 300 + char.position * 40, height - 250 - 150 * (2 - char.position))

            self.enemies_bars[char.position] = bar
            bar.rect = pygame.Rect(width - 350, 40 + char.position * 40, 250, 20)
        char.rect.left = char.place[0]
        char.rect.top = char.place[1]


class Person(pygame.sprite.Sprite):
    def __init__(self, name, sheet, side, position, hero, skills, hp=1000, magic=100, damage=100, armor=5):
        super().__init__(all_sprites, characters_sprites)
        self.frames = []
        self.cut_sheet(pygame.transform.scale(sheet, (960, 1920)), 10, 10)
        self.radius = 40
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.magic = magic
        self.damage = damage
        self.armor = armor
        self.position = position
        self.side = side
        self.hero = hero
        self.skills = skills
        self.cur_image = 0
        self.image = self.frames[self.cur_image]
        self.place = None
        self.update_points = 0

        self.target = None
        self.cur_skill = None

        self.moving_x = 0
        self.moving_y = 0
        self.iteration = 0

        self.forward_move = False
        self.backing = False
        self.attacking = False
        self.getting_damage = False
        self.helping = False
        self.shooting = False

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(width, 0, sheet.get_width() // columns, sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j + 50)
                self.frames.append(sheet.subsurface(pygame.Rect(frame_location, (self.rect.size[0], self.rect.size[1] - 50))))

    def strategy(self):
        medicinal = [x for x in self.skills if x.meaning == 'help']
        if medicinal:
            for person in sorted([x for x in (scene.heroes if self.side else scene.enemies) if x is not None], key=lambda x: x.hp):
                if person.hp / person.max_hp < random.random():
                    return person, random.choice(medicinal)
        crippling = [x for x in self.skills if x.meaning in ['closed', 'ranged']]
        if random.random() < 0.3:
            return random.choice([x for x in (scene.enemies if self.side else scene.heroes) if x is not None]), random.choice(crippling)
        return sorted([x for x in (scene.enemies if self.side else scene.heroes) if x is not None], key=lambda x: x.hp)[0], random.choice(crippling)

    def recovery(self):
        self.hp = self.max_hp
        self.rect.left = width

    def help(self, skill, target):
        self.target = target
        self.cur_skill = skill
        self.iteration = 0
        self.helping = True

    def shoot(self, skill, target):
        self.target = target
        self.cur_skill = skill
        self.iteration = 0
        self.shooting = True
        skill.spell.flip = not self.side
        skill.spell.rect.left = self.place[0] + 60
        skill.spell.rect.bottom = self.place[1] + 100
        skill.spell.moving_x = (target.place[0] - self.place[0]) / 30
        skill.spell.moving_y = (target.place[1] - self.place[1]) / 30

    def forward(self, skill, target):
        self.target = target
        self.cur_skill = skill

        self.forward_move = True
        self.iteration = 0
        distance = 50 if self.side else -50
        self.moving_x = (target.place[0] - distance - self.place[0]) / 30
        self.moving_y = (target.place[1] - self.place[1]) / 30

    def back(self):
        self.backing = True
        self.iteration = 0
        self.moving_x = (self.place[0] - self.rect.x) / 30
        self.moving_y = (self.place[1] - self.rect.y) / 30

    def update(self, *args):
        global moving
        if self.iteration == 30:
            if self.forward_move:
                self.forward_move = False
                self.moving_x = 0
                self.moving_y = 0
                self.attacking = True
                self.iteration = 0
            elif self.attacking:
                self.attacking = False
                self.back()
                self.target.hp -= self.damage * self.cur_skill.coefficient * (1 - self.target.armor / 100)
                ShiftHP(self.target.place, self.damage * self.cur_skill.coefficient * (1 - self.target.armor / 100), True)
                if self.target.side:
                    bar = scene.heroes_bars[self.target.position]
                else:
                    bar = scene.enemies_bars[self.target.position]
                bar.hp -= self.damage * self.cur_skill.coefficient * (1 - self.target.armor / 100)
            elif self.backing:
                self.backing = False
                self.moving_x = 0
                self.moving_y = 0
                self.iteration = 0
                self.target = None
                self.cur_skill = None
            elif self.helping:
                self.helping = False
                self.target.hp = min(self.target.max_hp, self.target.hp + self.magic * self.cur_skill.coefficient)
                if self.target.side:
                    bar = scene.heroes_bars[self.target.position]
                else:
                    bar = scene.enemies_bars[self.target.position]
                bar.hp = min(bar.max_hp, bar.hp + self.magic * self.cur_skill.coefficient)
                ShiftHP(self.target.place, self.magic * self.cur_skill.coefficient, False)
                self.iteration = 0
                self.target = None
                self.cur_skill = None
                next_turn()
            elif self.shooting:
                self.iteration = 0
                self.target.hp -= self.magic * self.cur_skill.coefficient
                ShiftHP(self.target.place, self.magic * self.cur_skill.coefficient, True)
                if self.target.side:
                    bar = scene.heroes_bars[self.target.position]
                else:
                    bar = scene.enemies_bars[self.target.position]
                bar.hp -= self.magic * self.cur_skill.coefficient
                self.cur_skill.spell.down()
                self.target.getting_damage = True
                self.target.update()
                self.target.iteration = 0
                self.shooting = False
                self.target = None
                self.cur_skill = None

            elif self.getting_damage:
                scene.selected = None
                self.getting_damage = False
                if self.hp <= 0:
                    if self in scene.heroes:
                        scene.heroes[self.position] = None
                    else:
                        scene.enemies[self.position] = None
                    self.recovery()
                next_turn()

        self.cur_image = 0

        if self.forward_move or self.backing:
            if self.iteration < 10:
                self.cur_image = 17
            elif self.iteration < 20:
                self.cur_image = 18
            else:
                self.cur_image = 19
        if self.attacking or self.helping:
            if self.iteration < 5:
                self.cur_image = 20
            elif self.iteration < 10:
                self.cur_image = 21
            elif self.iteration < 15:
                self.cur_image = 22
            else:
                self.cur_image = 23
                if self.attacking:
                    self.target.getting_damage = True
                if self.target != self:
                    self.target.iteration = 0
        if self.getting_damage:
            if self.iteration < 5:
                self.cur_image = 11
            elif self.iteration < 10:
                self.cur_image = 12
            elif self.iteration < 15:
                self.cur_image = 13
            else:
                self.cur_image = 14
        if self.shooting:
            if self.iteration < 5:
                self.cur_image = 26
            elif self.iteration < 10:
                self.cur_image = 27
            else:
                self.cur_image = 28

        self.image = pygame.transform.flip(self.frames[self.cur_image], not self.side, False)

        self.rect = self.rect.move(self.moving_x, self.moving_y)
        self.iteration += 1


class HPBar(pygame.sprite.Sprite):
    def __init__(self, name, hp):
        super().__init__(all_sprites, bars_sprites)
        self.max_hp = hp
        self.name = bar_font.render(name, True, (0, 0, 0))
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
        hp = bar_font.render(str(int(self.hp)), True, (0, 0, 0))
        pygame.draw.rect(self.image, 'green', (2, 2, 246, 26))
        pygame.draw.rect(self.image, 'red', (self.percent * 2.5, 2, 250 - self.percent * 2.5 - 1, 26))
        self.image.blit(self.name, (5, 0))
        self.image.blit(hp, (190, 0))


class ShiftHP(pygame.sprite.Sprite):
    def __init__(self, pos, value, damage):
        super().__init__(all_sprites, bars_sprites)
        self.image = pygame.Surface((len(str(value)) * 40, 40), pygame.SRCALPHA, 32)
        color = 'red' if damage else 'green'
        font = pygame.font.SysFont('Sans', 40)
        name = font.render(str(int(value)), True, color)
        self.image.blit(name, (5, 0))
        self.rect = pygame.Rect(pos, (len(str(value)) * 40, 40))
        self.iteration = 0

    def update(self, *args):
        self.iteration += 1
        self.rect = self.rect.move(0, -2)
        if self.iteration == 40:
            self.kill()


class Skill(pygame.sprite.Sprite):
    def __init__(self, name, coefficient, pos, meaning, to_enemy, to_hero, spell=None, effect=None):
        super().__init__(all_sprites, skills_sprites)
        self.coefficient = coefficient
        self.meaning = meaning
        self.to_enemy = to_enemy
        self.to_hero = to_hero
        self.pos = pos
        self.spell = spell
        self.effect = effect
        self.image = pygame.transform.scale(load_image(name), (50, 50))
        self.rect = pygame.Rect((width, 740, 50, 50))

    def update(self, *args):
        global your_turn, moving
        self.rect.left = width
        if scene.selected is not None and (scene.selected.side and self.to_hero or not scene.selected.side and self.to_enemy) and self in scene.heroes[1].skills:
            self.rect.left = 30 + self.pos * 60
        if your_turn:
            if scene.selected is not None and args and args[0].type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(args[0].pos):
                if self.meaning == 'closed':
                    scene.heroes[1].forward(self, scene.selected)
                elif self.meaning == 'help':
                    scene.heroes[1].help(self, scene.selected)
                elif self.meaning == 'ranged':
                    scene.heroes[1].shoot(self, scene.selected)
                your_turn = False
                moving = False


class Spell(pygame.sprite.Sprite):
    def __init__(self, name):
        super().__init__(all_sprites, spells_sprites)
        self.frames = []
        self.cut_sheet(pygame.transform.scale(load_image(name), (192, 96)), 2, 1)
        self.cur_image = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.flip = False
        self.down()

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(frame_location, (self.rect.size[0], self.rect.size[1]))))

    def update(self, *args):
        self.cur_image += 1
        self.image = pygame.transform.flip(self.frames[self.cur_image % len(self.frames)], self.flip, False)
        self.rect = self.rect.move(self.moving_x, self.moving_y)

    def down(self):
        self.moving_x = 0
        self.moving_y = 0
        self.rect.left = width


class Sky(pygame.sprite.Sprite):
    def __init__(self, name, pos=0):
        super().__init__(all_sprites, background_sprites)
        self.image = pygame.transform.scale(load_image(name), (width, height / 3 * 2))
        self.rect = self.image.get_rect()
        self.rect.left += pos * 1200
        self.dx = -1

    def update(self, *args):
        self.rect = self.rect.move(self.dx, 0)
        if self.rect.left <= -1200:
            self.reset()

    def reset(self):
        self.rect.left = 1200


class Tree(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__(all_sprites, background_sprites)
        trees = ['brown tree2.png', 'brown_tree.png', 'green tree.png']
        self.frames = []
        self.cut_sheet(pygame.transform.scale(load_image(random.choice(trees)), (672, 384)), 2, 1)
        self.cur_image = random.randint(0, 1)
        self.image = self.frames[self.cur_image]
        self.rect = self.image.get_rect()
        self.rect.left = pos * 180 - 100
        self.rect.bottom = height * 2 / 5 + 100

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(frame_location, (self.rect.size[0], self.rect.size[1]))))


class Field(pygame.sprite.Sprite):
    def __init__(self, name):
        super().__init__(all_sprites, background_sprites)
        self.image = pygame.transform.scale(load_image(name), (width, height / 5 * 3))
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(0, height * 2 / 5)


strike = Skill('Icon.1_15.png', 1, 0, 'closed', True, False)
fireball_spell = Spell('orange_fireball.png')
fireball = Skill('Icon.1_24.png', 0.8, 1, 'ranged', True, False, fireball_spell)
heal = Skill('Icon.6_86.png', 2, 0, 'help', False, True)


def next_turn():
    global world_map, moving, your_turn, battle_number, battles_access, first_assistance, train
    if all([x is None for x in scene.heroes]) or all([x is None for x in scene.enemies]):
        for i in characters_sprites:
            i.recovery()
        for i in all_sprites:
            if i not in spells_sprites and i not in skills_sprites and i not in characters_sprites:
                i.kill()
        world_map = WorldMap()
        if all([x is None for x in scene.enemies]):
            Sonny.update_points += 5
            if first_assistance:
                Veradux.update_points += 5
            if not train:
                if battle_number == 2:
                    first_assistance = True
                if battle_number < len(battles_access) - 1:
                    battles_access[battle_number] = False
                    battles_access[battle_number + 1] = True
                    battle_number += 1
        train = False
        return 1
    moving = True
    if scene.pers_turning % 6 < 3:
        active = scene.heroes[scene.pers_turning % 3]
    else:
        active = scene.enemies[scene.pers_turning % 3]
    if active is not None:
        if not active.hero:
            tactic = active.strategy()
            target = tactic[0]
            technique = tactic[1]
            if technique.meaning == 'closed':
                active.forward(technique, target)
            elif technique.meaning == 'help':
                active.help(technique, target)
            elif technique.meaning == 'ranged':
                active.shoot(technique, target)
        else:
            your_turn = True
    scene.pers_turning += 1
    scene.selected = None
    if active is None:
        next_turn()


def terminate():
    pygame.quit()
    sys.exit()


scene = Scene()
battle_number = 1
battles_access = [True, True, False, False, False]

Sonny = Person('Sonny', load_image('SkeletonBase.png'), True, 1, True, [strike, fireball, heal], 1500, 10000, 10000)
Veradux = Person('Veradux', load_image('bloodSkeletonBase.png'), True, 2, False, [fireball, heal], 600, 150, 50, 3)
Warrior = Person('Warrior', load_image('warrior.png'), False, 1, False, [strike], 500)
Knight = Person('Knight', load_image('knight.png'), False, 2, False, [strike], 800, 0, 200, 10)
Mage = Person('Mage', load_image('mage.png'), False, 0, False, [fireball, heal], 600, 150, 50, 3)
Satyr = Person('Satyr', load_image('mvSatyr.png'), False, 1, False, [strike, heal, fireball], 3000, 400, 400, 20)
Cleric = Person('Cleric', load_image('cleric.png'), False, 1, False, [strike, heal], 600, 70, 130, 2)

first_assistance = False


def make_scene(chars, sky, field, trees=False):
    global scene, world_map, first_assistance
    world_map.kill()
    world_map = None
    scene.__init__()
    for i in chars:
        if i:
            scene.add_character(i)
    if first_assistance:
        scene.add_character(Veradux)
    Sky(sky)
    Sky(sky, 1)
    Field(field)
    if trees:
        for i in range(8):
            Tree(i)
    next_turn()


class MainMenu(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(all_sprites, main_sprites)
        self.image = pygame.transform.scale(load_image('main_menu.jpg'), (width, height))
        font = pygame.font.SysFont('monospaced', 100)
        name = font.render('SKELAPPERANCE DEMO', True, (0, 0, 0))
        self.image.blit(name, (170, 300))
        font = pygame.font.SysFont('monospaced', 90)
        name = font.render('нажмите в любом месте', True, (0, 0, 0))
        self.image.blit(name, (230, 450))
        self.rect = self.image.get_rect()


class WorldMap(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(all_sprites, main_sprites)
        self.image = pygame.transform.scale(load_image('world_map.jpg'), (width, height))
        self.upgrade = pygame.transform.scale(load_image('upgrade.png'), (200, 60))
        self.image.blit(self.upgrade, (width - 200, height - 60))
        self.upgrades_rect = pygame.Rect(width - 200, height - 60, 200, 60)
        self.rect = self.image.get_rect()

    def update(self, *args):
        self.__init__()
        pygame.draw.circle(self.image, 'yellow', (925, 160), 20)
        if battles_access[1]:
            pygame.draw.circle(self.image, 'red', (800, 250), 20)
        if battles_access[2]:
            pygame.draw.circle(self.image, 'red', (600, 320), 20)
        if battles_access[3]:
            pygame.draw.circle(self.image, 'red', (410, 330), 20)
        if battles_access[4]:
            pygame.draw.circle(self.image, 'red', (170, 470), 20)


class MenuUpgrade(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(all_sprites, main_sprites)
        self.image = pygame.Surface((width, height))
        pygame.draw.rect(self.image, 'white', pygame.Rect(0, 0, width / 3, height / 3 * 2))
        pygame.draw.rect(self.image, 'gray', pygame.Rect(0, height / 3 * 2, width / 3, height / 3))
        pygame.draw.rect(self.image, 'white', pygame.Rect(width / 3, height / 3 * 2, width / 3 * 2, height / 3))
        self.close = pygame.transform.scale(load_image('close.png', -1), (80, 75))
        self.close_rect = pygame.Rect(width - 80, 0, 80, 75)
        self.image.blit(self.close, (width - 80, 0))
        self.sonny_head = pygame.transform.scale(load_image('sonny_head.png', -1), (150, 120))
        pygame.draw.rect(self.image, 'black', (0, 400, 150, 135), 7)
        self.veradux_head = pygame.transform.scale(load_image('veradux_head.png', -1), (150, 120))
        pygame.draw.rect(self.image, 'black', (170, 400, 150, 135), 7)
        self.image.blit(self.sonny_head, (0, 400))
        self.sonny_rect = self.sonny_head.get_rect()
        self.sonny_rect.left = 0
        self.sonny_rect.top = 400
        self.image.blit(self.veradux_head, (170, 400))
        self.veradux_rect = self.veradux_head.get_rect()
        self.veradux_rect.left = 170
        self.veradux_rect.top = 400
        self.rect = self.image.get_rect()
        self.change(Sonny)
        self.changed = Sonny

    def update(self, *args):
        self.change(self.changed)
        if args and args[0].type == pygame.MOUSEBUTTONDOWN:
            if self.sonny_rect.collidepoint(args[0].pos):
                self.change(Sonny)
            if self.veradux_rect.collidepoint(args[0].pos):
                self.change(Veradux)

    def change(self, pers):
        self.changed = pers
        self.plus = bar_font.render('+', True, (0, 0, 0))

        pygame.draw.rect(self.image, 'gray', pygame.Rect(0, height / 3 * 2, width / 3, height / 3))
        self.hp = bar_font.render('HP: ' + str(int(pers.hp)), True, (0, 0, 0))
        self.add_hp_rect = pygame.Rect(140, 590, 30, 30)

        self.magic = bar_font.render('Magic: ' + str(int(pers.magic)), True, (0, 0, 0))
        self.add_magic_rect = pygame.Rect(140, 640, 30, 30)

        self.armor = bar_font.render('Armor: ' + str(int(pers.armor)) + '%', True, (0, 0, 0))
        self.add_armor_rect = pygame.Rect(140, 740, 30, 30)

        self.points = bar_font.render('Available points: ' + str(pers.update_points), True, (0, 0, 0))

        self.strength = bar_font.render('Strength: ' + str(int(pers.damage)), True, (0, 0, 0))
        self.add_strength_rect = pygame.Rect(140, 690, 30, 30)

        self.image.blit(self.points, (10, 550))
        self.image.blit(self.hp, (10, 600))
        self.image.blit(self.plus, (150, 600))
        self.image.blit(self.magic, (10, 650))
        self.image.blit(self.plus, (150, 650))
        self.image.blit(self.strength, (10, 700))
        self.image.blit(self.plus, (150, 700))
        self.image.blit(self.armor, (10, 750))
        self.image.blit(self.plus, (150, 750))


menu_upgrade = None
main_menu = MainMenu()
world_map = None
train = False

while True:
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            if main_menu:
                main_menu.kill()
                main_menu = None
                world_map = WorldMap()
            elif world_map:
                if 779 < event.pos[0] < 821 and 229 < event.pos[1] < 271 and battles_access[1]:
                    make_scene([Sonny, Warrior], 'sky.png', 'grass.jpg')
                elif 579 < event.pos[0] < 621 and 299 < event.pos[1] < 341 and battles_access[2]:
                    make_scene([Sonny, Warrior, Knight], 'dark_sky.png', 'grass.jpg', True)
                elif 389 < event.pos[0] < 431 and 319 < event.pos[1] < 351 and battles_access[3]:
                    make_scene([Sonny, Warrior, Knight, Mage], 'next_sky.png', 'bridge.png')
                elif 149 < event.pos[0] < 191 and 449 < event.pos[1] < 491 and battles_access[4]:
                    make_scene([Sonny, Satyr], 'dark_sky.png', 'dark_grass.jpg')
                elif 904 < event.pos[0] < 946 and 139 < event.pos[1] < 181 and battles_access[0]:
                    train = True
                    make_scene([Sonny, Cleric], 'sky.png', 'grass.jpg')
                elif world_map.upgrades_rect.collidepoint(event.pos):
                    world_map.kill()
                    menu_upgrade = MenuUpgrade()
            if menu_upgrade:
                if menu_upgrade.changed.update_points:
                    if menu_upgrade.add_hp_rect.collidepoint(event.pos):
                        menu_upgrade.changed.hp += 30
                        menu_upgrade.changed.max_hp += 30
                        menu_upgrade.changed.update_points -= 1
                    elif menu_upgrade.add_armor_rect.collidepoint(event.pos):
                        menu_upgrade.changed.armor += 1
                        menu_upgrade.changed.update_points -= 1
                    elif menu_upgrade.add_magic_rect.collidepoint(event.pos):
                        menu_upgrade.changed.magic += 5
                        menu_upgrade.changed.update_points -= 1
                    elif menu_upgrade.add_strength_rect.collidepoint(event.pos):
                        menu_upgrade.changed.damage += 5
                        menu_upgrade.changed.update_points -= 1
                if menu_upgrade.close_rect.collidepoint(event.pos):
                    menu_upgrade.kill()
                    menu_upgrade = None
                    world_map.add(main_sprites)
            for char in characters_sprites:
                if char.rect.collidepoint(event.pos):
                    if your_turn:
                        scene.selected = char
        if event.type == pygame.QUIT:
            terminate()
    pygame.display.flip()
    screen.fill((255, 255, 255))
    main_sprites.draw(screen)
    if scene:
        background_sprites.draw(screen)
        if scene.selected:
            rect = pygame.Rect(scene.selected.place[0] + 16, scene.selected.place[1] + 120, 65, 40)
            pygame.draw.ellipse(screen, 'yellow', rect)
            pygame.draw.ellipse(screen, 'black', rect, 2)
        characters_sprites.draw(screen)
        bars_sprites.draw(screen)
        skills_sprites.draw(screen)
        spells_sprites.draw(screen)
        all_sprites.update(event)
    clock.tick(FPS)
