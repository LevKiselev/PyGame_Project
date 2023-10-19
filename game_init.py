import pygame
import sqlite3
from sprites import Basket


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
EV_SQUEEZEW = pygame.USEREVENT + 4
EV_GAMEOVER = pygame.USEREVENT + 5

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
destroy_set = set()
level_data = (level, wind_speed, leave_delay, goal_type, goal_val, different)
username = ""
pause = False
infinity = False

wall: list[list] = [[0] * 5 for _ in range(5)]

con = sqlite3.connect("data/gamedata.db")
cur = con.cursor()

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
for i in range(4):
    health_pics.append(pygame.transform.scale(leave_pics[i + 6], (30, 30)))
    health_pics[i + 4].set_colorkey(TRANSP)

icon = pygame.image.load("data/pics/icon32.png").convert()
icon.set_colorkey(WHITE)
pygame.display.set_icon(icon)

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

in_air = pygame.sprite.Group()
in_back = pygame.sprite.Group()
in_basket = pygame.sprite.Group()
gr_basket = pygame.sprite.Group()
in_wall = pygame.sprite.Group()

basket = Basket()
gr_basket.add(basket)
