# AI Comics - Immersive AI-Generated Story Experience

AI Comics is an immersive web application that generates short stories with matching images, displayed in a comic book style. The application uses Google's Gemini 2.5 Pro Experimental 03-25 API to generate short stories based on user prompts, followed by image generation using a separate AI model.

## Features

- Dark-themed comic book style design
- Responsive layout for all device sizes
- Immersive reading experience with animations and transitions
- Two-step AI generation process:
  1. Story generation using Gemini 2.5 Pro Experimental 03-25
  2. Image generation using your choice of:
     - Vertex AI's Imagen (recommended for highest quality)
     - Gemini 1.5 Pro (for integrated workflow)
     - Gemini 2.5 Pro (for experimental features)
- Story archive to view all previously generated stories

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **AI Integration**:
  - Google Gemini 2.5 Pro Experimental 03-25 for text generation
  - Multiple options for image generation:
    - Google Vertex AI's Imagen (recommended)
    - Google Gemini 1.5 Pro
    - Google Gemini 2.5 Pro (experimental)
- **Design**: 
  - Comic book inspired UI/UX
  - Animations and transitions for immersive reading

## How It Works

The application follows a two-step AI generation process:

1. **Story Generation**: When a user submits a prompt, it's sent to Gemini 2.5 Pro Experimental 03-25, which generates a short story (approximately 150 words).

2. **Image Generation**: The story is analyzed to create an optimized image prompt, which is then sent to the configured image generation model (Vertex AI Imagen by default, but configurable to use Gemini models instead).

3. **Presentation**: The story and image are combined into a comic-book style presentation with animations and interactive elements.

This modular approach allows you to use the best model for each specific task, resulting in higher quality output.

## Setup and Installation

1. Clone the repository:
   ```
   git clone [repository-url]
   cd ai-comics
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   ```
   cp .env.example .env
   ```
   Then edit the `.env` file to add your API keys and credentials.

5. Run the application:
   ```
   flask run
   ```

6. Open your browser and navigate to `http://127.0.0.1:5000/`

## API Configuration

### Gemini API Setup (for story generation)

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey) to obtain your Gemini API key
2. Add the API key to your `.env` file as `GEMINI_API_KEY`
3. This application is configured to use Gemini 2.5 Pro Experimental 03-25 for optimal story generation

### Image Generation Setup

Choose one of the following options by setting the `IMAGE_GENERATION_MODEL` in your `.env` file:

#### Option 1: Vertex AI's Imagen (recommended)
1. Create a Google Cloud project and enable the Vertex AI API
2. Create a service account with Vertex AI permissions
3. Download the service account JSON key
4. Add the path to the JSON key file to your `.env` file as `GOOGLE_APPLICATION_CREDENTIALS`
5. Set `IMAGE_GENERATION_MODEL=vertex_ai_imagen` in your `.env` file

#### Option 2: Gemini 1.5 Pro
1. Ensure you have a Gemini API key (same as for story generation)
2. Set `IMAGE_GENERATION_MODEL=gemini_1_5_pro` in your `.env` file

#### Option 3: Gemini 2.5 Pro (experimental)
1. Ensure you have a Gemini API key (same as for story generation)
2. Set `IMAGE_GENERATION_MODEL=gemini_2_5_pro` in your `.env` file

## Usage

1. Enter a creative prompt in the story generation form
2. Click "Generate Story" to initiate the two-step AI generation process
3. View your generated story with matching image in comic book style
4. Browse previously generated stories in the gallery
5. Click on a story card to view the full story with its image

## Project Structure

```
ai-comics/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── .env.example           # Example environment variables
├── stories/               # Generated stories storage
├── static/
│   ├── css/
│   │   └── style.css      # Main stylesheet
│   ├── js/
│   │   └── main.js        # Frontend JavaScript
│   └── images/            # Static images
└── templates/
    ├── base.html          # Base template
    ├── index.html         # Homepage
    └── story.html         # Individual story view
```

## Customization

- Edit `static/css/style.css` to modify the visual design
- Adjust animations and interactions in `static/js/main.js`
- Modify the story or image generation parameters in `app.py`
- Choose different image generation models in the `.env` file

## License

[MIT License](LICENSE)

## Acknowledgements

- Google for providing access to Gemini 2.5 Pro Experimental and Vertex AI
- Comic book artists and storytellers for design inspiration 