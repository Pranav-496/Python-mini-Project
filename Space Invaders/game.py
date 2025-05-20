# Importing required libraries
import math      # For calculating distance between bullet and enemy
import random    # For generating random positions for enemies
import pygame    # Main library for game development
from pygame import mixer  # For playing sound/music

# Initialize all pygame modules
pygame.init()

# Create the game screen with width = 800 and height = 600
screen = pygame.display.set_mode((800, 600))

# Load background image
background = pygame.image.load('background.png')

# Load and play background music on loop (-1 means infinite loop)
mixer.music.load("background.wav")
mixer.music.play(-1)

# Set window title and icon
pygame.display.set_caption("Space Invaders")
icon = pygame.image.load('ufo.png')
pygame.display.set_icon(icon)

# Load player spaceship image and set initial position
playerImg = pygame.image.load('player.png')
playerX = 370  # Horizontal position
playerY = 480  # Vertical position (fixed)
playerX_change = 0  # Change in X (used for movement)

# Load enemy spaceship images and set their initial positions and speed
enemyImg = []         # List to hold enemy images
enemyX = []           # List to hold X positions of enemies
enemyY = []           # List to hold Y positions of enemies
enemyX_change = []    # List to hold X-axis movement speed
enemyY_change = []    # List to hold Y-axis drop after hitting screen edge
num_of_enemies = 6    # Number of enemies on screen

# Generate multiple enemies
for i in range(num_of_enemies):
    enemyImg.append(pygame.image.load('enemy.png'))
    enemyX.append(random.randint(0, 736))   # Random X position
    enemyY.append(random.randint(50, 150))  # Random Y position
    enemyX_change.append(4)                # Horizontal speed
    enemyY_change.append(40)               # Drop down when edge is hit

# Bullet setup
bulletImg = pygame.image.load('bullet.png')
bulletX = 0
bulletY = 480  # Initial Y position of bullet
bulletX_change = 0
bulletY_change = 10  # Speed of bullet going upward
bullet_state = "ready"  # "ready" = can fire, "fire" = bullet is on screen

# Score setup
score_value = 0
font = pygame.font.Font('freesansbold.ttf', 32)
textX = 10  # X position of score display
testY = 10  # Y position of score display

# Game Over font
over_font = pygame.font.Font('freesansbold.ttf', 64)

# Function to show score on screen
def show_score(x, y):
    score = font.render("Score : " + str(score_value), True, (255, 255, 255))
    screen.blit(score, (x, y))

# Function to display "GAME OVER" text
def game_over_text():
    over_text = over_font.render("GAME OVER", True, (255, 255, 255))
    screen.blit(over_text, (200, 250))

# Function to draw player spaceship on screen
def player(x, y):
    screen.blit(playerImg, (x, y))

# Function to draw enemy spaceship on screen
def enemy(x, y, i):
    screen.blit(enemyImg[i], (x, y))

# Function to fire the bullet
def fire_bullet(x, y):
    global bullet_state
    bullet_state = "fire"  # Bullet is now moving
    screen.blit(bulletImg, (x + 16, y + 10))  # Adjust bullet position for center

# Function to detect collision between bullet and enemy
def isCollision(enemyX, enemyY, bulletX, bulletY):
    distance = math.sqrt(math.pow(enemyX - bulletX, 2) + (math.pow(enemyY - bulletY, 2)))
    if distance < 27:  # If they are close enough, it’s a hit
        return True
    else:
        return False

# Main Game Loop
running = True
while running:
    # Fill the screen with black color before drawing everything
    screen.fill((0, 0, 0))
    
    # Draw background image
    screen.blit(background, (0, 0))

    # Loop through events (keyboard, mouse, etc.)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # Quit the game
            running = False

        # If a key is pressed down
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:  # Move left
                playerX_change = -5
            if event.key == pygame.K_RIGHT:  # Move right
                playerX_change = 5
            if event.key == pygame.K_SPACE:  # Fire bullet
                if bullet_state == "ready":  # Only fire if bullet is not already moving
                    bulletSound = mixer.Sound("laser.wav")
                    bulletSound.play()
                    bulletX = playerX  # Set bullet to current player position
                    fire_bullet(bulletX, bulletY)

        # If key is released, stop movement
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                playerX_change = 0

    # Update player position
    playerX += playerX_change

    # Keep player within screen boundaries
    if playerX <= 0:
        playerX = 0
    elif playerX >= 736:  # 800 - player image width (64)
        playerX = 736

    # Enemy Movement and Collision Detection
    for i in range(num_of_enemies):

        # Check if any enemy has reached close to the player (game over)
        if enemyY[i] > 440:
            for j in range(num_of_enemies):
                enemyY[j] = 2000  # Move all enemies off-screen
            game_over_text()
            break

        # Move enemy left/right
        enemyX[i] += enemyX_change[i]

        # Reverse direction and move down when hitting the edge
        if enemyX[i] <= 0:
            enemyX_change[i] = 4
            enemyY[i] += enemyY_change[i]
        elif enemyX[i] >= 736:
            enemyX_change[i] = -4
            enemyY[i] += enemyY_change[i]

        # Check for collision between this enemy and bullet
        collision = isCollision(enemyX[i], enemyY[i], bulletX, bulletY)
        if collision:
            explosionSound = mixer.Sound("explosion.wav")
            explosionSound.play()
            bulletY = 480  # Reset bullet position
            bullet_state = "ready"  # Bullet can be fired again
            score_value += 1  # Increase score
            # Respawn enemy at random position
            enemyX[i] = random.randint(0, 736)
            enemyY[i] = random.randint(50, 150)

        # Draw enemy
        enemy(enemyX[i], enemyY[i], i)

    # Bullet Movement
    if bulletY <= 0:
        bulletY = 480  # Reset bullet Y position
        bullet_state = "ready"  # Ready to fire again

    if bullet_state == "fire":
        fire_bullet(bulletX, bulletY)  # Draw the bullet
        bulletY -= bulletY_change      # Move bullet upward

    # Draw player and score
    player(playerX, playerY)
    show_score(textX, testY)

    # Update the screen with all drawings
    pygame.display.update()
