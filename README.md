# 🚀 AI Comic Generator

A web application that uses Google's Gemini API to generate comic-style stories from simple prompts. This application creates engaging narratives with a comic book aesthetic, complete with stylized panels and matching images.

## ✨ Features

- 🖋️ **AI-Powered Storytelling**: Generate engaging comic-style stories from simple prompts using Google's Gemini API
- 📝 **Comic-Style Formatting**: Stories are displayed with panel layouts, speech bubbles, and sound effects
- 🎭 **Multiple Style Options**: Choose from different comic styles (comic book, manga, pixel art, etc.)
- 🌓 **Dark Mode Design**: Built with a sleek dark theme for better reading experience
- 📱 **Responsive Layout**: Works on desktop and mobile devices
- 💨 **Animated Effects**: Dynamic animations for sound effects and UI elements
- 🔄 **Fallback Mechanism**: Creates placeholder images when API access is limited

## 🖼️ Screenshots

![Screenshot 1](static/img/screenshot-1.png)
![Screenshot 2](static/img/screenshot-2.png)

## 🛠️ Technologies Used

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript
- **AI**: Google Gemini API
- **Image Processing**: PIL (Python Imaging Library)
- **Environment Management**: python-dotenv

## 🔧 Installation

### Prerequisites

- Python 3.8 or higher
- Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### Setup Instructions

1. **Clone the repository**

```bash
git clone https://github.com/ashu/ai-comic-generator.git
cd ai-comic-generator
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

If you encounter permissions issues, you may need to use:

```bash
pip install -r requirements.txt --break-system-packages
```

3. **Set up environment variables**

Copy the `.env.example` file to `.env` and add your Gemini API key:

```bash
cp .env.example .env
```

Edit the `.env` file and add your API key:

```
GEMINI_API_KEY=your_api_key_here
```

4. **Run the application**

```bash
python -m flask run
```

5. **Access the application**

Open your browser and navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000)

## 🎮 Usage

1. Go to the homepage and enter a prompt in the "Story Idea" field
2. Select the number of panels and comic style
3. Click "Generate Story"
4. Wait for the AI to generate your comic story
5. Enjoy reading your personalized comic!

## 🔮 Future Enhancements

- Text-to-speech narration for comics
- Social sharing features
- User accounts to save favorite comics
- More comic style options
- Export to PDF feature

## 📊 Project Structure

```
ai-comic-generator/
├── app.py               # Flask application with Gemini API integration
├── .env                 # Environment variables (create from .env.example)
├── .env.example         # Example environment variables template
├── requirements.txt     # Python dependencies
├── static/              # Static files
│   ├── css/             # CSS styles
│   ├── js/              # JavaScript files
│   └── img/             # Images and assets
├── templates/           # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Homepage
│   └── story.html       # Story display page
└── stories/             # Generated stories (JSON)
```

## 📄 License

This project is licensed under the MIT License.

## 👤 Author

- **Ashu**
- GitHub: [ashu](https://github.com/ashu)

## 🙏 Acknowledgements

- Google for providing the Gemini API
- The Flask team for the excellent web framework
- The open-source community for all the amazing tools

---

⭐ If you find this project useful, please consider giving it a star on GitHub! 