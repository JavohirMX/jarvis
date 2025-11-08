// Jarvis Landing Page - Main JavaScript

// Navbar scroll effect with debouncing to prevent flickering
let lastScrollY = 0;
let ticking = false;

const updateNavbar = () => {
    const navbar = document.getElementById('navbar');
    const scrollY = window.scrollY;
    
    if (scrollY > 50 && lastScrollY <= 50) {
        navbar.classList.remove('bg-transparent');
        navbar.classList.add('bg-slate-900/95', 'backdrop-blur-lg', 'shadow-lg', 'border-b', 'border-jarvis-purple/20');
    } else if (scrollY <= 50 && lastScrollY > 50) {
        navbar.classList.add('bg-transparent');
        navbar.classList.remove('bg-slate-900/95', 'backdrop-blur-lg', 'shadow-lg', 'border-b', 'border-jarvis-purple/20');
    }
    
    lastScrollY = scrollY;
    ticking = false;
};

window.addEventListener('scroll', () => {
    if (!ticking) {
        window.requestAnimationFrame(updateNavbar);
        ticking = true;
    }
});

// Mobile menu toggle
const mobileMenuButton = document.getElementById('mobile-menu-button');
const mobileMenu = document.getElementById('mobile-menu');

if (mobileMenuButton && mobileMenu) {
    mobileMenuButton.addEventListener('click', () => {
        mobileMenu.classList.toggle('hidden');
    });

    // Close mobile menu when clicking on a link
    const mobileLinks = mobileMenu.querySelectorAll('a');
    mobileLinks.forEach(link => {
        link.addEventListener('click', () => {
            mobileMenu.classList.add('hidden');
        });
    });
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// OS Detection and Download Button
function detectOS() {
    const userAgent = window.navigator.userAgent.toLowerCase();
    const platform = window.navigator.platform.toLowerCase();
    
    if (platform.indexOf('mac') !== -1) {
        return 'macos';
    } else if (platform.indexOf('win') !== -1) {
        return 'windows';
    } else if (platform.indexOf('linux') !== -1 || platform.indexOf('x11') !== -1) {
        return 'linux';
    }
    return 'windows'; // default
}

// Update download buttons based on detected OS
function updateDownloadButtons() {
    const os = detectOS();
    const downloadText = document.getElementById('download-text');
    const downloadCTA = document.getElementById('download-cta');
    const finalDownloadCTA = document.getElementById('final-download-cta');
    
    let osName = 'Windows';
    if (os === 'macos') {
        osName = 'macOS';
    } else if (os === 'linux') {
        osName = 'Linux';
    }
    
    if (downloadText) {
        downloadText.textContent = `Download for ${osName}`;
    }
    
    // Add click handlers for download buttons
    const downloadHandler = (e) => {
        e.preventDefault();
        // Scroll to download section
        const downloadSection = document.getElementById('download');
        if (downloadSection) {
            downloadSection.scrollIntoView({ behavior: 'smooth' });
        }
    };
    
    if (downloadCTA) {
        downloadCTA.addEventListener('click', downloadHandler);
    }
    if (finalDownloadCTA) {
        finalDownloadCTA.addEventListener('click', downloadHandler);
    }
}

// Platform selector tabs in download section
const platformTabs = document.querySelectorAll('.platform-tab');
const downloadCards = document.querySelectorAll('.download-card');

platformTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const platform = tab.dataset.platform;
        
        // Update tab states
        platformTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Update card visibility
        downloadCards.forEach(card => {
            if (card.dataset.platform === platform) {
                card.classList.add('active');
            } else {
                card.classList.remove('active');
            }
        });
    });
});

// FAQ Accordion
const faqItems = document.querySelectorAll('.faq-item');

faqItems.forEach(item => {
    item.addEventListener('click', () => {
        const content = item.querySelector('.faq-content');
        const icon = item.querySelector('.faq-icon');
        
        // Toggle current item
        content.classList.toggle('hidden');
        icon.classList.toggle('rotate-180');
        
        // Optional: Close other FAQ items (uncomment if you want accordion behavior)
        // faqItems.forEach(otherItem => {
        //     if (otherItem !== item) {
        //         const otherContent = otherItem.querySelector('.faq-content');
        //         const otherIcon = otherItem.querySelector('.faq-icon');
        //         otherContent.classList.add('hidden');
        //         otherIcon.classList.remove('rotate-180');
        //     }
        // });
    });
});

// Scroll-triggered animations with smoother transitions
const observerOptions = {
    threshold: 0.15,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
            // Add slight delay for staggered effect
            setTimeout(() => {
                entry.target.style.opacity = '0';
                entry.target.style.transform = 'translateY(20px)';
                entry.target.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
                
                requestAnimationFrame(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                });
                
                observer.unobserve(entry.target);
            }, index * 50);
        }
    });
}, observerOptions);

// Observe cards and feature elements
document.addEventListener('DOMContentLoaded', () => {
    // Update download buttons
    updateDownloadButtons();
    
    // Observe elements for animations
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        observer.observe(card);
    });
});

// Add download click handlers for platform cards
document.addEventListener('DOMContentLoaded', () => {
    const downloadButtons = document.querySelectorAll('.download-card button');
    
    downloadButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const card = button.closest('.download-card');
            const platform = card.dataset.platform;
            
            // Show download message (placeholder - replace with actual download logic)
            alert(`Downloading Jarvis for ${platform}...\n\nNote: This is a demo. In production, this would initiate the actual download.`);
        });
    });
});

// Add hover effect to feature cards
const featureCards = document.querySelectorAll('.card');
featureCards.forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-4px)';
    });
    
    card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
    });
});

// Keyboard accessibility for FAQ
faqItems.forEach(item => {
    item.setAttribute('tabindex', '0');
    item.setAttribute('role', 'button');
    item.setAttribute('aria-expanded', 'false');
    
    item.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            item.click();
            const isExpanded = !item.querySelector('.faq-content').classList.contains('hidden');
            item.setAttribute('aria-expanded', isExpanded.toString());
        }
    });
});

console.log('🤖 Jarvis Landing Page loaded successfully!');

