from sys import exit
import pygame
import game_init as g
from sprites import Leave, Snowflake, Bonus
from datetime import date


def dialog_win(cont):
    titles = ["Next Level", "Pause", "Game Over", "Save Score"]
    colors = [(g.BLACK, g.MAGENTA), (g.MAGENTA, g.BLACK), (g.BLUE, g.BLACK), (g.GREEN, g.GREEN)]
    g.pause = True
    dialog = g.dialog_bg[cont].copy()
    dialog.set_colorkey(g.WHITE)
    dialog_rect = dialog.get_rect()
    draw_text(dialog, titles[cont], g.font_mid, colors[cont][0], 380, 150)
    if cont == g.SAVE_SCORE:
        draw_value(dialog, "Счет", g.score, g.font_mid, g.BLACK, g.MAGENTA, 350, 220)
        g.username = enter_name(dialog)
        g.pause = False
        return
    elif cont:
        draw_value(dialog, "Счет", g.score, g.font_mid, g.BLACK, g.MAGENTA, 350, 220)
        draw_value(dialog, "i", "Инструкция", g.font_small, colors[cont][0], colors[cont][1], 300, 320)
        draw_value(dialog, "t", "Таблица рекордов", g.font_small, colors[cont][0], colors[cont][1], 300, 340)
        draw_value(dialog, "ESCAPE", "Закончить игру", g.font_small, colors[cont][0], colors[cont][1], 300, 360)
        draw_value(dialog, "ENTER", "Начать игру заново", g.font_small, colors[cont][0], colors[cont][1], 300, 380)
        if cont == g.GAME_OVER and g.lives > 1 or cont == g.PAUSE_GAME:
            draw_value(dialog, "SPACE", "Продолжить игру", g.font_small, colors[cont][0], colors[cont][1], 300, 400)
    else:
        draw_value(dialog, "Уровень", g.level, g.font_mid, colors[cont][0], colors[cont][1], 420, 270)
        draw_value(dialog, g.goal_name[g.goal_type], g.goal_val, g.font_mid, colors[cont][0], colors[cont][1], 420, 320)

    g.screen.blit(g.bg, g.bg_rect)
    g.screen.blit(dialog, ((g.WIDTH - dialog_rect.width) // 2, 0))
    pygame.display.flip()
    run = True
    while run:
        g.clock.tick(g.FPS)
        g.screen.blit(g.bg, g.bg_rect)
        g.screen.blit(dialog, ((g.WIDTH - dialog_rect.width) // 2, 0))
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
                        if cont == g.GAME_OVER and g.lives > 1:
                            g.lives -= 1
                            g.health = 3
                            level_reset()
                            run = False
                        elif cont == g.PAUSE_GAME:
                            run = False
                    elif ev.key == pygame.K_i:
                        info()
                    elif ev.key == pygame.K_t:
                        top_score()
                else:
                    run = False
        pygame.display.flip()
    g.pause = False


def level_reset():
    g.level_data = g.cur.execute(f"SELECT * FROM levels WHERE id = {g.level}").fetchone()
    g.wind_speed, g.leave_delay, g.goal_type, g.goal_val, g.different = g.level_data[1:]
    g.wall = [[0] * 5 for _ in range(5)]
    g.leave_stack = []
    pygame.time.set_timer(g.EV_ADDLEAVE, g.leave_delay)
    g.in_air.empty()
    g.in_basket.empty()
    g.in_wall.empty()
    g.in_back.empty()
    g.screen.blit(g.bg, g.bg_rect)
    pygame.display.flip()
    dialog_win(g.NEXT_LEVEL)


def game_reset():
    g.lives = 3
    g.health = 3
    g.score = 0
    g.level = 1
    level_reset()


def level_bonus():
    g.pause = True
    gr = pygame.sprite.Group()
    gr.add(g.in_back.sprites())
    gr.add(g.in_air.sprites())
    gr.add(g.in_basket.sprites())
    gr.add(g.in_wall.sprites())
    for i in range(5):
        for j in range(5):
            if not g.wall[i][j]:
                snowflake = Snowflake(i, j)
                gr.add(snowflake)
    for elem in gr:
        if elem():
            bon = g.points[0][1]
        else:
            bon = g.points[0][2]
        g.score += bon
        bonus = Bonus(bon, elem.rect.x, elem.rect.y, 10, True)
        g.gr_basket.add(bonus)
        elem.kill()
        for _ in range(7):
            g.clock.tick(g.FPS)
            g.gr_basket.update()
            g.screen.blit(g.bg, g.bg_rect)
            draw_value(g.screen, "Счет", g.score, g.font_mid, g.BLUE, g.MAGENTA, 200, 10)
            gr.draw(g.screen)
            g.gr_basket.draw(g.screen)
            pygame.display.flip()
    level_reset()


def check_wall():
    res = set()
    combs = 0
    accum = 0
    for i in range(5):  # Горизонтали
        if g.wall[i][2]:
            cnt = [(i, 2)]
            if g.wall[i][1] and g.wall[i][2]() == g.wall[i][1]():
                cnt.append((i, 1))
                if g.wall[i][0] and g.wall[i][2]() == g.wall[i][0]():
                    cnt.append((i, 0))
            if g.wall[i][3] and g.wall[i][2]() == g.wall[i][3]():
                cnt.append((i, 3))
                if g.wall[i][4] and g.wall[i][2]() == g.wall[i][4]():
                    cnt.append((i, 4))
            if len(cnt) > 2:
                accum += g.points[1][len(cnt) - 3]
                combs += 1
                if g.goal_type == g.G_COMBY:
                    g.goal_val -= (len(cnt) - 2)
                res = res | set(cnt)
    for i in range(5):  # Вертикали
        if g.wall[2][i]:
            cnt = [(2, i)]
            if g.wall[1][i] and g.wall[2][i]() == g.wall[1][i]():
                cnt.append((1, i))
                if g.wall[0][i] and g.wall[2][i]() == g.wall[0][i]():
                    cnt.append((0, i))
            if g.wall[3][i] and g.wall[2][i]() == g.wall[3][i]():
                cnt.append((3, i))
                if g.wall[4][i] and g.wall[2][i]() == g.wall[4][i]():
                    cnt.append((4, i))
            if len(cnt) > 2:
                accum += g.points[2][len(cnt) - 3]
                combs += 1
                if g.goal_type in [g.G_COMBY, g.G_HORIZ]:
                    g.goal_val -= (len(cnt) - 2)
                res = res | set(cnt)
    matr: list[list] = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]] + g.wall.copy() + [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
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
                accum += g.points[3][len(cnt) - 3]
                combs += 1
                if g.goal_type in [g.G_COMBY, g.G_DIAGS]:
                    g.goal_val -= (len(cnt) - 2)
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
                accum += g.points[3][len(cnt) - 3]
                combs += 1
                if g.goal_type in [g.G_COMBY, g.G_DIAGS]:
                    g.goal_val -= (len(cnt) - 2)
                res = res | set(cnt)
    accum *= combs
    if g.goal_type == g.G_POINT:
        g.goal_val -= accum
    g.score += accum
    if accum:
        bonus = Bonus(accum, g.X_WALL - 300, 450)
        g.gr_basket.add(bonus)
    return res


def squeeze_wall():
    for i in range(5):
        if g.wall[i] != [0, 0, 0, 0, 0]:
            while 0 in g.wall[i]:
                g.wall[i].remove(0)
            for j in range(len(g.wall[i])):
                g.wall[i][j].coord = (i, j)
            while len(g.wall[i]) < 5:
                g.wall[i].append(0)


def add_leave(group):
    if not g.pause:
        elem = Leave()
        group.add(elem)


def game_over():
    if g.lives == 1 and g.score > 5000:
        dialog_win(g.SAVE_SCORE)
    dialog_win(g.GAME_OVER)


def enter_name(surf):
    x = 150
    y = 350
    w = 400
    h = 27
    cur_flash = False
    cnt = 0
    uname = g.username
    surf_rect = surf.get_rect()
    comment_surface = g.font_small.render("Введите ваше имя:", True, g.GREEN)
    comment_rect = comment_surface.get_rect()
    comment_rect.bottomleft = (x, y)
    l_rect = g.health_pics[0].get_rect()
    run = True
    while run:
        g.clock.tick(g.FPS)
        cnt += 1
        if cnt == 25:
            cur_flash = not cur_flash
            cnt = 0
        pygame.draw.rect(surf, g.BLACK, (x - 12, y - 2, w + 4, h + 4), 2, 10)
        pygame.draw.rect(surf, g.YELLOW, (x - 10, y, w, h), 0, 10)
        text_surface = g.font_small.render(uname, True, g.BLACK)
        text_rect = text_surface.get_rect()
        text_rect.topleft = (x, y)
        surf.blit(text_surface, text_rect)
        surf.blit(comment_surface, comment_rect)
        if cur_flash:
            l_rect.topleft = (x + text_rect.width, y - 1)
            surf.blit(g.health_pics[0], l_rect)
        g.screen.blit(g.bg, g.bg_rect)
        g.screen.blit(surf, ((g.WIDTH - surf_rect.width) // 2, 0))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                goodbye()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    if not uname:
                        uname = "NEMO"
                    new_rec = (None, g.score, g.level, date.today(), uname)
                    g.cur.execute("INSERT INTO scores VALUES (?,?,?,?,?)", new_rec)
                    g.con.commit()
                    return uname
                elif ev.key == pygame.K_BACKSPACE and len(uname):
                    uname = uname[:-1]
                elif pygame.K_SPACE <= ev.key <= pygame.K_z and len(uname) < 20:
                    uname += ev.unicode.upper()
        pygame.display.flip()


def draw_health(text, val, tcolor, x, y, mult=0):
    text_surface = g.font_small.render(text, True, tcolor)
    text_rect = text_surface.get_rect()
    text_rect.midright = (x, y)
    g.screen.blit(text_surface, text_rect)
    l_rect = g.health_pics[0].get_rect()
    for i in range(val):
        l_rect.midleft = (x, y)
        g.screen.blit(g.health_pics[min([mult * 4 + i, mult * 4 + 3])], l_rect)
        x += 12


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
    f.close()
    g.screen.fill(g.YELLOW)
    draw_text(g.screen, "Правила игры", g.font_mid, g.GREEN, 200, 10, False)
    draw_text(g.screen, text[0], g.font_small, g.BLUE, 200, 65, False)
    draw_text(g.screen, "Управление", g.font_mid, g.GREEN, 200, 325, False)
    keys = text[1].split('\n')
    y = 380
    for key in keys:
        if key:
            k = key.split(": ")
            draw_value(g.screen, k[0], k[1], g.font_small, g.MAGENTA, g.BLUE, 320, y)
            y += 20
    draw_text(g.screen, "Автор", g.font_mid, g.GREEN, 800, 325, False)
    draw_text(g.screen, text[2], g.font_small, g.BLUE, 800, 380, False)
    pygame.display.flip()
    run = True
    while run:
        g.clock.tick(g.FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                goodbye()
            if ev.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                run = False


def top_score():
    x = [100, 150, 300, 350, 500]
    c = [g.BLUE, g.MAGENTA, g.GREEN, g.BLUE, g.MAGENTA]
    header = ["#", "Счет", "Уров", "   Дата", "Имя"]
    g.screen.fill(g.YELLOW)
    draw_text(g.screen, "Таблица рекордов", g.font_mid, g.BLUE, 150, 10, False)
    res = g.cur.execute("SELECT * FROM scores ORDER BY score DESC LIMIT 20").fetchall()
    for j in range(1, 5):
        draw_text(g.screen, header[j], g.font_small, g.BLACK, x[j], 60, False)
    for i in range(len(res)):
        for j in range(1, 5):
            draw_text(g.screen, str(res[i][j]), g.font_small, c[j], x[j], i * 20 + 85, False)
    pygame.display.flip()
    run = True
    while run:
        g.clock.tick(g.FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                goodbye()
            if ev.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                run = False


def goodbye():
    g.pause = False
    g.infinity = True
    g.different = g.NUM_LEAVES - 1
    pygame.time.set_timer(g.EV_ADDLEAVE, 200)
    gr = pygame.sprite.Group()
    if not pygame.mixer.Sound.get_num_channels(g.intro_sound):
        g.intro_sound.play()
    g.screen.fill(g.BLACK)
    while 1:
        g.clock.tick(g.FPS)
        for ev in pygame.event.get():
            if ev.type in [pygame.QUIT, pygame.KEYDOWN]:
                pygame.quit()
                exit()
            if ev.type == g.EV_ADDLEAVE:
                add_leave(gr)
        gr.update(0)
        gr.draw(g.screen)
        draw_text(g.screen, "Goodbye, press any key...", g.font_mid, g.GREEN, g.WIDTH // 2, 10)
        draw_text(g.screen, "http://kise-lev.ru", g.font_mid, g.MAGENTA, g.WIDTH // 2, g.HEIGHT - 60)
        pygame.display.flip()


def intro():
    g.infinity = True
    g.different = g.NUM_LEAVES - 1
    pygame.time.set_timer(g.EV_ADDLEAVE, 200)
    gr = pygame.sprite.Group()
    g.intro_sound.play()
    run = True
    while run:
        g.clock.tick(g.FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                goodbye()
            if ev.type == g.EV_ADDLEAVE:
                add_leave(gr)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE:
                    run = False
                    g.intro_sound.stop()
                    g.infinity = False
                if ev.key == pygame.K_RETURN:
                    run = False
                    info()
                    g.intro_sound.stop()
                    g.infinity = False

        g.screen.blit(g.bg, g.bg_rect)
        gr.update(0)
        gr.draw(g.screen)
        draw_text(g.screen, "Осенний ветер", g.font_big, g.BLUE, g.WIDTH // 2 + 3, 103)
        draw_text(g.screen, "Осенний ветер", g.font_big, g.WHITE, g.WIDTH // 2, 100)
        draw_value(g.screen, "ENTER", "Инструкция", g.font_mid, g.MAGENTA, g.WHITE, 400, 420)
        draw_value(g.screen, "SPACE", "Старт", g.font_mid, g.MAGENTA, g.WHITE, 1000, 420)
        pygame.display.flip()
