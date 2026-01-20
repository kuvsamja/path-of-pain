import pygame
import random

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
        self.jump_timer = 0
        self.jump_speed = 5
        self.jump_time = 30 # max jump ascension time in frames
        self.touch_check_height = 0.01 # height of the ground / head collision boxes
        self.touch_check_width = 0.01 # width of the wall cling box
        self.grounded = False
        self.head_clipping = False
        self.can_jump = False
        self.wall_to_right = False
        self.wall_to_left = False
        self.wall_ride = False
        self.wall_ride_speed = 2
        self.wall_push_timer = -1
        self.wall_push_time = 5
        self.wall_push_speed = 5
        self.wall_jump_time = 15
        self.wall_push_direction = 1
        

        # CONTROLS
        self.jump_key = pygame.K_z
        self.left_key = pygame.K_LEFT
        self.right_key = pygame.K_RIGHT

    def move(self, buttons, world: World):

        dy_last_frame = self.dy
        dx_last_frame = self.dx
        self.dx = 0
        self.dy = 0

        # gravity
        self.acceleration_y += self.gravity
        if self.grounded:
            self.acceleration_y = 0

        # basic movement (left-right)
        if buttons[self.left_key]:
            self.dx -= self.speed
        if buttons[self.right_key]:
            self.dx += self.speed

        # jump
        self.jump_timer -= 1
        self.wall_push_timer -= 1

        if not buttons[self.jump_key] or (self.grounded and self.wall_ride) or self.head_clipping:
            self.jump_timer = 0

        if not buttons[self.jump_key]:
            self.can_jump = True

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
            self.dy = -self.jump_speed
            self.acceleration_y=0
        if self.wall_push_timer >= 0:
            self.dx = self.wall_push_speed * self.wall_push_direction

        # claw
        self.wall_ride = False
        if (self.wall_to_left or self.wall_to_right) and not self.grounded and dy_last_frame >= 0:
            self.wall_ride = True

        if self.wall_ride:
            self.acceleration_y = self.wall_ride_speed
    


        self.dy += self.acceleration_y
        self.x += self.dx
        self.y += self.dy

        self.collisionPush(world)
        self.touchCheck(world)
        self.camera.moveCamera(self)
        

    def draw(self, surface):
        screen_x = (self.x - self.camera.x) / self.camera.world_width * self.camera.pixel_width
        screen_y = (self.y - self.camera.y) / self.camera.world_height * self.camera.pixel_height
        width = self.width / self.camera.world_width * self.camera.pixel_width
        height = self.height / self.camera.world_height * self.camera.pixel_height

        pygame.draw.rect(surface, (255, 0, 0), (screen_x, screen_y, width, height))
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
        left_box = AxisAlignedBox(self.x - self.touch_check_width, self.y, self.touch_check_width, self.height)
        right_box = AxisAlignedBox(self.x + self.width, self.y, self.touch_check_width, self.height)
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

    window = pygame.display.set_mode((screen_width, screen_height))

    player_camera = Camera(0, 0, 768, 432, screen_width, screen_height)
    player = Player(20, 20, 20, 40, player_camera)

    world = World(
        [
            AxisAlignedBox(0, 250, 400, 300),
            AxisAlignedBox(50, 125, 100, 20),
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

        window.fill((0, 0, 0))
        player.move(buttons, world)
        player.draw(window)
        world.draw(window, player_camera)

        pygame.display.flip()
        pygame.time.delay(int(1000 / fps))





if __name__ == "__main__":
    main()