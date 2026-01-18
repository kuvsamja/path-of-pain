import pygame
import random

screen_width = 800
screen_height = 600
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
        self.softzone = Margins(75, 75, 75, 75)
        self.deadzone = Margins(50, 50, 50, 50)
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
        self.grounded = False
        self.gravity = 20
        self.grav_acceleration = 0
        self.dx = 0
        self.dy = 0
        self.jump_timer = 0
        self.jump_speed = 5
        self.jump_time = 30 # max time to hold a jump
        self.head_clipping = False
        self.can_jump = False

    def move(self, buttons):
        self.dx = 0
        self.dy = 0
        self.jump_timer -= 1

        self.grav_acceleration += self.gravity
        if self.grounded:
            self.grav_acceleration = 0
        self.dy += self.grav_acceleration / fps
        if buttons[pygame.K_LEFT]:
            self.dx -= self.speed
        if buttons[pygame.K_RIGHT]:
            self.dx += self.speed

        if not buttons[pygame.K_UP] or self.grounded or self.head_clipping:
            self.jump_timer = 0
        if not buttons[pygame.K_UP]:
            self.can_jump = True
        if (buttons[pygame.K_UP] and self.grounded and self.can_jump) or self.jump_timer > 0:
            if self.grounded:
                self.can_jump = False
                self.jump_timer = self.jump_time # max jump time in frames
            
            self.dy = -self.jump_speed
            self.grav_acceleration=0

        self.x += self.dx
        self.y += self.dy

        

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
        self.grounded = False
        self.head_clipping = False
        
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
                    self.grounded = True
                else:
                    self.y += overlap_y
                    self.head_clipping = True
            # TODO: ADD PROPER COLLISION PUSHING INVOLVING DX AND DY



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
    

class World():
    def __init__(self, platforms: list[AxisAlignedBox]):
        self.platforms = platforms
    def draw(self, surface, camera):
        for platform in self.platforms:
            platform.draw(surface, camera)


def main():
    pygame.init()

    window = pygame.display.set_mode((screen_width, screen_height))

    player_camera = Camera(0, 0, 400, 300, screen_width, screen_height)
    player = Player(20, 20, 20, 40, player_camera)

    world = World(
        [
            AxisAlignedBox(0, 250, 400, 300),
            AxisAlignedBox(100, 200, 20, 10),
        ]
    )

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        buttons = pygame.key.get_pressed()

        window.fill((0, 0, 0))
        player.move(buttons)
        player.collisionPush(world)
        player_camera.moveCamera(player)
        player.draw(window)

        world.draw(window, player_camera)
        print(player.can_jump)
        pygame.display.flip()
        pygame.time.delay(int(1000 / fps))





if __name__ == "__main__":
    main()