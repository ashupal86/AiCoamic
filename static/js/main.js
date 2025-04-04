document.addEventListener('DOMContentLoaded', function() {
    // Initialize animation observers
    initializeAnimations();
    
    // Setup form submission
    setupFormHandlers();
    
    // Initialize comic panel interactions
    initializePanelInteractions();
});

// Scroll animations with Intersection Observer
function initializeAnimations() {
    // Fade in animations for story elements
    const fadeElements = document.querySelectorAll('.fade-in');
    const staggerElements = document.querySelectorAll('.stagger-fade-in');
    
    const fadeObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = 1;
                entry.target.style.transform = 'translateY(0)';
                fadeObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    fadeElements.forEach(el => {
        el.style.opacity = 0;
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
        fadeObserver.observe(el);
    });
    
    staggerElements.forEach(container => {
        const children = Array.from(container.children);
        children.forEach((child, index) => {
            child.style.opacity = 0;
            child.style.transform = 'translateY(20px)';
            child.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
            child.style.transitionDelay = `${index * 0.2}s`;
            fadeObserver.observe(child);
        });
    });
    
    // Parallax effect for story images
    const parallaxImages = document.querySelectorAll('.story-image');
    
    window.addEventListener('scroll', () => {
        parallaxImages.forEach(image => {
            const scrollPosition = window.pageYOffset;
            const imagePosition = image.offsetTop;
            const distance = scrollPosition - imagePosition;
            
            if (Math.abs(distance) < window.innerHeight) {
                image.style.transform = `translateY(${distance * 0.1}px)`;
            }
        });
    });
}

// Setup form submission for story generation
function setupFormHandlers() {
    const generateForm = document.getElementById('generate-form');
    
    if (generateForm) {
        generateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<div class="loading-circle"></div>';
            
            // Get form data
            const formData = new FormData(this);
            
            // Send request to the server
            fetch('/generate', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.story && data.story.id) {
                    // Redirect to the story page with the correct ID
                    window.location.href = `/story/${data.story.id}`;
                } else if (data.success) {
                    // If there's no ID but success is true, show the latest story
                    console.log("Story generated successfully but no ID provided, redirecting to homepage");
                    window.location.href = '/';
                } else {
                    showError('Failed to generate story. Please try again.');
                }
            })
            .catch(err => {
                console.error('Error:', err);
                showError('An error occurred. Please try again.');
            })
            .finally(() => {
                // Reset button state
                submitBtn.disabled = false;
                submitBtn.textContent = originalBtnText;
            });
        });
    }
}

// Initialize interactive behaviors for comic panels
function initializePanelInteractions() {
    const comicPanels = document.querySelectorAll('.comic-panel');
    
    comicPanels.forEach(panel => {
        panel.addEventListener('mouseenter', function() {
            // Add subtle animation or effect on hover
            this.style.zIndex = '10';
        });
        
        panel.addEventListener('mouseleave', function() {
            // Reset after hover
            this.style.zIndex = '1';
        });
        
        // Make panels clickable to view the full story
        panel.addEventListener('click', function() {
            const storyLink = this.getAttribute('data-story-link');
            if (storyLink) {
                window.location.href = storyLink;
            }
        });
    });
    
    // Add comic sound effects on button clicks
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Create a temporary element for the sound effect
            const soundEffect = document.createElement('div');
            soundEffect.classList.add('sound-effect');
            soundEffect.textContent = ["POW!", "ZAP!", "BOOM!", "WHAM!"][Math.floor(Math.random() * 4)];
            soundEffect.style.position = 'absolute';
            soundEffect.style.left = `${e.clientX - 30}px`;
            soundEffect.style.top = `${e.clientY - 30}px`;
            soundEffect.style.fontFamily = "'Bangers', cursive";
            soundEffect.style.fontSize = '2rem';
            soundEffect.style.color = 'var(--accent-primary)';
            soundEffect.style.pointerEvents = 'none';
            soundEffect.style.zIndex = '9999';
            soundEffect.style.animation = 'popAndFade 0.6s forwards';
            
            document.body.appendChild(soundEffect);
            
            // Remove the element after animation completes
            setTimeout(() => {
                document.body.removeChild(soundEffect);
            }, 600);
        });
    });
    
    // Define the animation in a style element
    const styleElement = document.createElement('style');
    styleElement.textContent = `
        @keyframes popAndFade {
            0% { transform: scale(0); opacity: 0; }
            40% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(1); opacity: 0; }
        }
    `;
    document.head.appendChild(styleElement);
}

// Display error messages
function showError(message) {
    const errorContainer = document.querySelector('.error-message') || createErrorContainer();
    errorContainer.textContent = message;
    errorContainer.style.opacity = '1';
    
    // Auto hide after 5 seconds
    setTimeout(() => {
        errorContainer.style.opacity = '0';
    }, 5000);
}

// Create error container if it doesn't exist
function createErrorContainer() {
    const container = document.createElement('div');
    container.classList.add('error-message');
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.padding = '15px 20px';
    container.style.background = 'var(--error)';
    container.style.color = 'white';
    container.style.borderRadius = '5px';
    container.style.boxShadow = '0 4px 10px rgba(0,0,0,0.3)';
    container.style.zIndex = '9999';
    container.style.transition = 'opacity 0.3s ease';
    
    document.body.appendChild(container);
    return container;
} 