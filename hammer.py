import pygame
import sys
import os
import random
import math

pygame.init()

# Screen setup
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hammer Game - Hammer the Needles!")
clock = pygame.time.Clock()

# Colors
BROWN = (101, 67, 33)
DARK_BROWN = (80, 50, 20)
LIGHT_BROWN = (139, 90, 43)
NEEDLE_COLOR = (200, 200, 200)
NEEDLE_HEAD = (180, 180, 180)
HAMMER_COLOR = (100, 100, 120)
BG_COLOR = (240, 240, 220)
TEXT_COLOR = (50, 50, 50)
PARTICLE_COLOR = (160, 110, 60)

# Hit detection settings
HIT_TOLERANCE_X = 45
HIT_TOLERANCE_Y = 45
GAME_DURATION = 30 # seconds

# Asset loading
ASSETS_DIR = "assets"
wood_block_image = None
needle_image = None
hammer_image = None

def remove_background(img, threshold=200):
    """Remove white/light backgrounds from image by making them transparent"""
    img = img.convert_alpha()
    new_img = pygame.Surface(img.get_size(), pygame.SRCALPHA)
    new_img.blit(img, (0, 0))
    width, height = img.get_size()
    for x in range(width):
        for y in range(height):
            pixel = new_img.get_at((x, y))
            r, g, b, a = pixel.r, pixel.g, pixel.b, pixel.a
            if r > threshold and g > threshold and b > threshold:
                new_img.set_at((x, y), (r, g, b, 0))
            elif abs(r - g) < 15 and abs(g - b) < 15 and (r + g + b) / 3 > threshold:
                new_img.set_at((x, y), (r, g, b, 0))
    return new_img

def load_assets():
    global wood_block_image, needle_image, hammer_image
    if not os.path.exists(ASSETS_DIR):
        return

    # Load wood block
    for ext in [".png", ".jpg", ".jpeg"]:
        path = os.path.join(ASSETS_DIR, f"wood_block{ext}")
        if os.path.exists(path):
            try:
                img = pygame.image.load(path)
                wood_block_image = remove_background(img, threshold=200)
            except Exception as e:
                print(f"Error loading wood block: {e}")
            break
    
    # Load needle
    for name in ["needle", "Needle", "NEEDLE"]:
        for ext in [".png", ".jpg", ".jpeg"]:
            path = os.path.join(ASSETS_DIR, f"{name}{ext}")
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path)
                    needle_image = remove_background(img, threshold=200)
                except Exception as e:
                    print(f"Error loading needle: {e}")
                break
        if needle_image:
            break
    
    # Load hammer
    for ext in [".png", ".jpg", ".jpeg"]:
        path = os.path.join(ASSETS_DIR, f"hammer{ext}")
        if os.path.exists(path):
            try:
                img = pygame.image.load(path)
                hammer_image = remove_background(img, threshold=200)
            except Exception as e:
                print(f"Error loading hammer: {e}")
            break

# Particle System
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-5, -1)
        self.gravity = 0.2
        self.life = 255
        self.size = random.randint(2, 5)
        self.color = (
            min(255, PARTICLE_COLOR[0] + random.randint(-20, 20)),
            min(255, PARTICLE_COLOR[1] + random.randint(-20, 20)),
            min(255, PARTICLE_COLOR[2] + random.randint(-20, 20))
        )

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= 5

    def draw(self, surface):
        if self.life > 0:
            s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            s.fill((*self.color, self.life))
            surface.blit(s, (self.x, self.y))

# Hammer Class
class Hammer:
    def __init__(self):
        self.angle = 0
        self.swinging = False
        self.swing_speed = 15
        self.return_speed = 10
        self.target_angle = -45 # Cocked back position
        self.impact_angle = 45  # Hit position
        self.state = "IDLE" # IDLE, COCKING, SWINGING, RETURNING

    def swing(self):
        if self.state == "IDLE":
            self.state = "COCKING"

    def update(self):
        if self.state == "COCKING":
            self.angle -= self.swing_speed
            if self.angle <= self.target_angle:
                self.angle = self.target_angle
                self.state = "SWINGING"
        elif self.state == "SWINGING":
            self.angle += self.swing_speed * 2
            if self.angle >= self.impact_angle:
                self.angle = self.impact_angle
                self.state = "RETURNING"
                return True # Impact happened
        elif self.state == "RETURNING":
            self.angle -= self.return_speed
            if self.angle <= 0:
                self.angle = 0
                self.state = "IDLE"
        return False

    def draw(self, surface, x, y):
        # Pivot point logic for rotation
        if hammer_image:
            hammer_size = 60
            scaled_hammer = pygame.transform.scale(hammer_image, (hammer_size, hammer_size))
            # Rotate around bottom right roughly (handle)
            rotated_hammer = pygame.transform.rotate(scaled_hammer, -self.angle)
            
            # Adjust offset to keep handle at mouse position
            # This is a bit of trial and error without exact pivot points, 
            # but generally we want the rotation center to be where the hand holds it.
            rect = rotated_hammer.get_rect(center=(x, y))
            # Shift slightly to make it look like holding handle
            rect.x += 10
            rect.y -= 10
            
            surface.blit(rotated_hammer, rect)
        else:
            # Simple rect hammer
            # Save context
            # Create a surface for rotation
            h_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.rect(h_surf, HAMMER_COLOR, (0, 0, 36, 24)) # Head
            pygame.draw.rect(h_surf, DARK_BROWN, (14, 24, 8, 26)) # Handle
            
            rotated_h = pygame.transform.rotate(h_surf, -self.angle)
            rect = rotated_h.get_rect(center=(x, y))
            surface.blit(rotated_h, rect)

