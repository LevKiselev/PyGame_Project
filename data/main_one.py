from sys import exit
import pygame
import sqlite3
from random import randrange
from datetime import date

# Константы окна
FPS = 50
WIDTH = 1500
HEIGHT = 500
Y_OFFSET = 100
Y_STEP = 70
X_BASKET = WIDTH - 600
X_WALL = WIDTH - 10
X_DELLEAVE = WIDTH

# Константы цветов
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
MAGENTA = (255, 0, 255)
GREEN = (0, 120, 64)
YELLOW = (255, 224, 160)
TRANSP = (116, 172, 255)

# Константы целей
G_COMBY = 1  # Любые комбинации
G_DIAGS = 2  # Диагонали
G_LEAVE = 3  # Листья
G_POINT = 4  # Очки
G_HORIZ = 5  # Горизонтали

# Константы диалога
NEXT_LEVEL = 0
PAUSE_GAME = 1
GAME_OVER = 2
SAVE_SCORE = 3

# Константы событий
EV_ADDLEAVE = pygame.USEREVENT + 1
EV_BASKETUP = pygame.USEREVENT + 2
EV_BASKETDN = pygame.USEREVENT + 3

NUM_LEAVES = 16
# SINUS = [3, 5, 7, 9, 10, 10, 10, 9, 7, 5, 3, 0, -3, -5, -7, -9, -10, -10, -10, -9, -7, -5, -3, 0]
SINUS = [3, 2, 2, 2, 1, 0, 0, -1, -2, -2, -2, -3, -3, -2, -2, -2, -1, 0, 0, 1, 2, 2, 2, 3]

goal_name = ['', "Комбинации", "Диагонали", "Листья", "Очки", "Вертикали"]

points = [
    [5, 50, 200],  # Листья в игре
    [100, 5000, 10000],  # Горизонтали
    [1000, 5000, 10000],  # Вертикали
    [5000, 10000, 20000]  # Диагонали
]

lives = 3
health = 3
score = 0
level = 1
goal_type = G_COMBY
goal_val = 3
leave_delay = 4000
different = 5
wind_speed = 3
leave_stack = []
level_data = (level, wind_speed, leave_delay, goal_type, goal_val, different)
username = ""
pause = False
infinity = False

wall: list[list] = [[0] * 5 for _ in range(5)]
con = sqlite3.connect("data/gamedata.db")
cur = con.cursor()


