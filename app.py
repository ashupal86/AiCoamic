from flask import Flask, render_template, request, jsonify, redirect, url_for
from markupsafe import Markup
import os
import json
import markdown
import re
import datetime
import requests
import uuid
import time
from dotenv import load_dotenv
import google.generativeai as genai
import traceback
import base64
from PIL import Image, ImageDraw
from io import BytesIO
import math
import random

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Get API keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)  # Configure the genai library with API key

# Directory for storing images
IMAGES_DIR = "static/images"
os.makedirs(IMAGES_DIR, exist_ok=True)

# Global variables
STORIES_DIR = "stories"
STATIC_IMG_DIR = "static/img/stories"

# Create directories if they don't exist
os.makedirs(STORIES_DIR, exist_ok=True)
os.makedirs(STATIC_IMG_DIR, exist_ok=True)

# Helper functions
def get_timestamp():
    """Generate a timestamp for unique file naming"""
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def save_story(prompt, markdown_story, image_paths=None, image_prompts=None):
    """Save a story to a JSON file with a unique ID."""
    if image_paths is None:
        image_paths = []
    
    if image_prompts is None:
        image_prompts = []
        
    # Generate a unique ID and timestamp
    story_id = str(uuid.uuid4())
    created_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Extract title from the markdown (first heading)
    title = extract_title_from_markdown(markdown_story)
    
    # Create the story data structure
    story_data = {
        "id": story_id,
        "prompt": prompt,
        "markdown_story": markdown_story,
        "image_paths": image_paths,
        "image_prompts": image_prompts,  # Store the image prompts
        "created_date": created_date,
        "title": title
    }
    
    # Save to a JSON file
    story_path = os.path.join(STORIES_DIR, f"{story_id}.json")
    with open(story_path, "w") as f:
        json.dump(story_data, f, indent=2)
    
    return story_data

def extract_title_from_markdown(markdown_text):
    """Extract the title from markdown text (first heading)"""
    lines = markdown_text.split('\n')
    for line in lines:
        if line.startswith('# '):
            return line.replace('# ', '')
    return None

def generate_image_prompt(chapter_title, story_context, style="comic book"):
    """Generate a prompt for image generation based on chapter title and story context."""
    image_prompt = f"Create a detailed {style} style illustration for a comic panel depicting: {chapter_title}. {story_context}. Make it in a professional comic book style with vibrant colors, clear action, and engaging composition."
    return image_prompt

def extract_chapter_titles_and_content(markdown_story):
    """Extract chapter titles (h2 headings) and their content from markdown story."""
    chapter_info = []
    lines = markdown_story.split('\n')
    current_title = None
    current_content = []
    
    for line in lines:
        if line.startswith('## '):
            # If we were collecting content for a previous chapter, save it
            if current_title:
                chapter_info.append({
                    "title": current_title,
                    "content": ' '.join(current_content)
                })
                current_content = []
            current_title = line.replace('## ', '')
        elif current_title and line.strip():
            current_content.append(line)
    
    # Don't forget to add the last chapter
    if current_title and current_content:
        chapter_info.append({
            "title": current_title,
            "content": ' '.join(current_content)
        })
    
    return chapter_info

def split_story_by_panels(markdown_story):
    """Split a markdown story into panels based on h2 headings."""
    panels = []
    
    # First, get the story title and intro
    lines = markdown_story.split('\n')
    intro = []
    in_intro = True
    
    for line in lines:
        if line.startswith('## '):
            in_intro = False
            current_panel = [line]
            panels.append(current_panel)
        elif line.startswith('# '):
            intro.append(line)
        elif in_intro:
            intro.append(line)
        elif not in_intro and panels:
            panels[-1].append(line)
    
    return intro, panels

def load_stories():
    """Load all stories from the stories directory."""
    stories = []
    if os.path.exists(STORIES_DIR):
        for filename in os.listdir(STORIES_DIR):
            if filename.endswith(".json"):
                with open(os.path.join(STORIES_DIR, filename), "r") as f:
                    story_data = json.load(f)
                    stories.append(story_data)
    
    # Sort stories by creation date (newest first)
    stories.sort(key=lambda x: x.get("created_date", ""), reverse=True)
    return stories

