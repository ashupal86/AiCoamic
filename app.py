from flask import Flask, render_template, request, jsonify
from markupsafe import Markup
import os
import json
import markdown
import re
from datetime import datetime

app = Flask(__name__)

# Mock function for Gemini API integration (to be replaced with actual API call)
def generate_story(prompt):
    """
    Generate a longer story (up to 500 words) using Gemini 2.5 Pro Experimental 03-25 (mockup for now)
    
    Note: When implementing the real API, use Gemini 2.5 Pro Experimental 03-25
    for enhanced story generation capabilities, and instruct it to:
    1. Generate a 500-word story
    2. Structure it with markdown headers
    3. Include image placement markers with image prompts
    """
    # This will be replaced with actual Gemini API call
    # For now, we'll return a mock story with markdown formatting
    
    # Example structured story format that would come from Gemini
    markdown_story = f"""
# The Echo of Imagination

![panel1](A character standing at the threshold of a mystical doorway, surrounded by swirling elements related to: {prompt}, in dramatic comic book style, dark color palette with vibrant purple accents)

In a world inspired by your prompt: '{prompt}', the boundaries between reality and imagination began to blur. Sarah found herself standing at the edge of an ordinary day when the first signs appeared. Colors seemed more vibrant, sounds carried hidden melodies, and shadows cast patterns that shouldn't exist.

"Something's changed," she whispered, tracing her fingers along the wall where a faint luminescent trail appeared and disappeared with her touch.

## The Discovery

![panel2](Close-up of character's eyes reflecting magical elements, with expressions of wonder and determination, comic book style with stark lighting)

That evening, Sarah discovered an ancient book in her attic, its cover inscribed with symbols that rearranged themselves when she blinked. The pages felt warm to her touch, and as she began reading, the words lifted from the paper, swirling around her like fireflies.

"Every story needs a reader," the words formed in the air, "just as every reader needs a story."

Sarah nodded, understanding instinctively that she had been chosen for something extraordinary. The book was a gateway to a realm where imagination took physical form, where thoughts became reality and dreams walked beside their dreamers.

## The Journey Begins

![panel3](A vast landscape transitioning from mundane to fantastical, with the character stepping forward into unknown territory, comic book perspective with dynamic angles)

The first step through the gateway felt like passing through a veil of water—cool, resistant, then suddenly giving way. The landscape before her transformed from her dusty attic into a vast expanse where islands floated in the sky and rivers flowed upward.

"Welcome, Storyteller," a voice echoed from everywhere and nowhere.

Sarah turned to find a figure composed of shifting pages and flowing ink, features rearranging continuously as though unable to settle on a single form.

"What is this place?" she asked, her voice steady despite her racing heart.

"This is the Narrative Realm, where stories are born," the figure replied. "We've been waiting for someone who could bridge the worlds."

## The Challenge

![panel4](A confrontation scene with shadowy figures threatening the bright world of stories, dramatic lighting with contrast between dark threats and colorful story elements)

Not all was well in this realm of stories, however. Sarah soon discovered dark entities that fed on unfinished tales, consuming creative potential and leaving emptiness behind. These "Void Speakers," as the locals called them, had been growing stronger, threatening to unravel the fabric of imagination itself.

"You brought something we haven't had in centuries," the ink figure explained, pointing to the book Sarah still clutched. "A new perspective. Fresh ideas. The ability to complete stories that have been abandoned."

Sarah understood her purpose now. Every story she completed would strengthen the realm against the encroaching void. Every character she developed would stand against the dissolution of their world.

## The Resolution

![panel5](The character wielding creative energy like a weapon/tool, surrounded by manifestations of stories coming to life, vibrant comic book action scene)

Sarah spent what felt like both moments and lifetimes in the Narrative Realm. She learned to wield words like weapons, to sketch characters into existence with a gesture, to speak plots into being. Under her influence, the realm began to heal.

The final confrontation with the Void Speakers came unexpectedly. They surrounded her, formless shadows with hungry depths.

"Your stories cannot last," they hissed in unison. "All tales end. All books close."

Sarah smiled, opening her hands to reveal glowing symbols similar to those on her book. "True," she admitted. "But new ones begin. That's the power of imagination—it's endless."

With that declaration, she released the energy she had gathered, a cascade of creativity that illuminated the darkest corners of the realm. The Void Speakers retreated before this display of unfettered imagination.

## Return and Legacy

![panel6](The character returning to the normal world but transformed, with subtle elements showing their connection to the story realm remains, intimate comic book scene with symbolic elements)

When Sarah eventually returned to her world, she brought something back with her—a connection to the Narrative Realm that would never be severed. Ordinary life seemed different now, charged with potential and hidden meaning.

She began writing, pouring stories onto paper that somehow felt more real than mere fiction. Readers reported dreams of floating islands and ink-formed guides after finishing her books. Some even found faint luminescent trails on their walls that appeared when they touched them after reading.

The boundary between worlds remained thin around her, just as you suggested in your prompt. And perhaps, for those with enough imagination to see it, that boundary exists for all of us—waiting for the right story to help us cross over.
"""
    
    # Extract image prompts from the markdown
    image_prompts = re.findall(r'!\[(\w+)\]\((.*?)\)', markdown_story)
    
    # Return both the markdown story and extracted image prompts
    return {
        "story": markdown_story,
        "image_prompts": [{"panel": panel, "prompt": prompt} for panel, prompt in image_prompts]
    }