class Basket(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.cur_pos = 2
        self.image = basket_empty
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()
        self.rect.width = 20
        self.radius = 10
        self.rect.x = X_BASKET
        self.rect.y = self.cur_pos * Y_STEP + Y_OFFSET - 15

    def up(self):
        if self.cur_pos:
            self.cur_pos -= 1
            self.rect.y = self.cur_pos * Y_STEP + Y_OFFSET - 15

    def down(self):
        if self.cur_pos < 4:
            self.cur_pos += 1
            self.rect.y = self.cur_pos * Y_STEP + Y_OFFSET - 15

    def drop(self):
        global level, health, lives
        if leave_stack and 0 in wall[self.cur_pos]:
            elem = leave_stack.pop()
            elem.add(in_wall)
            elem.remove(in_basket)
            empty = wall[self.cur_pos].index(0)
            wall[self.cur_pos][empty] = elem
            elem.coord = (self.cur_pos, empty)
            drop_sound.play()

    def back(self):
        if leave_stack:
            elem = leave_stack.pop()
            elem.add(in_back)
            elem.remove(in_basket)
            elem.coord = (self.cur_pos, X_BASKET - 100)
            back_sound.play()

    def update(self, *args):
        if len(leave_stack) < 5:
            self.image = basket_empty
        else:
            self.image = basket_full
        self.image.set_colorkey(WHITE)


class Bonus(pygame.sprite.Sprite):

    def __init__(self, val, x, y, speed=3, down=False):
        pygame.sprite.Sprite.__init__(self)
        text = "+" + str(val)
        if val > 5000:
            text += " !!!"
            big_bonus_sound.play()
        else:
            bonus_sound.play()
        self.image = font_mid.render(text, True, MAGENTA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed
        self.down = down

    def update(self):
        if self.down:
            self.rect.y += self.speed
            if self.rect.y > HEIGHT:
                self.kill()
        else:
            self.rect.x += self.speed
            if self.rect.x > WIDTH:
                self.kill()


class Leave(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.coord = (0, 0)
        self.leave_id = randrange(1, different + 1)
        self.image_src = leave_pics[self.leave_id]
        self.image_src.set_colorkey(TRANSP)
        self.image = self.image_src.copy()
        self.rect = self.image.get_rect()
        self.radius = int(Y_OFFSET * .2)
        self.rect.x = -Y_STEP
        self.rect.y = randrange(5) * Y_STEP + Y_OFFSET
        self.stepy = 0
        self.speedx = wind_speed
        self.deltax = 0
        self.rot = 0
        self.rot_speed = randrange(-7, 8, 2)

    def __call__(self, *args, **kwargs):
        return self.leave_id

    def rotate(self):
        self.rot = (self.rot + self.rot_speed) % 360
        new_image = pygame.transform.rotate(self.image_src, self.rot)
        old_center = self.rect.center
        self.image = new_image
        self.rect = self.image.get_rect()
        self.rect.center = old_center

    def update(self, *args):
        global score, goal_val

        def fly(forward=True):
            global health
            self.rotate()
            if forward:
                self.rect.x += self.speedx
                self.deltax += self.speedx
                if self.deltax > 16:
                    self.rect.y += SINUS[self.stepy]
                    self.stepy = (self.stepy + 1) % len(SINUS)
                    self.deltax = 0
            else:
                self.rect.x -= 10
                if self.rect.left < 200:
                    self.add(in_air)
                    self.remove(in_back)
            if self.rect.left > X_DELLEAVE:
                if not infinity:
                    fault_sound.play()
                    health -= 1
                    if health == 0:
                        if lives == 1 and score > 5000:
                            dialog_win(SAVE_SCORE)
                        dialog_win(GAME_OVER)
                self.kill()

        self.speedx = wind_speed
        if args[0] == 0:  # Полет листьев в заставке
            fly()
        if args[0] == 1:  # Полет листьев и попадание в корзину
            if (pygame.sprite.spritecollideany(self, gr_basket, pygame.sprite.collide_circle)
                    and len(leave_stack) < 5):
                self.add(in_basket)
                self.remove(in_air)
                score += points[0][0]
                if goal_type == G_POINT:
                    goal_val -= points[0][0]
                if goal_type == G_LEAVE:
                    goal_val -= 1
                self.image = self.image_src
                leave_stack.append(self)
                self.rect.x = X_BASKET + (5 - len(leave_stack)) * 20
                basket_sound.play()
            else:
                fly()
        if args[0] == 2:  # Перемещение листьев вместе с корзиной
            self.rect.y = basket.cur_pos * Y_STEP + Y_OFFSET
        if args[0] == 3:  # Листья в стене
            self.rect.x = X_WALL - (self.coord[1] + 1) * Y_STEP
        if args[0] == 4:  # Удаление листьев из стены
            if self.coord in destroy_set:
                snowflake = Snowflake(self.coord[0], self.coord[1])
                wall[self.coord[0]][self.coord[1]] = 0
                in_wall.add(snowflake)
                self.kill()
        if args[0] == 5:  # Отброс листа назад
            fly(False)


class Snowflake(Leave):

    def __init__(self, y, x):
        pygame.sprite.Sprite.__init__(self)
        self.coord = (y, x)
        self.leave_id = 0
        self.image_src = leave_pics[0]
        self.image_src.set_colorkey(TRANSP)
        self.image = self.image_src.copy()
        self.rect = self.image.get_rect()
        self.rect.y = y * Y_STEP + Y_OFFSET
        self.rect.x = X_WALL - (x + 1) * Y_STEP
        self.step = 0
        self.rot = 0
        self.rot_speed = 8

    def update(self, *args):
        global wall
        if self.step < 20:
            self.rotate()
            self.image.set_alpha(self.step * 12)
            self.step += 1
        else:
            self.kill()
            squeeze_wall()


def dialog_win(cont):
    global pause, lives, health, username
    titles = ["Next Level", "Pause", "Game Over", "Save Score"]
    colors = [(BLACK, MAGENTA), (MAGENTA, BLACK), (BLUE, BLACK), (GREEN, GREEN)]
    pause = True
    dialog = dialog_bg[cont].copy()
    dialog.set_colorkey(WHITE)
    dialog_rect = dialog.get_rect()
    draw_text(dialog, titles[cont], font_mid, colors[cont][0], 380, 150)
    if cont == SAVE_SCORE:
        draw_value(dialog, "Счет", score, font_mid, BLACK, MAGENTA, 350, 220)
        username = enter_name(dialog)
        pause = False
        return
    elif cont:
        draw_value(dialog, "Счет", score, font_mid, BLACK, MAGENTA, 350, 220)
        draw_value(dialog, "i", "Инструкция", font_small, colors[cont][0], colors[cont][1], 300, 320)
        draw_value(dialog, "t", "Таблица рекордов", font_small, colors[cont][0], colors[cont][1], 300, 340)
        draw_value(dialog, "ESCAPE", "Закончить игру", font_small, colors[cont][0], colors[cont][1], 300, 360)
        draw_value(dialog, "ENTER", "Начать игру заново", font_small, colors[cont][0], colors[cont][1], 300, 380)
        if cont == GAME_OVER and lives > 1 or cont == PAUSE_GAME:
            draw_value(dialog, "SPACE", "Продолжить игру", font_small, colors[cont][0], colors[cont][1], 300, 400)
    else:
        draw_value(dialog, "Уровень", level, font_mid, colors[cont][0], colors[cont][1], 420, 270)
        draw_value(dialog, goal_name[goal_type], goal_val, font_mid, colors[cont][0], colors[cont][1], 420, 320)

    screen.blit(bg, bg_rect)
    screen.blit(dialog, ((WIDTH - dialog_rect.width) // 2, 0))
    pygame.display.flip()
    run = True
    while run:
        clock.tick(FPS)
        screen.blit(bg, bg_rect)
        screen.blit(dialog, ((WIDTH - dialog_rect.width) // 2, 0))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                goodbye()
            if ev.type == pygame.KEYDOWN:
                if cont:
                    if ev.key == pygame.K_ESCAPE:
                        goodbye()
                    elif ev.key == pygame.K_RETURN:
                        run = False
                        game_reset()
                    elif ev.key == pygame.K_SPACE:
                        if cont == GAME_OVER and lives > 1:
                            lives -= 1
                            health = 3
                            level_reset()
                            run = False
                        elif cont == PAUSE_GAME:
                            run = False
                    elif ev.key == pygame.K_i:
                        info()
                    elif ev.key == pygame.K_t:
                        top_score()
                else:
                    run = False
        pygame.display.flip()
    pause = False


def level_reset():
    global wall, leave_stack, wind_speed, leave_delay, goal_type, goal_val, different, level_data, pause
    level_data = cur.execute(f"SELECT * FROM levels WHERE id = {level}").fetchone()
    wind_speed, leave_delay, goal_type, goal_val, different = level_data[1:]
    wall = [[0] * 5 for _ in range(5)]
    leave_stack = []
    pygame.time.set_timer(EV_ADDLEAVE, leave_delay)
    in_air.empty()
    in_basket.empty()
    in_wall.empty()
    in_back.empty()
    screen.blit(bg, bg_rect)
    pygame.display.flip()
    dialog_win(NEXT_LEVEL)


def game_reset():
    global score, level, lives, health
    lives = 3
    health = 3
    score = 0
    level = 1
    level_reset()


def level_bonus():
    global wall, pause, score
    pause = True
    gr = pygame.sprite.Group()
    gr.add(in_back.sprites())
    gr.add(in_air.sprites())
    gr.add(in_basket.sprites())
    gr.add(in_wall.sprites())
    for i in range(5):
        for j in range(5):
            if not wall[i][j]:
                snowflake = Snowflake(i, j)
                gr.add(snowflake)
    for elem in gr:
        if elem():
            bon = points[0][1]
        else:
            bon = points[0][2]
        score += bon
        bonus = Bonus(bon, elem.rect.x, elem.rect.y, 10, True)
        gr_basket.add(bonus)
        elem.kill()
        for _ in range(7):
            clock.tick(FPS)
            gr_basket.update()
            screen.blit(bg, bg_rect)
            draw_value(screen, "Счет", score, font_mid, BLUE, MAGENTA, 200, 10)
            gr.draw(screen)
            gr_basket.draw(screen)
            pygame.display.flip()
    level_reset()


def check_wall():
    global score, goal_val, goal_type
    res = set()
    combs = 0
    accum = 0
    for i in range(5):  # Горизонтали
        if wall[i][2]:
            cnt = [(i, 2)]
            if wall[i][1] and wall[i][2]() == wall[i][1]():
                cnt.append((i, 1))
                if wall[i][0] and wall[i][2]() == wall[i][0]():
                    cnt.append((i, 0))
            if wall[i][3] and wall[i][2]() == wall[i][3]():
                cnt.append((i, 3))
                if wall[i][4] and wall[i][2]() == wall[i][4]():
                    cnt.append((i, 4))
            if len(cnt) > 2:
                accum += points[1][len(cnt) - 3]
                combs += 1
                if goal_type == G_COMBY:
                    goal_val -= (len(cnt) - 2)
                res = res | set(cnt)
    for i in range(5):  # Вертикали
        if wall[2][i]:
            cnt = [(2, i)]
            if wall[1][i] and wall[2][i]() == wall[1][i]():
                cnt.append((1, i))
                if wall[0][i] and wall[2][i]() == wall[0][i]():
                    cnt.append((0, i))
            if wall[3][i] and wall[2][i]() == wall[3][i]():
                cnt.append((3, i))
                if wall[4][i] and wall[2][i]() == wall[4][i]():
                    cnt.append((4, i))
            if len(cnt) > 2:
                accum += points[2][len(cnt) - 3]
                combs += 1
                if goal_type in [G_COMBY, G_HORIZ]:
                    goal_val -= (len(cnt) - 2)
                res = res | set(cnt)
    matr: list[list] = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]] + wall.copy() + [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
    for i in range(2, 7):  # Диагонали
        if matr[i][2]:
            cnt = [(i - 2, 2)]
            if matr[i - 1][1] and matr[i][2]() == matr[i - 1][1]():
                cnt.append((i - 3, 1))
                if matr[i - 2][0] and matr[i][2]() == matr[i - 2][0]():
                    cnt.append((i - 4, 0))
            if matr[i + 1][3] and matr[i][2]() == matr[i + 1][3]():
                cnt.append((i - 1, 3))
                if matr[i + 2][4] and matr[i][2]() == matr[i + 2][4]():
                    cnt.append((i, 4))
            if len(cnt) > 2:
                accum += points[3][len(cnt) - 3]
                combs += 1
                if goal_type in [G_COMBY, G_DIAGS]:
                    goal_val -= (len(cnt) - 2)
                res = res | set(cnt)
            cnt = [(i - 2, 2)]
            if matr[i - 1][3] and matr[i][2]() == matr[i - 1][3]():
                cnt.append((i - 3, 3))
                if matr[i - 2][4] and matr[i][2]() == matr[i - 2][4]():
                    cnt.append((i - 4, 4))
            if matr[i + 1][1] and matr[i][2]() == matr[i + 1][1]():
                cnt.append((i - 1, 1))
                if matr[i + 2][0] and matr[i][2]() == matr[i + 2][0]():
                    cnt.append((i, 0))
            if len(cnt) > 2:
                accum += points[3][len(cnt) - 3]
                combs += 1
                if goal_type in [G_COMBY, G_DIAGS]:
                    goal_val -= (len(cnt) - 2)
                res = res | set(cnt)
    accum *= combs
    if goal_type == G_POINT:
        goal_val -= accum
    score += accum
    if accum:
        bonus = Bonus(accum, X_WALL - 300, 450)
        gr_basket.add(bonus)
    return res


def squeeze_wall():
    for i in range(5):
        if wall[i] != [0, 0, 0, 0, 0]:
            while 0 in wall[i]:
                wall[i].remove(0)
            for j in range(len(wall[i])):
                wall[i][j].coord = (i, j)
            while len(wall[i]) < 5:
                wall[i].append(0)


def add_leave(group):
    if not pause:
        elem = Leave()
        group.add(elem)


def enter_name(surf):
    x = 150
    y = 350
    w = 400
    h = 27
    cur_flash = False
    cnt = 0
    uname = username
    surf_rect = surf.get_rect()
    comment_surface = font_small.render("Введите ваше имя:", True, GREEN)
    comment_rect = comment_surface.get_rect()
    comment_rect.bottomleft = (x, y)
    l_rect = health_pics[0].get_rect()
    run = True
    while run:
        clock.tick(FPS)
        cnt += 1
        if cnt == 25:
            cur_flash = not cur_flash
            cnt = 0
        pygame.draw.rect(surf, BLACK, (x - 12, y - 2, w + 4, h + 4), 2, 10)
        pygame.draw.rect(surf, YELLOW, (x - 10, y, w, h), 0, 10)
        text_surface = font_small.render(uname, True, BLACK)
        text_rect = text_surface.get_rect()
        text_rect.topleft = (x, y)
        surf.blit(text_surface, text_rect)
        surf.blit(comment_surface, comment_rect)
        if cur_flash:
            l_rect.topleft = (x + text_rect.width, y - 1)
            surf.blit(health_pics[0], l_rect)
        screen.blit(bg, bg_rect)
        screen.blit(surf, ((WIDTH - surf_rect.width) // 2, 0))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                goodbye()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    if not uname:
                        uname = "NEMO"
                    new_rec = (None, score, level, date.today(), uname)
                    cur.execute("INSERT INTO scores VALUES (?,?,?,?,?)", new_rec)
                    con.commit()
                    return uname
                elif ev.key == pygame.K_BACKSPACE and len(uname):
                    uname = uname[:-1]
                elif pygame.K_SPACE <= ev.key <= pygame.K_z and len(uname) < 20:
                    uname += ev.unicode.upper()
        pygame.display.flip()


def draw_health(val, tcolor, x, y):
    text_surface = font_small.render("Здоровье: ", True, tcolor)
    text_rect = text_surface.get_rect()
    text_rect.midright = (x, y)
    screen.blit(text_surface, text_rect)
    l_rect = health_pics[0].get_rect()
    for i in range(val):
        l_rect.midleft = (x, y)
        screen.blit(health_pics[min([i, 3])], l_rect)
        x += 15


def draw_value(surf, text, val, font, tcolor, vcolor, x, y):
    text_surface = font.render(text + ": ", True, tcolor)
    val_surface = font.render(str(val), True, vcolor)
    text_rect = text_surface.get_rect()
    val_rect = val_surface.get_rect()
    text_rect.topright = (x, y)
    val_rect.topleft = (x, y)
    surf.blit(text_surface, text_rect)
    surf.blit(val_surface, val_rect)


def draw_text(surf, text, font, color, x, y, centered=True):
    lines = text.split('\n')
    for i in range(len(lines)):
        text_surface = font.render(lines[i], True, color)
        text_rect = text_surface.get_rect()
        if centered:
            text_rect.midtop = (x, y + i * text_rect.height)
        else:
            text_rect.topleft = (x, y + i * text_rect.height)
        surf.blit(text_surface, text_rect)


def info():
    f = open("data/help.txt", encoding="utf-8")
    text = f.read().split("#####\n")
    screen.fill(YELLOW)
    draw_text(screen, "Правила игры", font_mid, GREEN, 200, 10, False)
    draw_text(screen, text[0], font_small, BLUE, 200, 65, False)
    draw_text(screen, "Управление", font_mid, GREEN, 200, 325, False)
    keys = text[1].split('\n')
    f.close()
    y = 380
    for key in keys:
        if key:
            k = key.split(": ")
            draw_value(screen, k[0], k[1], font_small, MAGENTA, BLUE, 320, y)
            y += 20
    pygame.display.flip()
    run = True
    while run:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                goodbye()
            if ev.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                run = False


def top_score():
    x = [100, 150, 300, 350, 500]
    c = [BLUE, MAGENTA, GREEN, BLUE, MAGENTA]
    header = ["#", "Счет", "Уров", "   Дата", "Имя"]
    screen.fill(YELLOW)
    draw_text(screen, "Таблица рекордов", font_mid, BLUE, 150, 10, False)
    res = cur.execute("SELECT * FROM scores ORDER BY score DESC LIMIT 20").fetchall()
    for j in range(1, 5):
        draw_text(screen, header[j], font_small, BLACK, x[j], 60, False)
    for i in range(len(res)):
        for j in range(1, 5):
            draw_text(screen, str(res[i][j]), font_small, c[j], x[j], i * 20 + 85, False)
    pygame.display.flip()
    run = True
    while run:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                goodbye()
            if ev.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                run = False


def goodbye():
    global different, pause, infinity
    pause = False
    infinity = True
    different = NUM_LEAVES - 1
    pygame.time.set_timer(EV_ADDLEAVE, 200)
    gr = pygame.sprite.Group()
    if not pygame.mixer.Sound.get_num_channels(intro_sound):
        intro_sound.play()
    screen.fill(BLACK)
    while 1:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type in [pygame.QUIT, pygame.KEYDOWN]:
                pygame.quit()
                exit()
            if ev.type == EV_ADDLEAVE:
                add_leave(gr)
        gr.update(0)
        gr.draw(screen)
        draw_text(screen, "Goodbye, press any key...", font_mid, GREEN, WIDTH // 2, 10)
        pygame.display.flip()


def intro():
    global different, infinity
    infinity = True
    different = NUM_LEAVES - 1
    pygame.time.set_timer(EV_ADDLEAVE, 200)
    gr = pygame.sprite.Group()
    intro_sound.play()
    run = True
    while run:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                goodbye()
            if ev.type == EV_ADDLEAVE:
                add_leave(gr)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE:
                    run = False
                    intro_sound.stop()
                    infinity = False
                if ev.key == pygame.K_RETURN:
                    run = False
                    info()
                    intro_sound.stop()
                    infinity = False

        screen.blit(bg, bg_rect)
        gr.update(0)
        gr.draw(screen)
        draw_text(screen, "Осенний ветер", font_big, BLUE, WIDTH // 2 + 3, 103)
        draw_text(screen, "Осенний ветер", font_big, WHITE, WIDTH // 2, 100)
        draw_value(screen, "ENTER", "Инструкция", font_mid, MAGENTA, WHITE, 400, 420)
        draw_value(screen, "SPACE", "Старт", font_mid, MAGENTA, WHITE, 1000, 420)
        pygame.display.flip()


pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wind of Autumn")
clock = pygame.time.Clock()

font_small = pygame.font.Font("data/Peace_Sans.ttf", 20)
font_mid = pygame.font.Font("data/Peace_Sans.ttf", 40)
font_big = pygame.font.Font("data/Peace_Sans.ttf", 150)

bg = pygame.image.load("data/pics/background_0.png").convert()
bg_rect = bg.get_rect()
basket_empty = pygame.image.load("data/pics/basket0.png").convert()
basket_full = pygame.image.load("data/pics/basket1.png").convert()

leave_pics = []
for i in range(NUM_LEAVES):
    leave_pics.append(pygame.image.load(f"data/pics/leave{i:02d}.png").convert())

health_pics = []
for i in range(4):
    health_pics.append(pygame.transform.scale(leave_pics[i + 1], (30, 30)))
    health_pics[i].set_colorkey(TRANSP)
pygame.display.set_icon(health_pics[0])

dialog_bg = []
for i in range(4):
    dialog_bg.append(pygame.image.load(f"data/pics/dialog_bg{i}.png").convert())

basket_sound = pygame.mixer.Sound('data/sound/basket.wav')
drop_sound = pygame.mixer.Sound('data/sound/drop.wav')
back_sound = pygame.mixer.Sound('data/sound/back.wav')
bonus_sound = pygame.mixer.Sound('data/sound/bonus.wav')
big_bonus_sound = pygame.mixer.Sound('data/sound/big_bonus.wav')
fault_sound = pygame.mixer.Sound('data/sound/fault.wav')
level_sound = pygame.mixer.Sound('data/sound/big_bonus.wav')
intro_sound = pygame.mixer.Sound('data/sound/intro.mp3')

intro()

in_air = pygame.sprite.Group()
in_back = pygame.sprite.Group()
in_basket = pygame.sprite.Group()
gr_basket = pygame.sprite.Group()
in_wall = pygame.sprite.Group()

basket = Basket()
gr_basket.add(basket)

game_reset()

while 1:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            goodbye()
        if event.type == EV_ADDLEAVE:
            add_leave(in_air)
        if event.type == EV_BASKETUP:
            basket.up()
        if event.type == EV_BASKETDN:
            basket.down()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                basket.back()
            elif event.key == pygame.K_RIGHT:
                wind_speed = 10
                pygame.time.set_timer(EV_ADDLEAVE, 500)
            elif event.key == pygame.K_SPACE:
                basket.drop()
            elif event.key == pygame.K_UP:
                basket.up()
                pygame.time.set_timer(EV_BASKETUP, 170)
            elif event.key == pygame.K_DOWN:
                basket.down()
                pygame.time.set_timer(EV_BASKETDN, 170)
            else:
                dialog_win(PAUSE_GAME)
                add_leave(in_air)
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_RIGHT:
                wind_speed = level_data[1]
                pygame.time.set_timer(EV_ADDLEAVE, leave_delay)
            elif event.key == pygame.K_UP:
                pygame.time.set_timer(EV_BASKETUP, 0)
            elif event.key == pygame.K_DOWN:
                pygame.time.set_timer(EV_BASKETDN, 0)

    destroy_set = check_wall()
    if destroy_set:
        in_wall.update(4)
        destroy_set = set()
    if goal_val <= 0:
        level += 1
        if health < 10:
            health += 1
        else:
            health = 3
            lives += 1
        level_bonus()

    in_air.update(1)
    in_basket.update(2)
    in_wall.update(3)
    in_back.update(5)
    gr_basket.update()

    screen.blit(bg, bg_rect)
    draw_health(health, BLUE, 750, 50)
    draw_value(screen, "Жизни", lives, font_small, BLUE, MAGENTA, 750, 10)
    draw_value(screen, "Уровень", level, font_small, BLUE, MAGENTA, WIDTH - 100, 10)
    draw_value(screen, goal_name[goal_type], goal_val, font_small, BLUE, MAGENTA, WIDTH - 100, 40)
    draw_value(screen, "Счет", score, font_mid, BLUE, MAGENTA, 200, 10)

    for i in range(6):
        pygame.draw.line(screen, WHITE, (X_WALL - Y_STEP * 5, Y_OFFSET + Y_STEP * i),
                         (X_WALL, Y_OFFSET + Y_STEP * i), width=1)
        pygame.draw.line(screen, WHITE, (X_WALL - Y_STEP * i, Y_OFFSET),
                         (X_WALL - Y_STEP * i, Y_OFFSET + Y_STEP * 5), width=1)

    in_air.draw(screen)
    in_basket.draw(screen)
    in_wall.draw(screen)
    in_back.draw(screen)
    gr_basket.draw(screen)

    pygame.display.flip()

# pygame.quit()
