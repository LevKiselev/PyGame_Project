import game_init as g
import pygame
from random import randrange


class Basket(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.cur_pos = 2
        self.image = g.basket_empty
        self.image.set_colorkey(g.WHITE)
        self.rect = self.image.get_rect()
        self.rect.width = 20
        self.radius = 10
        self.rect.x = g.X_BASKET
        self.rect.y = self.cur_pos * g.Y_STEP + g.Y_OFFSET - 15

    def up(self):
        if self.cur_pos:
            self.cur_pos -= 1
            self.rect.y = self.cur_pos * g.Y_STEP + g.Y_OFFSET - 15

    def down(self):
        if self.cur_pos < 4:
            self.cur_pos += 1
            self.rect.y = self.cur_pos * g.Y_STEP + g.Y_OFFSET - 15

    def drop(self):
        if g.leave_stack and 0 in g.wall[self.cur_pos]:
            elem = g.leave_stack.pop()
            elem.add(g.in_wall)
            elem.remove(g.in_basket)
            empty = g.wall[self.cur_pos].index(0)
            g.wall[self.cur_pos][empty] = elem
            elem.coord = (self.cur_pos, empty)
            g.drop_sound.play()

    def back(self):
        if g.leave_stack:
            elem = g.leave_stack.pop()
            elem.add(g.in_back)
            elem.remove(g.in_basket)
            elem.coord = (self.cur_pos, g.X_BASKET - 100)
            g.back_sound.play()

    def update(self, *args):
        if len(g.leave_stack) < 5:
            self.image = g.basket_empty
        else:
            self.image = g.basket_full
        self.image.set_colorkey(g.WHITE)


class Bonus(pygame.sprite.Sprite):

    def __init__(self, val, x, y, speed=3, down=False):
        pygame.sprite.Sprite.__init__(self)
        text = "+" + str(val)
        if val > 5000:
            text += " !!!"
            g.big_bonus_sound.play()
        else:
            g.bonus_sound.play()
        self.image = g.font_mid.render(text, True, g.MAGENTA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed
        self.down = down

    def update(self):
        if self.down:
            self.rect.y += self.speed
            if self.rect.y > g.HEIGHT:
                self.kill()
        else:
            self.rect.x += self.speed
            if self.rect.x > g.WIDTH:
                self.kill()


class Leave(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.coord = (0, 0)
        self.leave_id = randrange(1, g.different + 1)
        self.image_src = g.leave_pics[self.leave_id]
        self.image_src.set_colorkey(g.TRANSP)
        self.image = self.image_src.copy()
        self.rect = self.image.get_rect()
        self.radius = int(g.Y_OFFSET * .2)
        self.rect.x = -g.Y_STEP
        self.rect.y = randrange(5) * g.Y_STEP + g.Y_OFFSET
        self.stepy = 0
        self.speedx = g.wind_speed
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

    def fly(self, forward=True):
        self.rotate()
        if forward:
            self.rect.x += self.speedx
            self.deltax += self.speedx
            if self.deltax > 16:
                self.rect.y += g.SINUS[self.stepy]
                self.stepy = (self.stepy + 1) % len(g.SINUS)
                self.deltax = 0
        else:
            self.rect.x -= 10
            if self.rect.left < 200:
                self.add(g.in_air)
                self.remove(g.in_back)
        if self.rect.left > g.X_DELLEAVE:
            if not g.infinity:
                g.fault_sound.play()
                g.health -= 1
                if g.health == 0:
                    pygame.event.post(pygame.event.Event(g.EV_GAMEOVER))
            self.kill()

    def update(self, *args):

        self.speedx = g.wind_speed
        if args[0] == 0:  # Полет листьев в заставке
            self.fly()
        if args[0] == 1:  # Полет листьев и попадание в корзину
            if (pygame.sprite.spritecollideany(self, g.gr_basket, pygame.sprite.collide_circle)
                    and len(g.leave_stack) < 5):
                self.add(g.in_basket)
                self.remove(g.in_air)
                g.score += g.points[0][0]
                if g.goal_type == g.G_POINT:
                    g.goal_val -= g.points[0][0]
                if g.goal_type == g.G_LEAVE:
                    g.goal_val -= 1
                self.image = self.image_src
                g.leave_stack.append(self)
                self.rect.x = g.X_BASKET + (5 - len(g.leave_stack)) * 20
                g.basket_sound.play()
            else:
                self.fly()
        if args[0] == 2:  # Перемещение листьев вместе с корзиной
            self.rect.y = g.basket.cur_pos * g.Y_STEP + g.Y_OFFSET
        if args[0] == 3:  # Листья в стене
            self.rect.x = g.X_WALL - (self.coord[1] + 1) * g.Y_STEP
        if args[0] == 4:  # Удаление листьев из стены
            if self.coord in g.destroy_set:
                snowflake = Snowflake(self.coord[0], self.coord[1])
                g.wall[self.coord[0]][self.coord[1]] = 0
                g.in_wall.add(snowflake)
                self.kill()
        if args[0] == 5:  # Отброс листа назад
            self.fly(False)


class Snowflake(Leave):

    def __init__(self, y, x):
        pygame.sprite.Sprite.__init__(self)
        self.coord = (y, x)
        self.leave_id = 0
        self.image_src = g.leave_pics[0]
        self.image_src.set_colorkey(g.TRANSP)
        self.image = self.image_src.copy()
        self.rect = self.image.get_rect()
        self.rect.y = y * g.Y_STEP + g.Y_OFFSET
        self.rect.x = g.X_WALL - (x + 1) * g.Y_STEP
        self.step = 0
        self.rot = 0
        self.rot_speed = 8

    def update(self, *args):
        if self.step < 20:
            self.rotate()
            self.image.set_alpha(self.step * 12)
            self.step += 1
        else:
            self.kill()
            if g.EV_SQUEEZEW not in pygame.event.get():
                pygame.event.post(pygame.event.Event(g.EV_SQUEEZEW))