# Function to create an image prompt based on the story panel
def create_image_prompt(panel_prompt):
    """
    Create a detailed image prompt based on the panel description
    
    In the actual implementation, this could use another Gemini API call
    to refine the image prompt for better results
    """
    # The story generation now includes specific image prompts per panel
    # so we'll just return the panel prompt directly
    return panel_prompt

# Mock function for image generation using a different model
def generate_image(image_prompt):
    """
    Generate an image using a different model capable of image generation
    
    Options include:
    1. Vertex AI's Imagen (preferred for production quality)
    2. Gemini 1.5 Pro (for integrated text-to-image generation)
    3. Gemini 2.5 Pro (experimental image capabilities)
    
    Note: Each model has different strengths for image generation
    """
    # This will be replaced with actual API call to the selected image generation model
    # For now, we'll just return a placeholder
    print(f"Generating image with prompt: {image_prompt}")
    return "/static/images/placeholder.jpg"

# Store generated stories
STORIES_DIR = "stories"
os.makedirs(STORIES_DIR, exist_ok=True)

def save_story(story_data):
    """Save generated story to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    story_id = f"story_{timestamp}"
    filename = f"{STORIES_DIR}/{story_id}.json"
    
    with open(filename, 'w') as f:
        json.dump(story_data, f)
    
    return story_id

def get_all_stories():
    """Get all saved stories"""
    stories = []
    if os.path.exists(STORIES_DIR):
        for filename in os.listdir(STORIES_DIR):
            if filename.endswith('.json'):
                with open(os.path.join(STORIES_DIR, filename), 'r') as f:
                    story_data = json.load(f)
                    story_data['id'] = filename.split('.')[0]
                    stories.append(story_data)
    return sorted(stories, key=lambda x: x.get('created_at', ''), reverse=True)

# Convert markdown to HTML
def markdown_to_html(markdown_text):
    """Convert markdown text to HTML"""
    return markdown.markdown(markdown_text)

# Add context processor for current year
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

@app.route('/')
def index():
    """Render the main page"""
    stories = get_all_stories()
    return render_template('index.html', stories=stories)

@app.route('/generate', methods=['POST'])
def generate():
    """Generate a new story and image based on prompt"""
    user_prompt = request.form.get('prompt', 'Generate a short fantasy story')
    
    # Step 1: Generate story using Gemini 2.5 Pro Experimental 03-25
    # This now returns both the story in markdown format and extracted image prompts
    story_data = generate_story(user_prompt)
    markdown_story = story_data["story"]
    image_prompts = story_data["image_prompts"]
    
    # Step 2: Generate images for each panel
    images = []
    for panel in image_prompts:
        # Generate image using the panel-specific prompt
        image_url = generate_image(panel["prompt"])
        images.append({
            "panel": panel["panel"],
            "url": image_url,
            "prompt": panel["prompt"]
        })
    
    # Step 3: Convert markdown to HTML for display
    html_story = markdown_to_html(markdown_story)
    
    # Save the complete story data
    story_obj = {
        "prompt": user_prompt,
        "markdown_story": markdown_story,
        "html_story": html_story,
        "images": images,
        "created_at": datetime.now().isoformat()
    }
    
    # Save story and get the story ID
    story_id = save_story(story_obj)
    
    # Add the ID to the response object
    story_obj["id"] = story_id
    
    return jsonify({"success": True, "story": story_obj})

@app.route('/story/<story_id>')
def view_story(story_id):
    """View a specific story"""
    filename = f"{STORIES_DIR}/{story_id}.json"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            story_data = json.load(f)
            # Convert the HTML story to a Markup object to prevent escaping
            if "html_story" in story_data:
                story_data["html_story"] = Markup(story_data["html_story"])
        return render_template('story.html', story=story_data)
    return "Story not found", 404

if __name__ == '__main__':
    app.run(debug=True) 