def generate_story(prompt, num_panels=4, style="comic book"):
    """Generate a story using the Gemini API."""
    try:
        if not GEMINI_API_KEY:
            return fallback_story_generation(prompt, num_panels)
            
        # Configure the model
        generation_config = {
            "temperature": 0.9,
            "top_p": 1,
            "top_k": 32,
            "max_output_tokens": 2048,
        }
        
        # Create model instance
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config
        )
        
        # Create the prompt for story generation
        story_prompt = f"""
        You are a creative comic book writer and artist. Create an engaging comic-style story with exactly {num_panels} distinct panels that will be illustrated as a comic book or manga.
        
        The story should be based on this prompt: "{prompt}"
        
        Format your response in markdown with:
        1. A creative title (# Title) - make it catchy and comic-like
        2. An introduction paragraph that sets the scene
        3. Exactly {num_panels} sections (## Panel 1, ## Panel 2, etc.) - one for each comic panel
        4. Each panel description should:
           - Include vivid visual descriptions for the illustrator
           - Include dialogue in quotation marks ("Like this!")
           - Describe the scene, characters, actions, and emotions clearly
           - Focus on a single moment or action that would make a good comic panel
        5. End with a conclusion paragraph that wraps up the story
        6. After the conclusion, include a section called "## Image Prompts" that contains {num_panels + 1} distinct prompts for image generation:
           - First prompt should be for the cover image
           - Remaining prompts should be for each panel
           - Format as "Cover: [detailed prompt for cover image]" and "Panel 1: [detailed prompt for panel 1]", etc.
           - Each image prompt should be descriptive, detailed and optimized for AI image generation
        
        Comic-specific guidelines:
        - Create visually interesting scenes that would work well as comic book panels
        - Include dynamic camera angles (close-ups, wide shots, etc.) in your descriptions
        - Use dialogue that fits in speech bubbles - keep it concise and impactful
        - Use comic book conventions like onomatopoeia (BOOM!, CRASH!) where appropriate
        - Include character emotions and expressions clearly
        - Describe the art style as {style}
        - Keep panels roughly the same length, but vary them for dramatic effect
        
        The output will be turned into a {style} comic with {num_panels} illustrated panels, so make sure each section describes a clear, distinct visual scene.
        """
        
        # Generate the story
        response = model.generate_content(story_prompt)
        markdown_story = response.text
        
        # Clean up the markdown
        markdown_story = markdown_story.strip()
        
        # Extract image prompts (if present)
        image_prompts = extract_image_prompts(markdown_story)
        
        # Remove image prompts section from the story
        if "## Image Prompts" in markdown_story:
            markdown_story = markdown_story.split("## Image Prompts")[0].strip()
        
        # Ensure we have exactly the right number of section headings
        section_headings = re.findall(r'## .*', markdown_story)
        if len(section_headings) != num_panels:
            # If we don't have the right number of headings, use the fallback
            return fallback_story_generation(prompt, num_panels), []
        
        return markdown_story, image_prompts
    except Exception as e:
        print(f"Error generating story: {e}")
        traceback.print_exc()
        return fallback_story_generation(prompt, num_panels), []

def extract_image_prompts(markdown_story):
    """Extract image prompts from the markdown story."""
    image_prompts = []
    
    # Check if the image prompts section exists
    if "## Image Prompts" in markdown_story:
        # Extract the image prompts section
        prompts_section = markdown_story.split("## Image Prompts")[1].strip()
        
        # Extract individual prompts
        lines = prompts_section.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("Cover:"):
                image_prompts.append({"type": "cover", "prompt": line[6:].strip()})
            elif line.startswith("Panel"):
                # Extract panel number
                panel_match = re.match(r"Panel (\d+):", line)
                if panel_match:
                    panel_num = int(panel_match.group(1))
                    prompt_text = line[line.index(":")+1:].strip()
                    image_prompts.append({"type": "panel", "number": panel_num, "prompt": prompt_text})
    
    return image_prompts

