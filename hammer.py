import pygame
import sys
import os
import random

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

# Asset loading
ASSETS_DIR = "assets"
wood_block_image = None
needle_image = None
hammer_image = None

def remove_background(img, threshold=200):
    """Remove white/light backgrounds from image by making them transparent"""
    # Convert to surface with alpha channel
    img = img.convert_alpha()
    
    # Create a new surface with per-pixel alpha
    new_img = pygame.Surface(img.get_size(), pygame.SRCALPHA)
    new_img.blit(img, (0, 0))
    
    # Get dimensions
    width, height = img.get_size()
    
    # Process each pixel
    for x in range(width):
        for y in range(height):
            # Get pixel color
            pixel = new_img.get_at((x, y))
            r, g, b, a = pixel.r, pixel.g, pixel.b, pixel.a
            
            # Check if pixel is light colored (white/light background)
            if r > threshold and g > threshold and b > threshold:
                # Make transparent
                new_img.set_at((x, y), (r, g, b, 0))
            # Also check for very light grays
            elif abs(r - g) < 15 and abs(g - b) < 15 and (r + g + b) / 3 > threshold:
                # Make transparent
                new_img.set_at((x, y), (r, g, b, 0))
    
    return new_img

def load_assets():
    """Load assets if they exist"""
    global wood_block_image, needle_image, hammer_image
    
    if not os.path.exists(ASSETS_DIR):
        return
    
    # Load wood block
    for ext in [".png", ".jpg", ".jpeg"]:
        path = os.path.join(ASSETS_DIR, f"wood_block{ext}")
        if os.path.exists(path):
            try:
                img = pygame.image.load(path)
                # Remove background (adjust threshold if needed)
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
                    # Remove background
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
                # Remove background
                hammer_image = remove_background(img, threshold=200)
            except Exception as e:
                print(f"Error loading hammer: {e}")
            break

# Needle class
class Needle:
    def __init__(self, x, y):
        self.start_x = x
        self.start_y = y
        self.x = x
        self.y = y
        self.depth = 0  # How far hammered in (0-100)
        self.hammered = False
        self.hammer_animation = 0
        self.is_active = False  # Only one needle is active (visible outside) at a time
        
    def hammer(self):
        """Hammer the needle down - instantly goes into the block"""
        if self.is_active:
            # Instantly hammer it in
            self.depth = 100
            self.is_active = False
            self.hammer_animation = 10
    
    def update(self):
        """Update animation"""
        if self.hammer_animation > 0:
            self.hammer_animation -= 1
        # Update position - needles start outside on the right and move left into the block
        # The needle starts at start_x (outside on right) and moves left as it's hammered
        # At depth 0: needle at start_x (outside on right)
        # At depth 100: needle head at start_x - 100 (inside block)
        if self.is_active:
            # Active needle is outside, depth = 0
            self.depth = 0
            self.x = self.start_x
        else:
            # Inactive needle is inside the block, depth = 100
            self.depth = 100
            self.x = self.start_x - 100
    
    def activate(self):
        """Activate this needle (bring it outside the block)"""
        self.is_active = True
        self.depth = 0
        self.hammered = False  # Reset hammered state for infinite game
        self.x = self.start_x
    
    def draw(self, surface):
        """Draw the needle (custom drawn) - only if active"""
        # Only draw if the needle is active (outside the block)
        if not self.is_active:
            return
        
        needle_length = 100 - self.depth
        if needle_length > 0:
            # Needle dimensions
            shaft_thickness = 6  # Thickness of the needle shaft
            head_radius = 12  # Radius of the needle head (visible part)
            
            # Draw needle shaft (the main body)
            # From left end to right end (pointing into block)
            start_x = self.x - needle_length  # Left end of needle
            end_x = self.x  # Right end (head position)
            
            # Draw shadow/outline for depth
            pygame.draw.line(surface, (80, 80, 80), 
                           (start_x, self.y + 1), 
                           (end_x, self.y + 1), shaft_thickness + 1)
            
            # Draw main needle shaft (metallic gray)
            pygame.draw.line(surface, NEEDLE_COLOR, 
                           (start_x, self.y), 
                           (end_x, self.y), shaft_thickness)
            
            # Draw highlight on needle shaft for 3D effect
            pygame.draw.line(surface, (220, 220, 220), 
                           (start_x, self.y - 1), 
                           (end_x, self.y - 1), 2)
            
            # Draw needle head (the circular part you see on the right)
            if not self.hammered:
                # Draw head shadow
                pygame.draw.circle(surface, (60, 60, 60), 
                                 (end_x + 1, self.y + 1), head_radius)
                # Draw main head
                pygame.draw.circle(surface, (160, 160, 160), 
                                 (end_x, self.y), head_radius)
                # Draw head highlight
                pygame.draw.circle(surface, (200, 200, 200), 
                                 (end_x - 3, self.y - 3), head_radius - 4)
        
        # Hammer impact effect
        if self.hammer_animation > 0:
            alpha = int(255 * (self.hammer_animation / 10))
            impact_surf = pygame.Surface((25, 25), pygame.SRCALPHA)
            pygame.draw.circle(impact_surf, (255, 200, 100, alpha), (12, 12), 12)
            surface.blit(impact_surf, (self.x - 12, self.y - 12))

