import pygame
import random
import math

screen_width = 1920
screen_height = 1080
fps = 60



class Margins():
    def __init__(self, up, down, left, right):
        self.up = up
        self.down = down
        self.left = left
        self.right = right

class Camera():
    def __init__(self, x, y, world_width, world_height, pixel_width, pixel_height):
        self.world_width = world_width
        self.world_height = world_height  #height in world units
        self.pixel_width = pixel_width
        self.pixel_height = pixel_height
        self.x = x
        self.y = y
        self.softzone = Margins(150, 75, 300, 300)
        self.deadzone = Margins(100, 50, 100, 100)
        self.camera_follow_speed = 3
        
    def moveCamera(self, player: Player):
        # deadzone
        ## right
        if player.x - self.x + player.width > self.world_width - self.deadzone.right:
            self.x = player.x - self.world_width + player.width + self.deadzone.right
        ## left
        if player.x - self.x < self.deadzone.left:
            self.x = player.x - self.deadzone.left
        ## down
        if player.y - self.y + player.height > self.world_height - self.deadzone.down:
            self.y = player.y - self.world_height + player.height + self.deadzone.down
        ##up
        if player.y - self.y < self.deadzone.up:
            self.y = player.y - self.deadzone.up

        # softzone
        ## right
        if player.x - self.x + player.width > self.world_width - self.softzone.right:
            self.x += self.camera_follow_speed
        ## left
        if player.x - self.x < self.softzone.left:
            self.x -= self.camera_follow_speed
        ## down
        if player.y - self.y + player.height > self.world_height - self.softzone.down:
            self.y += self.camera_follow_speed
        ##up
        if player.y - self.y < self.softzone.up:
            self.y -= self.camera_follow_speed