# Needle class
class Needle:
    def __init__(self, x, y):
        self.start_x = x
        self.start_y = y
        self.x = x
        self.y = y
        self.target_depth = 0
        self.current_depth = 0
        self.is_active = False
        self.hammered = False
        self.wobble = 0
        
    def hammer(self):
        """Hammer the needle down"""
        if self.is_active and not self.hammered:
            self.hammered = True
            self.target_depth = 100
            return True
        return False
    
    def update(self):
        """Update animation"""
        # Smooth movement
        if self.current_depth < self.target_depth:
            self.current_depth += (self.target_depth - self.current_depth) * 0.2
            if abs(self.target_depth - self.current_depth) < 0.5:
                self.current_depth = self.target_depth
        
        # Reset if fully hammered and inactive (logic handled in main)
        
        # Calculate x based on depth
        if self.is_active:
            self.x = self.start_x - self.current_depth
        else:
            self.x = self.start_x - 100 # Hidden inside
            self.current_depth = 100
            self.target_depth = 100

    def activate(self):
        """Activate this needle"""
        self.is_active = True
        self.current_depth = 0
        self.target_depth = 0
        self.hammered = False
        self.x = self.start_x
    
    def draw(self, surface):
        """Draw the needle"""
        if not self.is_active:
            return
        
        needle_length = 100 - self.current_depth
        if needle_length > 0:
            shaft_thickness = 6
            head_radius = 12
            
            start_x = self.x - needle_length
            end_x = self.x
            
            # Shadow
            pygame.draw.line(surface, (80, 80, 80), 
                           (start_x, self.y + 1), 
                           (end_x, self.y + 1), shaft_thickness + 1)
            
            # Shaft
            pygame.draw.line(surface, NEEDLE_COLOR, 
                           (start_x, self.y), 
                           (end_x, self.y), shaft_thickness)
            
            # Highlight
            pygame.draw.line(surface, (220, 220, 220), 
                           (start_x, self.y - 1), 
                           (end_x, self.y - 1), 2)
            
            # Head
            # Only draw head if not fully submerged (or maybe always visible until gone?)
            # Let's keep it visible
            pygame.draw.circle(surface, (60, 60, 60), 
                                (end_x + 1, self.y + 1), head_radius)
            pygame.draw.circle(surface, (160, 160, 160), 
                                (end_x, self.y), head_radius)
            pygame.draw.circle(surface, (200, 200, 200), 
                                (end_x - 3, self.y - 3), head_radius - 4)