# Main game
def main():
    # Load assets
    load_assets()
    
    # Block dimensions (vertical block)
    block_x = 300
    block_y = 100
    block_width = 200
    block_height = 400
    
    # Initialize three needles - only one is active at a time
    # Active needle is outside the block, others are inside
    needle_start_offset = block_width + 55  # Start position outside the block (right side)
    needles = [
        Needle(block_x + needle_start_offset, block_y + 120),
        Needle(block_x + needle_start_offset, block_y + 200),
        Needle(block_x + needle_start_offset, block_y + 280),
    ]
    
    # Activate the first needle (only one visible at a time)
    needles[0].activate()
    active_needle_index = 0
    
    # Hide default cursor and use hammer as cursor
    pygame.mouse.set_visible(False)
    
    running = True
    score = 0  # Count of needles hammered (infinite game)
    
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    # Only check the active needle
                    active_needle = needles[active_needle_index]
                    if active_needle.is_active:
                        # Check if click is near the active needle
                        needle_length = 100 - active_needle.depth
                        needle_left_end = active_needle.x - needle_length  # Left end of needle
                        # Adjusted hitbox for needles on right side
                        if (min(active_needle.x, needle_left_end) - 25 <= mouse_x <= max(active_needle.x, needle_left_end) + 25 and
                            active_needle.y - 15 <= mouse_y <= active_needle.y + 15):
                            # Hit the active needle - instantly hammer it in
                            active_needle.hammer()
                            
                            # Increment score (infinite game)
                            score += 1
                            
                            # Randomly activate one of the 3 needles (infinite game)
                            random_index = random.randint(0, len(needles) - 1)
                            active_needle_index = random_index
                            needles[active_needle_index].activate()
        
        # Update
        for needle in needles:
            needle.update()
        
        # Get mouse position for hammer cursor
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # Draw
        screen.fill(BG_COLOR)
        
        # Draw wood block
        if wood_block_image:
            # Use asset - scale maintaining aspect ratio but FORCE vertical orientation
            orig_width, orig_height = wood_block_image.get_size()
            
            # Check if image is horizontal (wider than tall)
            # If so, we want it to be vertical, so we'll rotate or swap dimensions
            if orig_width > orig_height:
                # Image is horizontal - rotate it 90 degrees to make it vertical
                rotated_img = pygame.transform.rotate(wood_block_image, 90)
                orig_width, orig_height = rotated_img.get_size()
            else:
                rotated_img = wood_block_image
            
            # Calculate scale to fit vertically (maintain aspect ratio)
            scale = min(block_width / orig_width, block_height / orig_height)
            scaled_width = int(orig_width * scale)
            scaled_height = int(orig_height * scale)
            
            # Scale the image
            scaled_block = pygame.transform.scale(rotated_img, (scaled_width, scaled_height))
            
            # Center the scaled image in the block area
            block_center_x = block_x + block_width // 2
            block_center_y = block_y + block_height // 2
            screen.blit(scaled_block, (block_center_x - scaled_width // 2, block_center_y - scaled_height // 2))
        else:
            # Draw simple wood block
            pygame.draw.rect(screen, BROWN, (block_x, block_y, block_width, block_height))
            # Wood grain (vertical lines)
            for i in range(6):
                x = block_x + 25 + i * 30
                pygame.draw.line(screen, DARK_BROWN, (x, block_y + 10), (x, block_y + block_height - 10), 2)
            # Side edges
            pygame.draw.rect(screen, LIGHT_BROWN, (block_x, block_y, 15, block_height))
            pygame.draw.rect(screen, LIGHT_BROWN, (block_x + block_width - 15, block_y, 15, block_height))
        
        # Draw needles
        for needle in needles:
            needle.draw(screen)
        
        # Draw UI
        instruction = font.render("Click on the needle to hammer it!", True, TEXT_COLOR)
        screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 30))
        
        # Show score (infinite game)
        score_text = small_font.render(f"Score: {score}", True, TEXT_COLOR)
        screen.blit(score_text, (10, 10))
        
        # Draw hammer as mouse cursor (follows mouse position) - draw last so it's on top
        if hammer_image:
            # Scale hammer to cursor size
            hammer_size = 50
            scaled_hammer = pygame.transform.scale(hammer_image, (hammer_size, hammer_size))
            # Draw hammer centered on mouse cursor
            screen.blit(scaled_hammer, (mouse_x - hammer_size // 2, mouse_y - hammer_size // 2))
        else:
            # Fallback: simple hammer shape if asset not loaded
            pygame.draw.rect(screen, HAMMER_COLOR, (mouse_x - 18, mouse_y - 30, 36, 24))
            pygame.draw.rect(screen, DARK_BROWN, (mouse_x - 4, mouse_y - 6, 8, 35))
        
        pygame.display.update()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
