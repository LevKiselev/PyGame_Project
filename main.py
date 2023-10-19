import pygame
import game_init as g
from functions import dialog_win, game_reset, game_over, add_leave, goodbye, squeeze_wall, \
                      check_wall, level_bonus, intro, draw_value, draw_health

intro()
game_reset()

while 1:
    g.clock.tick(g.FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            goodbye()
        if event.type == g.EV_ADDLEAVE:
            add_leave(g.in_air)
        if event.type == g.EV_BASKETUP:
            g.basket.up()
        if event.type == g.EV_BASKETDN:
            g.basket.down()
        if event.type == g.EV_SQUEEZEW:
            squeeze_wall()
        if event.type == g.EV_GAMEOVER:
            game_over()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                g.basket.back()
            elif event.key == pygame.K_RIGHT:
                g.wind_speed = 10
                pygame.time.set_timer(g.EV_ADDLEAVE, 500)
            elif event.key == pygame.K_SPACE:
                g.basket.drop()
            elif event.key == pygame.K_UP:
                g.basket.up()
                pygame.time.set_timer(g.EV_BASKETUP, 150)
            elif event.key == pygame.K_DOWN:
                g.basket.down()
                pygame.time.set_timer(g.EV_BASKETDN, 150)
            else:
                dialog_win(g.PAUSE_GAME)
                add_leave(g.in_air)
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_RIGHT:
                g.wind_speed = g.level_data[1]
                pygame.time.set_timer(g.EV_ADDLEAVE, g.leave_delay)
            elif event.key == pygame.K_UP:
                pygame.time.set_timer(g.EV_BASKETUP, 0)
            elif event.key == pygame.K_DOWN:
                pygame.time.set_timer(g.EV_BASKETDN, 0)

    g.destroy_set = check_wall()
    if g.destroy_set:
        g.in_wall.update(4)
        g.destroy_set = set()
    if g.goal_val <= 0:
        g.level += 1
        if g.health < 10:
            g.health += 1
        else:
            g.health = 3
            g.lives += 1
        level_bonus()

    g.in_air.update(1)
    g.in_basket.update(2)
    g.in_wall.update(3)
    g.in_back.update(5)
    g.gr_basket.update()

    g.screen.blit(g.bg, g.bg_rect)
    draw_health("Жизни: ", g.lives, g.BLUE, 750, 20)
    draw_health("Здоровье: ", g.health, g.BLUE, 750, 50, 1)
    draw_value(g.screen, "Уровень", g.level, g.font_small, g.BLUE, g.MAGENTA, g.WIDTH - 100, 10)
    draw_value(g.screen, g.goal_name[g.goal_type], g.goal_val, g.font_small, g.BLUE, g.MAGENTA, g.WIDTH - 100, 40)
    draw_value(g.screen, "Счет", g.score, g.font_mid, g.BLUE, g.MAGENTA, 200, 10)

    for i in range(6):
        pygame.draw.line(g.screen, g.WHITE, (g.X_WALL - g.Y_STEP * 5, g.Y_OFFSET + g.Y_STEP * i),
                         (g.X_WALL, g.Y_OFFSET + g.Y_STEP * i), width=1)
        pygame.draw.line(g.screen, g.WHITE, (g.X_WALL - g.Y_STEP * i, g.Y_OFFSET),
                         (g.X_WALL - g.Y_STEP * i, g.Y_OFFSET + g.Y_STEP * 5), width=1)

    g.in_air.draw(g.screen)
    g.in_basket.draw(g.screen)
    g.in_wall.draw(g.screen)
    g.in_back.draw(g.screen)
    g.gr_basket.draw(g.screen)

    pygame.display.flip()

# pygame.quit()