def fallback_story_generation(prompt, num_panels=4):
    """Generate a fallback story when the API call fails."""
    title = f"The Amazing Adventure of {prompt[:20]}..."
    
    # Create a basic story structure with more comic-friendly content
    story_parts = [
        f"# {title}",
        f"\nIn a world where anything can happen, our story about {prompt} begins to unfold. "
        f"The adventure that awaits is unlike anything seen before, filled with excitement and wonder.",
        
        f"\n## Panel 1: The Beginning",
        f"\nA bright scene introduces our hero in the world of {prompt}. "
        f"The background shows a vibrant landscape with rich details. "
        f'"This is where my journey begins!" exclaims the protagonist, eyes wide with determination. '
        f"Their expression shows a mix of excitement and nervousness as they take their first step forward.",
        
        f"\n## Panel 2: The Challenge",
        f"\nThe scene darkens slightly as our hero encounters their first obstacle. "
        f"The composition shows them facing a looming challenge, with dramatic lighting highlighting their determined expression. "
        f'"I won\'t back down now," they mutter, clenching their fists. '
        f"The tension is palpable as sweat beads on their forehead. WHOOSH! The sound effect emphasizes the moment.",
    ]
    
    # Add additional panels based on requested number with comic-specific elements
    if num_panels >= 3:
        story_parts.extend([
            f"\n## Panel 3: The Unexpected Turn",
            f"\nA dramatic wide shot reveals a surprising development in the {prompt} storyline. "
            f"The color palette shifts dramatically to emphasize the surprise. "
            f'"I can\'t believe what I\'m seeing!" gasps the hero, taking a step back. '
            f"Their face shows complete shock as the world around them transforms. CRACK! The sound splits the panel as reality shifts.",
        ])
    
    if num_panels >= 4:
        story_parts.extend([
            f"\n## Panel 4: The Confrontation",
            f"\nA close-up shot focuses on the intense standoff between our hero and the challenge. "
            f"Dramatic shadows cast across their face show determination mixed with fear. "
            f'"This ends now!" they declare boldly, striking a powerful stance. '
            f"The background shows motion lines emphasizing the intensity of the moment. BOOM! The sound effect punctuates their declaration.",
        ])
    
    if num_panels >= 5:
        story_parts.extend([
            f"\n## Panel 5: The Revelation",
            f"\nThe panel reveals a crucial discovery that changes everything about {prompt}. "
            f"A glowing light illuminates our hero's face from below, casting ethereal shadows. "
            f'"So that\'s what this has all been about..." they whisper, eyes widening with understanding. '
            f"The composition zooms out to show the magnitude of this revelation, with small details becoming clear.",
        ])
    
    if num_panels >= 6:
        story_parts.extend([
            f"\n## Panel 6: The Resolution",
            f"\nA triumphant scene shows our hero standing victorious among the elements of {prompt}. "
            f"The color palette is bright and uplifting, with a sunrise composition symbolizing new beginnings. "
            f'"We did it! Against all odds, we actually did it!" they cheer, striking a victorious pose. '
            f"Supporting characters gather around, their faces showing relief and joy. Colorful celebratory effects fill the background.",
        ])
    
    # Add conclusion
    story_parts.append(
        f"\nAnd so, the tale of {prompt} concludes, but like all great comic stories, the adventure never truly ends. "
        f"Our hero's journey through challenges and triumphs reminds us that even in the most extraordinary circumstances, "
        f"courage and determination can lead to unexpected wonders. Until the next issue!"
    )
    
    return "".join(story_parts), []

def generate_image(prompt, image_path, style="comic book"):
    """Generate an image using Gemini's model for image generation"""
    try:
        if not GEMINI_API_KEY:
            print("No API key available for image generation")
            return create_minimal_image(image_path, prompt, style)
        
        # Enhanced prompt for text-based image generation
        enhanced_prompt = f"""
        Generate a detailed description of a professional-quality {style} illustration for this scene:
        
        {prompt}
        
        Focus on these elements in your description:
        - Character appearance details (clothing, expressions, poses)
        - Scene composition and environment details
        - Lighting and atmosphere
        - Color palette
        - Any text elements like speech bubbles or sound effects
        
        Make the description highly specific and detailed enough to create a clear mental image.
        """
        
        try:
            # Use Gemini 1.5 Pro for the detailed description
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Configure generation parameters
            generation_config = {
                "temperature": 1.0,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 4096,
            }
            
            # Generate a detailed text description
            response = model.generate_content(
                enhanced_prompt,
                generation_config=generation_config,
                stream=False
            )
            
            # Get the text description
            image_description = response.text.strip()
            
            # Now use this detailed description to create an image - this is where you would
            # connect to Imagen or another image generation API. Currently, we'll use our
            # improved placeholder system with the detailed text
            
            print(f"✓ Generated detailed image description: {image_description[:100]}...")
            return create_art_based_image(image_path, image_description, style)
            
        except Exception as img_gen_error:
            print(f"Error generating image description: {img_gen_error}")
            traceback.print_exc()
            return create_minimal_image(image_path, prompt, style)
            
    except Exception as e:
        print(f"Error in image generation process: {e}")
        traceback.print_exc()
        return create_minimal_image(image_path, prompt, style)

