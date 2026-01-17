import pygame


screen_width = 800
screen_height = 600

class Camera():
    def __init__(self, x, y, world_width, world_height, pixel_width, pixel_height):
        self.world_width = world_width
        self.world_height = world_height  #height in world units
        self.pixel_width = pixel_width
        self.pixel_height = pixel_height
        self.x = x
        self.y = y


class Player():
    def __init__(self, x, y, width, height, camera: Camera):
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.camera = camera
        self.speed = 10

    def move(self, buttons):
        if buttons[pygame.K_LEFT]:
            self.x -= self.speed
        if buttons[pygame.K_RIGHT]:
            self.x += self.speed
        if buttons[pygame.K_DOWN]:
            self.y -= self.speed
        if buttons[pygame.K_UP]:
            self.y += self.speed

    def draw(self, surface):
        screen_x = (self.x - self.camera.x) / self.camera.world_width * self.camera.pixel_width
        screen_y = (self.y - self.camera.y) / self.camera.world_height * self.camera.pixel_height
        width = self.width / self.camera.world_width * self.camera.pixel_width
        height = self.height / self.camera.world_height * self.camera.pixel_height


        pygame.draw.rect(surface, (255, 0, 0), (screen_x, screen_height - screen_y, width, height))


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


        pygame.draw.rect(surface, (0, 255, 0), (screen_x, screen_height - screen_y, width, height))

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
    player = Player(20, 20, 10, 20, player_camera)

    world = World(
        [
            AxisAlignedBox(10, 10, 10, 10)
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
        player.draw(window)

        world.draw(window, player_camera)

        pygame.display.flip()
        pygame.time.delay(16)





if __name__ == "__main__":
    main()