class Player():
    def __init__(self, x, y, width, height, camera: Camera):
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.camera = camera
        self.speed = 4
        self.gravity = 0.33
        self.acceleration_y = 0
        self.dx = 0
        self.dy = 0
        
        self.animation_frame = 0
        self.animation_speed = 0.2
        self.animation_walk = 0
        self.animation_fall = 1
        self.animation_ascending = 2
        self.animation_dash = 3
        self.animation_cdash = 4
        self.animation_charging_cdash = 5
        self.animation_claw = 6
        self.animation_cdash_stop_wall = 7
        self.animation_cdash_stop = 8
        self.current_animations = [
                                    False, # walking
                                    False, # falling
                                    False, # jumping(going up)
                                    False, # dashing
                                    False, # cdashing
                                    False, # charging cdash
                                    False, # claw
                                    False, # cdash stop wall
                                    False, # cdash stop
                                ]
        self.looking_dir = 1

        # jump
        self.jump_timer = 0
        self.jump_timer_last_frame = -1
        self.jump_speed = 5
        self.jump_time = 30 # max jump ascension time in frames
        self.touch_check_height = 0.01 # height of the ground / head collision boxes
        self.touch_check_width = 0.01 # width of the wall cling box
        self.grounded = False
        self.head_clipping = False
        self.can_jump = False
        self.jump_exit_speed = -1.5

        # wall jump
        self.wall_to_right = False
        self.wall_to_left = False
        self.wall_ride = False
        self.wall_ride_speed = 2
        self.wall_push_timer = -1
        self.wall_push_time = 5
        self.wall_push_speed = 5
        self.wall_jump_time = 15
        self.wall_push_direction = 1

        # double jump
        self.can_double_jump = False
        self.double_jump_time = 20
        self.double_jump_timer = 0
        self.double_jump_timer_last_frame = -1
        self.double_jump_speed = 7
        self.double_jump_exit_speed = -2
        
        # dash
        self.can_dash = False
        self.dash_speed = 20
        self.dash_timer = 0
        self.dash_time = 12
        self.dash_direction = 1

        #cdash
        self.can_cdash = False
        self.cdash_speed = 15
        self.cdash_charge_time = 50
        self.cdash_wall_stun_time = 20
        self.cdash_stop_time = 30
        self.cdash_stop_timer = 0
        self.cdash_stopping = False
        self.cdash_stop_wall = False
        self.cdash_charge_timer = 0

        # CONTROLS
        self.buttons_last_frame = []
        self.jump_key = pygame.K_z
        self.left_key = pygame.K_LEFT
        self.right_key = pygame.K_RIGHT
        self.dash_key = pygame.K_LSHIFT
        self.cdash_key = pygame.K_c
        self.in_cdash = False
        self.cdash_timer = 0

    def move(self, buttons, world: World):
        self.jump_timer_last_frame = self.jump_timer
        self.double_jump_timer_last_frame = self.double_jump_timer
        
        dy_last_frame = self.dy
        dx_last_frame = self.dx
        self.dx = 0
        # self.dy = 0

        
        # gravity
        self.dy += self.gravity
        if self.grounded:
            self.dy = 0

        self.current_animations[self.animation_walk] = False
        if not self.in_cdash and not self.cdash_stopping and self.cdash_charge_timer <= 0:
            # basic movement (left-right)
            if buttons[self.left_key] and not buttons[self.right_key]:
                self.dx -= self.speed
                self.looking_dir = -1
                self.current_animations[self.animation_walk] = True
            if buttons[self.right_key] and not buttons[self.left_key]:
                self.dx += self.speed
                self.looking_dir = 1
                self.current_animations[self.animation_walk] = True

            # claw 
            self.wall_ride = False
            if (self.wall_to_left or self.wall_to_right) and not self.grounded and dy_last_frame >= 0:
                self.wall_ride = True
            if self.wall_to_left and self.wall_ride:
                self.looking_dir = 1
                self.dash_direction = 1
            if self.wall_to_right and self.wall_ride:
                self.looking_dir = -1
                self.dash_direction = -1

            # jump and claw jump (and some double jump)
            self.jump_timer -= 1
            self.wall_push_timer -= 1

            if not buttons[self.jump_key] or (self.grounded and self.wall_ride) or self.head_clipping:
                self.jump_timer = 0

            if not buttons[self.jump_key]:
                self.can_jump = True

            # if self.double_jump_timer == 0 and 
            if (buttons[self.jump_key] and (self.grounded or self.wall_ride) and self.can_jump) or self.jump_timer > 0:
                if self.grounded:
                    self.can_jump = False
                    self.jump_timer = self.jump_time

                if self.wall_ride:
                    self.can_jump = False
                    self.jump_timer = self.wall_jump_time

                    self.wall_push_timer = self.wall_push_time
                    if self.wall_to_left:
                        self.wall_push_direction = 1
                    if self.wall_to_right:
                        self.wall_push_direction = -1
                if self.wall_push_timer >= 0:
                    self.dx = self.wall_push_speed * self.wall_push_direction

                self.dy = -self.jump_speed
                self.acceleration_y=0

            # double jump
            self.double_jump_timer -= 1

            if not buttons[self.jump_key] or (self.grounded and self.wall_ride) or self.head_clipping:
                self.double_jump_timer = 0

            if self.grounded or self.wall_ride:
                self.can_double_jump = True
            
            if (self.can_double_jump and buttons[self.jump_key] and not self.buttons_last_frame[self.jump_key] and not (self.grounded or  self.wall_ride)) or self.double_jump_timer > 0:
                if self.can_double_jump:
                    self.can_double_jump = False
                    self.double_jump_timer = self.double_jump_time
                self.dy = -self.jump_speed
            

            # claw
            if self.wall_ride:
                self.dy = self.wall_ride_speed

            # dash
            if buttons[self.left_key]:
                self.dash_direction = -1
            if buttons[self.right_key]:
                self.dash_direction = 1

            self.dash_timer -= 1
            if self.grounded or self.wall_ride:
                self.can_dash = True
            if buttons[self.dash_key] and not self.buttons_last_frame[self.dash_key] and self.dash_timer <= 0 and self.can_dash:
                self.can_dash = False
                self.dash_timer = self.dash_time
                self.dash_speed_current = self.dash_speed * self.dash_direction
            if self.dash_timer > 0:
                self.dx = self.dash_speed_current * math.sin(self.dash_timer / self.dash_time)
                self.dy = 0
                self.acceleration_y = 0
                self.looking_dir = self.dash_speed_current // self.dash_speed
                self.dash_direction = self.dash_speed_current // self.dash_speed

            # jump / doublejump end
            if self.jump_timer == 0 and self.jump_timer_last_frame > 0:
                self.dy = self.jump_exit_speed
            if self.double_jump_timer == 0 and self.double_jump_timer_last_frame > 0:
                self.dy = self.double_jump_exit_speed

        if self.dash_timer <= 0:
            #cdash
            self.can_cdash = (self.grounded or self.wall_ride) and not self.in_cdash
            
            if self.can_cdash and buttons[self.cdash_key]:
                self.cdash_charge_timer += 1
                self.dx = 0
                if self.wall_ride and not self.in_cdash:
                    self.dy = 0
            if self.cdash_charge_timer >= self.cdash_charge_time and not buttons[self.cdash_key]:
                self.in_cdash = True
                self.cdash_timer = 0
            if self.in_cdash:
                self.dx = self.looking_dir * self.cdash_speed
                self.dy = 0
                self.cdash_timer += 1
            if buttons[self.jump_key] and self.in_cdash and self.cdash_timer > 3:
                self.in_cdash = False
                self.cdash_stopping = True
                self.cdash_stop_timer = self.cdash_stop_time
            if (self.wall_to_left or self.wall_to_right) and self.in_cdash and self.cdash_timer > 3:
                self.in_cdash = False
                self.cdash_stop_wall = True
                self.cdash_stop_timer = self.cdash_wall_stun_time
            if self.cdash_stopping:
                self.cdash_stop_timer -= 1
                self.dx = self.looking_dir * (self.cdash_speed * (self.cdash_stop_timer / self.cdash_stop_time))
                self.dy = 0
            if self.cdash_stop_wall:
                self.cdash_stop_timer -= 1
                self.dx = 0
                self.dy = 0
            if self.cdash_stop_timer <= 0 and (self.cdash_stopping or self.cdash_stop_wall):
                self.cdash_stopping = False
                self.cdash_stop_wall = False
            if not buttons[self.cdash_key]:
                self.cdash_charge_timer = 0



        self.x += self.dx
        self.y += self.dy

        self.collisionPush(world)
        self.touchCheck(world)
        self.camera.moveCamera(self)

        self.buttons_last_frame = buttons
        
        self.current_animations[self.animation_claw] = self.wall_ride

        self.current_animations[self.animation_charging_cdash] = False
        if self.cdash_charge_timer > 0 and not self.in_cdash and not self.cdash_stopping:
            self.current_animations[self.animation_charging_cdash] = True
        
        self.current_animations[self.animation_cdash] = False
        if self.in_cdash:
            self.current_animations[self.animation_cdash] = True

        self.current_animations[self.animation_cdash_stop] = False
        if self.cdash_stopping:
            self.current_animations[self.animation_cdash_stop] = True

        self.current_animations[self.animation_cdash_stop_wall] = False
        if self.cdash_stop_wall:
            self.current_animations[self.animation_cdash_stop_wall] = True
        # self.animation_walk = 0             done
        # self.animation_fall = 1             
        # self.animation_ascending = 2        
        # self.animation_dash = 3             
        # self.animation_cdash = 4            
        # self.animation_charging_cdash = 5   done
        # self.animation_claw = 6             done
        # self.animation_cdash_stop_wall = 7
        # self.animation_cdash_stop = 8
    
    @staticmethod
    def twoDigitNum(n):
        if int(n) < 10:
            return '0' + n
        return n

    def animate(self, surface: pygame.surface.Surface):
        x, y, width, height = self.draw(surface)
        x += width / 2
        y += height / 2
        self.animation_frame += 1
        image_name = 'assets/the-knight/001.Idle/001-' + self.twoDigitNum(str(int(self.animation_frame*self.animation_speed) % 9)) + '.png'
        flip = 1
        if self.current_animations[self.animation_walk]:
            image_name = 'assets/the-knight/005.Run/005-' + self.twoDigitNum(str(int(self.animation_frame*self.animation_speed) % 10 + 3)) + '.png'
            flip = 1
        if self.current_animations[self.animation_claw]:
            image_name = 'assets/the-knight/084.Wall Slide/084-' + self.twoDigitNum(str(int(self.animation_frame*self.animation_speed) % 4)) + '.png'
            flip = -1
        if self.current_animations[self.animation_charging_cdash]:
            flip = 1
            if self.cdash_charge_timer < self.cdash_charge_time:
                image_name = 'assets/the-knight/085.SD Charge Ground/085-' + self.twoDigitNum(str(int(self.cdash_charge_timer / self.cdash_charge_time * 8) % 8)) + '.png'
            else:
                image_name = 'assets/the-knight/085.SD Charge Ground/085-' + self.twoDigitNum(str(int(self.cdash_charge_timer / self.cdash_charge_time * 8) % 4 + 4)) + '.png'
        if self.current_animations[self.animation_cdash]:
            flip = 1
            image_name = 'assets/the-knight/086.SD Dash/086-' + self.twoDigitNum(str(int(self.animation_frame*self.animation_speed) % 4)) + '.png'
            # flip = -int(self.dx / abs(self.dx))
        if self.current_animations[self.animation_cdash_stop]:
            flip = 1
            image_name = 'assets/the-knight/088.SD Charge Ground End/088-' + self.twoDigitNum(str(int((self.cdash_stop_time - self.cdash_stop_timer) / self.cdash_stop_time * 4) % 4)) + '.png'
            # flip = -int(self.dx / abs(self.dx))
        if self.current_animations[self.animation_cdash_stop_wall]:
            flip = 1
            image_name = 'assets/the-knight/091.SD Hit Wall/091-00.png'
        if self.current_animations[self.animation_charging_cdash] and self.current_animations[self.animation_claw]:
            flip = -1
            if self.cdash_charge_timer < self.cdash_charge_time:
                image_name = 'assets/the-knight/097.SD Wall Charge/097-' + self.twoDigitNum(str(int(self.cdash_charge_timer / self.cdash_charge_time * 9) % 9)) + '.png'
            else:
                image_name = 'assets/the-knight/097.SD Wall Charge/097-' + self.twoDigitNum(str(int(self.cdash_charge_timer / self.cdash_charge_time * 9) % 2 + 7)) + '.png'

        
        if self.looking_dir * flip == 1:
            sprite = pygame.transform.flip(pygame.image.load(image_name).convert_alpha(), True, False)
        else:
            sprite = pygame.image.load(image_name).convert_alpha()
        x -= sprite.get_width() / 2
        y -= sprite.get_height() / 2
        surface.blit(sprite, (x, y)) # cekaj

    def draw(self, surface):
        screen_x = (self.x - self.camera.x) / self.camera.world_width * self.camera.pixel_width
        screen_y = (self.y - self.camera.y) / self.camera.world_height * self.camera.pixel_height
        width = self.width / self.camera.world_width * self.camera.pixel_width
        height = self.height / self.camera.world_height * self.camera.pixel_height

        # pygame.draw.rect(surface, (255, 0, 0), (screen_x, screen_y, width, height))
        return screen_x, screen_y, width, height
    def worldColliding(self, world: World):
        for platform in world.platforms:
            if platform.playerCollision(self):
                return True
        return False
    
    def collisionPush(self, world: World):
        for platform in world.platforms:
            if not platform.playerCollision(self):
                continue
            overlap_x = min(self.x + self.width - platform.x, platform.x + platform.width - self.x)
            overlap_y = min(self.y + self.height - platform.y, platform.y + platform.height - self.y)
            
            if overlap_x < overlap_y:
                if self.x < platform.x:
                    self.x -= overlap_x
                else:
                    self.x += overlap_x
            else:
                if self.y < platform.y:
                    self.y -= overlap_y
                else:
                    self.y += overlap_y

    def touchCheck(self, world: World):
        self.grounded = False
        self.head_clipping = False
        self.wall_to_right = False
        self.wall_to_left = False

        feet_box = AxisAlignedBox(self.x, self.y + self.touch_check_height + self.height, self.width, self.touch_check_height)
        head_box = AxisAlignedBox(self.x, self.y - self.touch_check_height, self.width, self.touch_check_height)
        left_box = AxisAlignedBox(self.x - self.touch_check_width, self.y + self.height / 4, self.touch_check_width, self.height / 2)
        right_box = AxisAlignedBox(self.x + self.width, self.y + self.height / 4, self.touch_check_width, self.height / 2)

        if world.AABColliding(feet_box):
            self.grounded = True
        if world.AABColliding(head_box):
            self.head_clipping = True
        if world.AABColliding(left_box):
            self.wall_to_left = True
        if world.AABColliding(right_box):
            self.wall_to_right = True