def create_art_based_image(image_path, description, style="comic book"):
    """Create an artistic image based on the description"""
    try:
        # In a real implementation, this would call an image generation API like Stable Diffusion
        # or Midjourney using the description. For now, we'll create a more sophisticated placeholder.
        
        # Create a colored background image
        width, height = 800, 600
        
        # Color scheme based on style and description mood
        bg_colors = {
            "comic book": (20, 20, 30),  # Dark blue-black for comic
            "manga": (10, 10, 15),       # Even darker for manga
            "pixel art": (25, 35, 40),   # Bluish dark for pixel art
            "watercolor": (35, 25, 30),  # Reddish dark for watercolor
            "3D rendered": (25, 15, 35)  # Purplish dark for 3D
        }
        
        # Determine mood from description
        mood = "standard"
        if any(word in description.lower() for word in ["dark", "night", "shadow", "gloomy", "mysterious"]):
            mood = "dark"
        elif any(word in description.lower() for word in ["bright", "sunny", "vibrant", "colorful", "happy"]):
            mood = "bright"
        
        # Adjust base color based on mood
        base_color = bg_colors.get(style, (20, 20, 30))
        if mood == "dark":
            base_color = (max(base_color[0]-10, 5), max(base_color[1]-10, 5), max(base_color[2]-10, 5))
        elif mood == "bright":
            base_color = (min(base_color[0]+10, 40), min(base_color[1]+10, 40), min(base_color[2]+10, 40))
            
        # Create the base image
        image = Image.new('RGB', (width, height), base_color)
        draw = ImageDraw.Draw(image)
        
        # Add a stylish border
        border_width = 12
        draw.rectangle(
            [(border_width, border_width), (width-border_width, height-border_width)],
            outline=(200, 200, 200),
            width=border_width//2
        )
        
        # Draw artistic panel dividers based on style
        if style == "comic book":
            # Create a dynamic panel layout
            panel_division = random.choice(["diagonal", "horizontal", "vertical", "cross"])
            
            if panel_division == "diagonal":
                draw.line([(border_width*2, border_width*2), (width-border_width*2, height-border_width*2)], 
                          fill=(150, 150, 150), width=3)
            elif panel_division == "horizontal":
                draw.line([(border_width*2, height//2), (width-border_width*2, height//2)], 
                          fill=(150, 150, 150), width=3)
            elif panel_division == "vertical":
                draw.line([(width//2, border_width*2), (width//2, height-border_width*2)], 
                          fill=(150, 150, 150), width=3)
            elif panel_division == "cross":
                draw.line([(width//2, border_width*2), (width//2, height-border_width*2)], 
                          fill=(150, 150, 150), width=3)
                draw.line([(border_width*2, height//2), (width-border_width*2, height//2)], 
                          fill=(150, 150, 150), width=3)
        
        # Extract key phrases from the description for visualization
        key_phrases = extract_key_phrases_from_description(description)
        
        # Visualize characters if mentioned
        character_keywords = extract_character_keywords(description)
        if character_keywords:
            draw_character_silhouettes(draw, character_keywords, width, height)
        
        # Always add a speech bubble with a key phrase
        add_artistic_speech_bubble(draw, key_phrases[0] if key_phrases else "...", width, height, style)
        
        # Add style-specific visual elements
        if style == "manga":
            add_manga_style_elements(draw, width, height, mood)
        elif style == "comic book":
            add_comic_style_elements(draw, width, height, mood)
        elif style == "pixel art":
            add_pixelated_elements(draw, width, height)
        
        # Add scene description at the bottom for context
        shortened_desc = shorten_description(description, 120)
        draw_caption_area(draw, shortened_desc, width, height)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image.save(image_path)
        
        return image_path
    except Exception as e:
        print(f"Error creating art based image: {e}")
        traceback.print_exc()
        
        # Fallback to minimal image
        return create_minimal_image(image_path, description, style)

def extract_character_keywords(description):
    """Extract character-related words from description"""
    character_indicators = [
        "man", "woman", "boy", "girl", "person", "figure", "hero", "villain", 
        "protagonist", "character", "warrior", "wizard", "alien", "robot",
        "teacher", "student", "child", "adult", "teenager"
    ]
    
    words = description.lower().split()
    character_words = []
    
    for i, word in enumerate(words):
        if word in character_indicators and i > 0:
            # Get descriptive words before character indicators
            if i > 1 and words[i-2] not in character_indicators:
                character_words.append(words[i-2])
            if words[i-1] not in character_indicators:
                character_words.append(words[i-1])
            character_words.append(word)
    
    return character_words[:3]  # Limit to top 3

def draw_character_silhouettes(draw, character_keywords, width, height):
    """Draw abstract character silhouettes based on keywords"""
    num_characters = min(len(character_keywords), 3)
    character_spacing = width // (num_characters + 1)
    
    for i in range(num_characters):
        x_pos = character_spacing * (i + 1)
        # Vary height based on character type
        if "child" in character_keywords or "boy" in character_keywords or "girl" in character_keywords:
            char_height = height // 3
        else:
            char_height = height // 2.2
        
        # Character base position
        base_y = height // 1.5
        
        # Draw character silhouette - simple abstract shape
        if "woman" in character_keywords or "girl" in character_keywords:
            # Female silhouette
            draw.ellipse([(x_pos-30, base_y-char_height), (x_pos+30, base_y-char_height+60)], 
                        fill=(120, 120, 140), outline=(160, 160, 180))
            # Body
            draw.polygon([(x_pos-25, base_y-char_height+50), (x_pos+25, base_y-char_height+50),
                         (x_pos+40, base_y), (x_pos-40, base_y)], 
                         fill=(120, 120, 140), outline=(160, 160, 180))
        else:
            # Male/generic silhouette
            draw.ellipse([(x_pos-25, base_y-char_height), (x_pos+25, base_y-char_height+50)], 
                        fill=(120, 120, 140), outline=(160, 160, 180))
            # Body
            draw.polygon([(x_pos-30, base_y-char_height+40), (x_pos+30, base_y-char_height+40),
                         (x_pos+45, base_y), (x_pos-45, base_y)], 
                         fill=(120, 120, 140), outline=(160, 160, 180))

def add_artistic_speech_bubble(draw, text, width, height, style):
    """Add an artistic speech bubble with stylized text"""
    # Prepare text
    if len(text) > 80:
        text = text[:77] + "..."
    
    # Different bubble styles based on comic style
    if style == "manga":
        # Angular manga-style bubble
        bubble_x = width // 3
        bubble_y = height // 3
        bubble_width = width // 2
        bubble_height = 80
        
        # Angular points for manga style
        points = [
            (bubble_x, bubble_y),
            (bubble_x + bubble_width, bubble_y),
            (bubble_x + bubble_width, bubble_y + bubble_height),
            (bubble_x + bubble_width//2 + 20, bubble_y + bubble_height),
            (bubble_x + bubble_width//2, bubble_y + bubble_height + 30),
            (bubble_x + bubble_width//2 - 20, bubble_y + bubble_height),
            (bubble_x, bubble_y + bubble_height),
        ]
        
        draw.polygon(points, fill=(240, 240, 240), outline=(30, 30, 30), width=2)
    else:
        # Rounded comic-style bubble
        bubble_x = width // 3
        bubble_y = height // 3
        bubble_width = width // 2
        bubble_height = 80
        
        # Draw rounded rectangle
        draw.rounded_rectangle(
            [(bubble_x, bubble_y), (bubble_x + bubble_width, bubble_y + bubble_height)],
            radius=15, fill=(240, 240, 240), outline=(30, 30, 30), width=2
        )
        
        # Add a pointer
        draw.polygon(
            [(bubble_x + bubble_width//2 - 10, bubble_y + bubble_height),
             (bubble_x + bubble_width//2, bubble_y + bubble_height + 25),
             (bubble_x + bubble_width//2 + 15, bubble_y + bubble_height)],
            fill=(240, 240, 240), outline=(30, 30, 30), width=2
        )
    
    # Draw text centered in bubble
    text_width = len(text) * 6  # Rough estimate
    text_x = bubble_x + bubble_width//2 - text_width//2
    text_y = bubble_y + bubble_height//2 - 10
    
    # Draw with shadow for better visibility
    draw.text((text_x+1, text_y+1), text, fill=(50, 50, 50))
    draw.text((text_x, text_y), text, fill=(0, 0, 0))

def add_manga_style_elements(draw, width, height, mood):
    """Add manga-specific visual elements"""
    # Add speed/emotion lines based on mood
    if mood == "dark":
        # Dark mood - fewer, more angular lines
        for i in range(15):
            start_x = random.randint(width//4, width*3//4)
            start_y = random.randint(height//4, height*3//4)
            length = random.randint(30, 100)
            angle = random.uniform(0, 2 * 3.14159)
            end_x = start_x + int(length * math.cos(angle))
            end_y = start_y + int(length * math.sin(angle))
            draw.line([(start_x, start_y), (end_x, end_y)], fill=(180, 180, 180), width=1)
    else:
        # Action/bright mood - more dynamic radial lines
        center_x = width // 2
        center_y = height // 2
        for i in range(24):
            angle = (i / 24) * 2 * 3.14159
            length = random.randint(50, 150)
            end_x = center_x + int(length * math.cos(angle))
            end_y = center_y + int(length * math.sin(angle))
            draw.line([(center_x, center_y), (end_x, end_y)], fill=(200, 200, 200), width=1)

def add_comic_style_elements(draw, width, height, mood):
    """Add comic book-specific visual elements"""
    # Add sound effect burst
    if random.random() > 0.5:
        sound_effects = ["POW!", "BAM!", "ZOOM!", "WHAM!", "CRASH!", "BANG!"]
        effect = random.choice(sound_effects)
        
        # Position in upper corner
        effect_x = width * 0.75
        effect_y = height * 0.25
        
        # Create starburst shape
        points = []
        num_points = 12
        inner_radius = 50
        outer_radius = 80
        
        for i in range(num_points * 2):
            angle = (i * 3.14159) / num_points
            radius = outer_radius if i % 2 == 0 else inner_radius
            x = effect_x + radius * math.cos(angle)
            y = effect_y + radius * math.sin(angle)
            points.append((x, y))
        
        # Color varies by mood
        if mood == "dark":
            fill_color = (80, 20, 20)  # Dark red for dark mood
            text_color = (220, 220, 220)
        elif mood == "bright":
            fill_color = (255, 220, 0)  # Bright yellow for bright mood
            text_color = (255, 0, 0)
        else:
            fill_color = (255, 150, 0)  # Orange for standard
            text_color = (0, 0, 0)
            
        draw.polygon(points, fill=fill_color, outline=(0, 0, 0), width=2)
        
        # Draw effect text
        text_width = len(effect) * 10
        draw.text((effect_x - text_width//2, effect_y - 15), effect, fill=text_color)

def add_pixelated_elements(draw, width, height):
    """Add pixel art style elements"""
    pixel_size = 15
    # Create a pixelated grid in the background
    for x in range(0, width, pixel_size):
        for y in range(0, height, pixel_size):
            if random.random() > 0.85:  # Only color some pixels
                color = (
                    random.randint(30, 80),
                    random.randint(30, 80),
                    random.randint(40, 100)
                )
                draw.rectangle([(x, y), (x+pixel_size-1, y+pixel_size-1)], fill=color)

def extract_key_phrases_from_description(description, max_phrases=3):
    """Extract key descriptive phrases from the image description"""
    # Split into sentences
    sentences = re.split(r'[.!?]', description)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    # Find sentences with vivid descriptive language
    scored_sentences = []
    descriptive_words = ["vivid", "bright", "colorful", "detailed", "dramatic", "striking", 
                         "intense", "powerful", "dynamic", "expressive", "emotional"]
                         
    for sentence in sentences:
        score = 0
        for word in descriptive_words:
            if word in sentence.lower():
                score += 1
                
        # Longer sentences likely have more description but not too long
        length_score = min(len(sentence) / 30, 3)
        score += length_score
        
        scored_sentences.append((sentence, score))
    
    # Sort by score, highest first
    scored_sentences.sort(key=lambda x: x[1], reverse=True)
    
    # Take top phrases, truncate if needed
    selected_phrases = []
    for sentence, _ in scored_sentences[:max_phrases]:
        if len(sentence) > 100:
            sentence = sentence[:97] + "..."
        selected_phrases.append(sentence)
        
    return selected_phrases

def shorten_description(description, max_length=120):
    """Shorten a long description to a reasonable length while preserving meaning"""
    if len(description) <= max_length:
        return description
        
    # Try to find a good breaking point
    sentences = re.split(r'[.!?]', description)
    
    result = ""
    for sentence in sentences:
        if len(result) + len(sentence) <= max_length:
            result += sentence + "."
        else:
            break
            
    # If we couldn't even fit one sentence, just truncate
    if not result:
        result = description[:max_length-3] + "..."
        
    return result.strip()

def draw_caption_area(draw, text, width, height):
    """Draw a caption area at the bottom with the description"""
    # Create semi-transparent overlay at the bottom
    caption_height = 60
    caption_y = height - caption_height - 10
    
    # Draw caption background
    draw.rectangle(
        [(20, caption_y), (width-20, caption_y + caption_height)],
        fill=(30, 30, 40, 180),
        outline=(200, 200, 200),
        width=1
    )
    
    # Wrap text to fit the caption area
    wrapped_text = []
    words = text.split()
    line = ""
    for word in words:
        test_line = line + word + " "
        if len(test_line) * 6 < width - 60:  # Rough estimate
            line = test_line
        else:
            wrapped_text.append(line)
            line = word + " "
    if line:
        wrapped_text.append(line)
        
    # Limit to 2 lines maximum
    wrapped_text = wrapped_text[:2]
    
    # Draw text
    text_y = caption_y + 10
    for line in wrapped_text:
        draw.text((30, text_y), line, fill=(220, 220, 220))
        text_y += 25

def generate_comic_images(story_id, image_prompts, style="comic book"):
    """Generate all images for a comic story based on provided prompts"""
    image_paths = []
    timestamp = get_timestamp()
    
    try:
        # Check if we have image prompts
        if not image_prompts:
            # Fallback to generated placeholder images based on titles
            return generate_basic_placeholder_images(story_id, style)
        
        # First, find the cover prompt
        cover_prompt = next((p["prompt"] for p in image_prompts if p["type"] == "cover"), None)
        
        # If no cover prompt found, create a basic one
        if not cover_prompt:
            cover_prompt = f"Create a captivating comic book cover illustration in {style} style."
        
        # Generate cover image
        cover_path = f"{STATIC_IMG_DIR}/{story_id}_{timestamp}_cover.jpg"
        cover_result = generate_image(cover_prompt, cover_path, style)
        
        if cover_result:
            image_paths.append(cover_result)
        
        # Sort panel prompts by panel number
        panel_prompts = sorted([p for p in image_prompts if p["type"] == "panel"], 
                               key=lambda x: x.get("number", 999))
        
        # Generate panel images
        for i, panel_prompt in enumerate(panel_prompts, 1):
            panel_path = f"{STATIC_IMG_DIR}/{story_id}_{timestamp}_panel{i}.jpg"
            panel_result = generate_image(panel_prompt["prompt"], panel_path, style)
            
            if panel_result:
                image_paths.append(panel_result)
    
    except Exception as e:
        print(f"Error in generate_comic_images: {e}")
        traceback.print_exc()
    
    return image_paths

def generate_basic_placeholder_images(story_id, style="comic book"):
    """Generate basic placeholder images when no prompts are available."""
    image_paths = []
    timestamp = get_timestamp()
    
    try:
        # Create a basic cover
        cover_path = f"{STATIC_IMG_DIR}/{story_id}_{timestamp}_cover.jpg"
        cover_prompt = f"Create a captivating comic book cover illustration in {style} style."
        cover_result = create_placeholder_image(cover_path, cover_prompt)
        
        if cover_result:
            image_paths.append(cover_result)
        
        # Create 4 basic panel images
        for i in range(1, 5):
            panel_path = f"{STATIC_IMG_DIR}/{story_id}_{timestamp}_panel{i}.jpg"
            panel_prompt = f"Comic panel {i} in {style} style."
            panel_result = create_placeholder_image(panel_path, panel_prompt)
            
            if panel_result:
                image_paths.append(panel_result)
    
    except Exception as e:
        print(f"Error in generate_basic_placeholder_images: {e}")
    
    return image_paths

# Convert markdown to HTML
def markdown_to_html(markdown_text):
    """Convert markdown text to HTML"""
    html = markdown.markdown(markdown_text)
    return html

# Add custom filters
@app.template_filter('startswith')
def startswith_filter(s, substring):
    """Check if a string starts with a given substring."""
    return s.startswith(substring)

# Add context processor for current year
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.datetime.now().year}

@app.route('/')
def index():
    """Render the main page"""
    stories = load_stories()
    current_year = datetime.datetime.now().year
    return render_template('index.html', stories=stories, current_year=current_year)

@app.route('/generate', methods=['POST'])
def generate():
    """Generate a new story based on prompt, without images"""
    prompt = request.form.get('prompt', 'Generate a short fantasy story')
    num_panels = int(request.form.get('num_panels', 4))
    style = request.form.get('style', 'comic book')
    
    # Generate the story
    markdown_story, _ = generate_story(prompt, num_panels, style)
    
    # Create a unique ID for the story
    story_id = str(uuid.uuid4())
    
    # Skip image generation - create an empty image paths array
    image_paths = []
    
    # Save the story (without images)
    story_data = save_story(prompt, markdown_story, image_paths, [])
    
    # Return JSON response if AJAX request, otherwise redirect
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "story": story_data})
    else:
        return redirect(url_for("story", story_id=story_data["id"]))

@app.route('/story/<story_id>')
def story(story_id):
    """View a specific story"""
    # Find the story with the given ID
    stories = load_stories()
    story_data = None
    for story in stories:
        if story["id"] == story_id:
            story_data = story
            break
    
    if story_data is None:
        return redirect(url_for("index"))
    
    # Convert markdown to HTML
    story_data["html_story"] = Markup(markdown.markdown(story_data["markdown_story"]))
    current_year = datetime.datetime.now().year
    
    return render_template('story.html', story=story_data, current_year=current_year)

@app.template_filter('wordcount')
def wordcount_filter(s):
    """Count the number of words in a string."""
    return len(s.split())

@app.template_filter('split_by_panels')
def split_by_panels_filter(markdown_text):
    """Filter to split a markdown story into intro and panels, 
    cleaning up visual descriptions and focusing on story content."""
    lines = markdown_text.split('\n')
    intro = []
    panels = []
    current_panel = None
    
    # Extract intro (before first panel)
    in_intro = True
    for line in lines:
        if line.startswith('## '):
            in_intro = False
            current_panel = [line]
            panels.append(current_panel)
        elif line.startswith('# '):
            intro.append(line)
        elif in_intro:
            if "Visual Description:" not in line:  # Skip visual descriptions
                intro.append(line)
        elif not in_intro and panels:
            if "Visual Description:" not in line:  # Skip visual descriptions in panels
                panels[-1].append(line)
    
    return intro, panels

@app.template_filter('get_panel')
def get_panel_filter(panels, index):
    """Filter to get the content of a specific panel."""
    if not panels or index >= len(panels):
        return ""
    return " ".join([line.strip() for line in panels[index] if line.strip() and not line.startswith("##")])

@app.route('/regenerate-image/<story_id>/<panel_index>')
def regenerate_image(story_id, panel_index):
    """Regenerate a specific panel image for a story"""
    try:
        # Find the story
        story_path = os.path.join(STORIES_DIR, f"{story_id}.json")
        if not os.path.exists(story_path):
            return jsonify({"success": False, "error": "Story not found"})
        
        with open(story_path, "r") as f:
            story_data = json.load(f)
        
        # Get the appropriate prompt
        image_prompts = story_data.get("image_prompts", [])
        panel_idx = int(panel_index)
        
        if not image_prompts or panel_idx >= len(image_prompts):
            # Fallback to using the panel text
            chapter_info = extract_chapter_titles_and_content(story_data["markdown_story"])
            if panel_idx == 0:  # Cover
                prompt = f"Create a cover image for: {story_data.get('title', 'Comic Story')}"
            elif panel_idx <= len(chapter_info):
                prompt = generate_image_prompt(
                    chapter_info[panel_idx-1]["title"], 
                    chapter_info[panel_idx-1]["content"]
                )
            else:
                return jsonify({"success": False, "error": "Invalid panel index"})
        else:
            # Use the stored prompt
            prompt = image_prompts[panel_idx]["prompt"]
        
        # Generate a new image
        timestamp = get_timestamp()
        
        if panel_idx == 0:  # Cover
            image_path = f"{STATIC_IMG_DIR}/{story_id}_{timestamp}_cover.jpg"
        else:
            image_path = f"{STATIC_IMG_DIR}/{story_id}_{timestamp}_panel{panel_idx}.jpg"
        
        style = "comic book"  # Default style
        image_result = generate_image(prompt, image_path, style)
        
        if image_result:
            # Update the story data with the new image path
            if panel_idx < len(story_data["image_paths"]):
                story_data["image_paths"][panel_idx] = image_result
            else:
                story_data["image_paths"].append(image_result)
            
            # Save the updated story data
            with open(story_path, "w") as f:
                json.dump(story_data, f, indent=2)
            
            return jsonify({
                "success": True, 
                "new_image": image_result,
                "panel_index": panel_idx
            })
        else:
            return jsonify({"success": False, "error": "Failed to generate image"})
        
    except Exception as e:
        print(f"Error regenerating image: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

def create_minimal_image(image_path, prompt_text, style="comic book"):
    """Create a simple comic-style panel with text only - no placeholders"""
    try:
        # Create a colored background image
        width, height = 800, 600
        
        # Use color based on style
        bg_colors = {
            "comic book": (30, 30, 40),  # Dark blue-gray
            "manga": (20, 20, 20),       # Nearly black
            "pixel art": (40, 40, 50),   # Dark indigo
            "watercolor": (40, 30, 30),  # Dark brown
            "3D rendered": (30, 20, 40)  # Dark purple
        }
        
        # Extract style and get background color
        detected_style = style
        for s in bg_colors.keys():
            if s in prompt_text.lower():
                detected_style = s
                break
                
        # Create the image with a dark background
        bg_color = bg_colors.get(detected_style, (30, 30, 40))
        image = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(image)
        
        # Add simple panel border
        border_width = 10
        draw.rectangle(
            [(border_width, border_width), (width-border_width, height-border_width)],
            outline=(220, 220, 220),
            width=border_width//2
        )
        
        # Extract key phrases from prompt
        key_phrases = extract_key_phrases(prompt_text)
        
        # Add title/caption at the top
        title = extract_title(prompt_text)
        title_y = 50
        
        # Draw title with white text on dark background
        draw_centered_text(draw, title, width//2, title_y, (255, 255, 255), font_size=36)
        
        # Add the key phrases as text in the panel
        text_y = height // 3
        for phrase in key_phrases:
            draw_centered_text(draw, phrase, width//2, text_y, (255, 255, 255), font_size=24)
            text_y += 50
            
        # Add a disclaimer at the bottom that doesn't look like a placeholder
        draw_centered_text(
            draw,
            "Click refresh button to regenerate this panel",
            width//2, 
            height - 50,
            (200, 200, 200),
            font_size=18
        )
        
        # Ensure directory exists and save
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image.save(image_path)
        
        return image_path
    except Exception as e:
        print(f"Error creating minimal image: {e}")
        traceback.print_exc()
        
        # Create an absolute minimal image as last resort
        try:
            Image.new('RGB', (400, 300), (40, 40, 40)).save(image_path)
            return image_path
        except:
            return None

def extract_key_phrases(text, max_phrases=3):
    """Extract key phrases from text to display in minimal image"""
    # Split by punctuation and get longer segments
    import re
    segments = re.split(r'[.,;!?]', text)
    segments = [s.strip() for s in segments if len(s.strip()) > 10]
    
    # Sort by length (prefer mid-length phrases that are likely descriptive)
    segments.sort(key=lambda x: abs(len(x) - 50))
    
    # Return top phrases
    return segments[:max_phrases]

def draw_centered_text(draw, text, x, y, color, font_size=24):
    """Draw centered text with wrapping"""
    # Simple word wrap (proper font metrics would be better but this works for basic cases)
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = current_line + [word]
        if len(' '.join(test_line)) * (font_size // 10) < 700:  # rough estimate
            current_line = test_line
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw each line centered
    current_y = y
    for line in lines:
        line_width = len(line) * (font_size // 2)  # rough estimate
        draw.text((x - line_width//2, current_y), line, fill=color)
        current_y += font_size * 1.2

if __name__ == '__main__':
    app.run(debug=True) 