# Main game
def main():
    load_assets()
    
    block_x = 300
    block_y = 100
    block_width = 200
    block_height = 400
    
    needle_start_offset = block_width + 55
    needles = [
        Needle(block_x + needle_start_offset, block_y + 120),
        Needle(block_x + needle_start_offset, block_y + 200),
        Needle(block_x + needle_start_offset, block_y + 280),
    ]
    
    needles[0].activate()
    active_needle_index = 0
    
    hammer = Hammer()
    particles = []
    
    pygame.mouse.set_visible(False)
    
    running = True
    game_over = False
    score = 0
    start_ticks = pygame.time.get_ticks()
    
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    big_font = pygame.font.Font(None, 72)
    
    # Screenshake setup
    display_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    shake_timer = 0
    shake_offset = (0, 0)
    
    while running:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if game_over:
                        # Restart game
                        game_over = False
                        score = 0
                        particles = []
                        needles = [
                            Needle(block_x + needle_start_offset, block_y + 120),
                            Needle(block_x + needle_start_offset, block_y + 200),
                            Needle(block_x + needle_start_offset, block_y + 280),
                        ]
                        needles[0].activate()
                        active_needle_index = 0
                        start_ticks = pygame.time.get_ticks()
                    else:
                        hammer.swing()
                        # Check hit immediately for logic, but animation plays out
                        active_needle = needles[active_needle_index]
                        if active_needle.is_active and not active_needle.hammered:
                            needle_length = 100 - active_needle.current_depth
                            needle_left_end = active_needle.x - needle_length
                            
                            # Hitbox check
                            if (min(active_needle.x, needle_left_end) - HIT_TOLERANCE_X <= mouse_x <= max(active_needle.x, needle_left_end) + HIT_TOLERANCE_X and
                                active_needle.y - HIT_TOLERANCE_Y <= mouse_y <= active_needle.y + HIT_TOLERANCE_Y):
                                # Hit!
                                pass # Logic handled in hammer update sync
                            else:
                                # Missed!
                                game_over = True

        # Timer logic
        if not game_over:
            seconds_passed = (pygame.time.get_ticks() - start_ticks) / 1000
            seconds_left = GAME_DURATION - seconds_passed
            if seconds_left <= 0:
                seconds_left = 0
                game_over = True
        
        # Update
        impact = hammer.update()
        
        if impact and not game_over:
            # Hammer just hit the lowest point, check collision NOW
            active_needle = needles[active_needle_index]
            if active_needle.is_active and not active_needle.hammered:
                 # Re-check position at impact time (roughly same as click but safer)
                 # Actually, we already decided game over or not on click. 
                 # If we are here, it means we didn't miss (game_over would be true).
                 # So we just apply the hit.
                 if active_needle.hammer():
                    score += 1
                    shake_timer = 15 # Shake for 15 frames
                    # Spawn particles
                    for _ in range(15):
                        particles.append(Particle(active_needle.x, active_needle.y))
                    
                    # Schedule next needle
                    # We wait for animation to finish? No, let's just activate next one after a delay?
                    # For now, instant switch after a short delay would be better but let's stick to logic
                    # Let's wait until this one is mostly in?
                    pass

        # Check if active needle is fully hammered to switch
        if needles[active_needle_index].hammered and abs(needles[active_needle_index].current_depth - 100) < 5:
             # Switch to next
             needles[active_needle_index].is_active = False
             random_index = random.randint(0, len(needles) - 1)
             active_needle_index = random_index
             needles[active_needle_index].activate()

        for needle in needles:
            needle.update()
            
        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)
        
        if shake_timer > 0:
            shake_timer -= 1
            shake_offset = (random.randint(-5, 5), random.randint(-5, 5))
        else:
            shake_offset = (0, 0)
        
        # Draw to display_surface instead of screen
        display_surface.fill(BG_COLOR)
        
        # Draw wood block
        if wood_block_image:
            orig_width, orig_height = wood_block_image.get_size()
            if orig_width > orig_height:
                rotated_img = pygame.transform.rotate(wood_block_image, 90)
                orig_width, orig_height = rotated_img.get_size()
            else:
                rotated_img = wood_block_image
            scale = min(block_width / orig_width, block_height / orig_height)
            scaled_width = int(orig_width * scale)
            scaled_height = int(orig_height * scale)
            scaled_block = pygame.transform.scale(rotated_img, (scaled_width, scaled_height))
            block_center_x = block_x + block_width // 2
            block_center_y = block_y + block_height // 2
            display_surface.blit(scaled_block, (block_center_x - scaled_width // 2, block_center_y - scaled_height // 2))
        else:
            pygame.draw.rect(display_surface, BROWN, (block_x, block_y, block_width, block_height))
            for i in range(6):
                x = block_x + 25 + i * 30
                pygame.draw.line(display_surface, DARK_BROWN, (x, block_y + 10), (x, block_y + block_height - 10), 2)
            pygame.draw.rect(display_surface, LIGHT_BROWN, (block_x, block_y, 15, block_height))
            pygame.draw.rect(display_surface, LIGHT_BROWN, (block_x + block_width - 15, block_y, 15, block_height))
        
        # Draw needles
        for needle in needles:
            needle.draw(display_surface)
            
        # Draw particles
        for p in particles:
            p.draw(display_surface)
        
        # UI
        if not game_over:
            instruction = font.render("Click on the needle!", True, TEXT_COLOR)
            display_surface.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 30))
            score_text = small_font.render(f"Score: {score}", True, TEXT_COLOR)
            display_surface.blit(score_text, (10, 10))
            
            # Draw Timer
            timer_color = TEXT_COLOR
            if seconds_left <= 5:
                timer_color = (200, 50, 50) # Red warning
            timer_text = font.render(f"Time: {int(seconds_left)}", True, timer_color)
            display_surface.blit(timer_text, (SCREEN_WIDTH - 120, 10))
        else:
            # Game Over Screen
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            display_surface.blit(overlay, (0, 0))
            
            go_text = big_font.render("GAME OVER", True, (255, 100, 100))
            display_surface.blit(go_text, (SCREEN_WIDTH // 2 - go_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            
            final_score = font.render(f"Final Score: {score}", True, (255, 255, 255))
            display_surface.blit(final_score, (SCREEN_WIDTH // 2 - final_score.get_width() // 2, SCREEN_HEIGHT // 2 + 20))
            
            retry_text = font.render("Click to Try Again", True, (200, 200, 200))
            display_surface.blit(retry_text, (SCREEN_WIDTH // 2 - retry_text.get_width() // 2, SCREEN_HEIGHT // 2 + 70))

        # Draw hammer
        hammer.draw(display_surface, mouse_x, mouse_y)
        
        # Final blit to screen with shake
        screen.fill(BG_COLOR) # Clear screen (or fill with black/bg)
        screen.blit(display_surface, shake_offset)
        
        pygame.display.update()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
