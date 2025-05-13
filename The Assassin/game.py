import os  # Operating system interaction
import sys  # System-specific parameters and functions
import math  # Math functions
import random  # Random number generation

import pygame  # Pygame library for game development

# Import custom modules and classes for game components and utilities
from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Enemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark

class Game:  # Main game class
    def __init__(self):  # Initialization of the game
        pygame.init()  # Initialize pygame modules

        pygame.display.set_caption('The Assassin')  # Set window title
        self.screen = pygame.display.set_mode((640, 480))  # Create main screen window with size 640x480
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)  # Create smaller surface for rendering with alpha
        self.display_2 = pygame.Surface((320, 240))  # Create another surface for layered rendering

        self.clock = pygame.time.Clock()  # Create clock to control FPS
        
        self.movement = [False, False]  # Movement flags for left and right
        
        # Load all game assets such as images and animations in a dictionary for easy access
        self.assets = {
            'decor': load_images('tiles/decor'),  # Load decorative tiles images
            'grass': load_images('tiles/grass'),  # Load grass tiles images
            'large_decor': load_images('tiles/large_decor'),  # Load large decorative tiles images
            'stone': load_images('tiles/stone'),  # Load stone tiles images
            'player': load_image('entities/player.png'),  # Load player image (static)
            'background': load_image('background.png'),  # Load background image
            'clouds': load_images('clouds'),  # Load clouds images
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),  # Load enemy idle animation
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),  # Load enemy running animation
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),  # Player idle animation
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),  # Player running animation
            'player/jump': Animation(load_images('entities/player/jump')),  # Player jumping animation
            'player/slide': Animation(load_images('entities/player/slide')),  # Player sliding animation
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),  # Player wall sliding animation
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),  # Leaf particle animation
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),  # Misc particle animation
            'gun': load_image('gun.png'),  # Gun image
            'projectile': load_image('projectile.png'),  # Projectile image
        }
        
        # Load sound effects into a dictionary
        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),  # Jump sound effect
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),  # Dash sound effect
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),  # Hit sound effect
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),  # Shoot sound effect
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),  # Ambient background sound
        }
        
        # Set volume levels for each sound effect
        self.sfx['ambience'].set_volume(0.2)  # Ambient sound volume
        self.sfx['shoot'].set_volume(0.4)  # Shooting sound volume
        self.sfx['hit'].set_volume(0.8)  # Hit sound volume
        self.sfx['dash'].set_volume(0.3)  # Dash sound volume
        self.sfx['jump'].set_volume(0.7)  # Jump sound volume
        
        self.clouds = Clouds(self.assets['clouds'], count=16)  # Create clouds effect with 16 cloud sprites
        
        self.player = Player(self, (50, 50), (8, 15))  # Create player object at position (50, 50) with size (8, 15)
        
        self.tilemap = Tilemap(self, tile_size=16)  # Create tilemap to manage level tiles with 16x16 tiles
        
        self.level = 0  # Starting level index
        self.load_level(self.level)  # Load level 0
        
        self.screenshake = 0  # Initialize screen shake effect amount
        
    def load_level(self, map_id):  # Load level data by id (map file)
        self.tilemap.load('data/maps/' + str(map_id) + '.json')  # Load the map json file
        
        self.leaf_spawners = []  # List of areas that spawn leaf particles
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):  # Extract large decor tiles matching criteria
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))  # Create rect for leaf spawn area
            
        self.enemies = []  # List of enemy objects
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):  # Extract spawner tiles for player/enemies
            if spawner['variant'] == 0:  # If variant 0, set player starting position
                self.player.pos = spawner['pos']  # Set player position
                self.player.air_time = 0  # Reset player's air time
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))  # Create enemy at spawner position
            
        self.projectiles = []  # List for projectiles in the game
        self.particles = []  # List for particle effects in the game
        self.sparks = []  # List for spark effects
        
        self.scroll = [0, 0]  # Current scrolling offset for camera
        self.dead = 0  # Player death count or flag
        self.transition = -30  # Transition timer/flag for level change
        
    def run(self):  # Main game loop to run the game
        pygame.mixer.music.load('data/music.wav')  # Load background music
        pygame.mixer.music.set_volume(0.5)  # Set music volume
        pygame.mixer.music.play(-1)  # Play music in a loop
        
        self.sfx['ambience'].play(-1)  # Play ambient sound effect in a loop
        
        while True:  # Game loop iteration
            self.display.fill((0, 0, 0, 0))  # Clear the display surface with transparent black
            self.display_2.blit(self.assets['background'], (0, 0))  # Draw the background onto display_2
            
            self.screenshake = max(0, self.screenshake - 1)  # Decrease screen shake effect over time
            
            if not len(self.enemies):  # If all enemies defeated
                self.transition += 1  # Increase transition timer
                if self.transition > 30:  # After delay
                    self.level = min(self.level + 1, len(os.listdir('data/maps')) - 1)  # Move to next level or last map
                    self.load_level(self.level)  # Load new level
            if self.transition < 0:  # If during transition start delay
                self.transition += 1  # Increment transition
            
            if self.dead:  # If player is dead
                self.dead += 1  # Increment dead timer
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)  # Start transition in after death
                if self.dead > 40:
                    self.load_level(self.level)  # Reload current level
            
            # Smoothly scroll camera to player position
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))  # Integer scroll offset for rendering
            
            # Spawn leaf particles randomly within leaf spawner rectangles
            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)  # Random position inside spawner
                    self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))
            
            self.clouds.update()  # Update cloud positions
            self.clouds.render(self.display_2, offset=render_scroll)  # Render clouds with scrolling offset
            
            self.tilemap.render(self.display, offset=render_scroll)  # Render tiles on display surface

            # Update and render enemies, remove them if killed
            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)
            
            if not self.dead:  # If player is alive
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))  # Update player movement input
                self.player.render(self.display, offset=render_scroll)  # Render player
            
            # For each projectile, update position, check collisions, and render
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]  # Move projectile horizontally
                projectile[2] += 1  # Increment projectile timer
                img = self.assets['projectile']  # Get projectile image
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))  # Render projectile
                
                if self.tilemap.solid_check(projectile[0]):  # Check if projectile hits solid tile
                    self.projectiles.remove(projectile)  # Remove projectile
                    for i in range(4):  # Create sparks on impact
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                elif projectile[2] > 360:  # Remove projectile if too old
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 50:  # Check collision with player if not dashing strongly
                    if self.player.rect().collidepoint(projectile[0]):  # If projectile hits player
                        self.projectiles.remove(projectile)  # Remove projectile
                        self.dead += 1  # Increase death counter
                        self.sfx['hit'].play()  # Play hit sound
                        self.screenshake = max(16, self.screenshake)  # Trigger screen shake effect
                        for i in range(30):  # Create sparks and particles on player hit
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                        
            # Update and render sparks; remove them if finished
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)
                    
            # Create a silhouette mask effect around the display for shading
            display_mask = pygame.mask.from_surface(self.display)
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Draw shadow offsets around edges
                self.display_2.blit(display_sillhouette, offset)
            
            # Update and render particles; leaves slightly sway side to side
            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3  # Sway leaves
                if kill:
                    self.particles.remove(particle)
            
            # Handle pygame events such as keyboard and window close
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # If window close button clicked
                    pygame.quit()  # Quit pygame
                    sys.exit()  # Exit program
                if event.type == pygame.KEYDOWN:  # Key pressed down
                    if event.key == pygame.K_LEFT:  # Left arrow key pressed
                        self.movement[0] = True  # Set left movement flag
                    if event.key == pygame.K_RIGHT:  # Right arrow key pressed
                        self.movement[1] = True  # Set right movement flag
                    if event.key == pygame.K_UP:  # Up arrow pressed
                        if self.player.jump():  # Attempt to jump
                            self.sfx['jump'].play()  # Play jump sound
                    if event.key == pygame.K_x:  # 'x' key pressed
                        self.player.dash()  # Player dash action
                if event.type == pygame.KEYUP:  # Key released
                    if event.key == pygame.K_LEFT:  # Left arrow released
                        self.movement[0] = False  # Clear left movement flag
                    if event.key == pygame.K_RIGHT:  # Right arrow released
                        self.movement[1] = False  # Clear right movement flag
                        
            if self.transition:  # If transitioning between levels
                transition_surf = pygame.Surface(self.display.get_size())  # Create a surface same size as game display
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)  # Draw circle to reveal next level
                transition_surf.set_colorkey((255, 255, 255))  # Set white as transparent color key
                self.display.blit(transition_surf, (0, 0))  # Draw transition mask on display
                
            self.display_2.blit(self.display, (0, 0))  # Blit the game display surface on top of display_2
            
            # Calculate screen shake offset randomly within shake magnitude
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            # Blit the final scaled display_2 surface to main screen with screenshake offset
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset)
            pygame.display.update()  # Update the full display Surface to the screen
            self.clock.tick(60)  # Keep the game running at 60 frames per second

Game().run()  # Create a Game instance and start running it