class AxisAlignedBox():
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    def draw(self, surface, camera):
        screen_x = (self.x - camera.x) / camera.world_width * camera.pixel_width
        screen_y = (self.y - camera.y) / camera.world_height * camera.pixel_height
        width = self.width / camera.world_width * camera.pixel_width
        height = self.height / camera.world_height * camera.pixel_height

        pygame.draw.rect(surface, (0, 255, 0), (screen_x, screen_y, width, height))
    def playerCollision(self, player: Player):
        return (self.x < player.x + player.width and
                self.x + self.width > player.x and
                self.y < player.y + player.height and
                self.y + self.height > player.y)
    def AABCollision(self, box: AxisAlignedBox):
        return (self.x < box.x + box.width and
                self.x + self.width > box.x and
                self.y < box.y + box.height and
                self.y + self.height > box.y)
    
# class AxisAlignedLine():
#     def __init__(self, x, y, len, is_horizontal: bool):
#         self.x = x
#         self.y = y
#         self.len = len # signed length
#         self.is_horizontal = is_horizontal

class World():
    def __init__(self, platforms: list[AxisAlignedBox]):
        self.platforms = platforms
    def draw(self, surface, camera):
        for platform in self.platforms:
            platform.draw(surface, camera)
    def AABColliding(self, box: AxisAlignedBox):
        for platform in self.platforms:
            if platform.AABCollision(box):
                return True
        return False


def main():
    pygame.init()

    global window
    window = pygame.display.set_mode((screen_width, screen_height))

    camera = Camera(0, 0, 768, 432, screen_width, screen_height)
    player = Player(20, 20, 18, 51, camera)

    world = World(
        [
            AxisAlignedBox(-1000, 250, 4000, 300),
            AxisAlignedBox(50, 125, 100, 20),
            AxisAlignedBox(350, 125, 100, 20),
            AxisAlignedBox(175, 0, 100, 200),
            AxisAlignedBox(50, -125, 100, 20),
            AxisAlignedBox(175, -250, 100, 20),
        ]
    )

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        buttons = pygame.key.get_pressed()

        window.fill((50, 100, 240))
        player.move(buttons, world)
        world.draw(window, camera)
        player.animate(window)

        pygame.display.flip()
        pygame.time.delay(int(1000 / fps))





if __name__ == "__main__":
    main()