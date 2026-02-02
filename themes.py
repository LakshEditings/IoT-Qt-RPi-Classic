THEMES = {
    "Default": {
        "primary1": "#0078d7",   # Original blue
        "primary2": "#e07b00",   # Original orange
        "secondary1": "#222222", # Original background
        "secondary2": "#1c0707", # Original dial background
        "secondary3": "#fcfcfc", # Original text color
        "accent": "#2ca02c",     # Original total dial color
    },
    "Obsidian": {
        "primary1": "#00A8E8",   # Vibrant Cyan
        "primary2": "#0077B6",   # Deep Cyan
        "secondary1": "#0A0F1A", # Deep Space Black
        "secondary2": "#1C2526", # Dark Metallic
        "secondary3": "#E6F1FA", # Off-White
        "accent": "#FFD700",     # Gold Accent
    },
    "Titanium": {
        "primary1": "#4CAF50",   # Emerald Green
        "primary2": "#388E3C",   # Forest Green
        "secondary1": "#E8ECEF", # Light Titanium
        "secondary2": "#CFD8DC", # Medium Titanium
        "secondary3": "#212121", # Dark Gray
        "accent": "#FF5722",     # Coral Accent
    },
    "Neon": {
        "primary1": "#FF007A",   # Neon Pink
        "primary2": "#C51162",   # Deep Pink
        "secondary1": "#120321", # Dark Void
        "secondary2": "#2A0A3F", # Purple Haze
        "secondary3": "#FFFFFF", # Pure White
        "accent": "#00FFCC",     # Neon Cyan
    },
    "Aurora": {
        "primary1": "#7B68EE",   # Medium Purple
        "primary2": "#6A5ACD",   # Slate Blue
        "secondary1": "#1B263B", # Night Sky
        "secondary2": "#415A77", # Deep Ocean
        "secondary3": "#E0E7FF", # Light Indigo
        "accent": "#FFB6C1",     # Light Pink
    }
}

class ThemeManager:
    def __init__(self):
        self.current_theme = "Default"
    
    def get_theme(self):
        return THEMES[self.current_theme]
    
    def set_theme(self, theme_name):
        self.current_theme = theme_name

# Global theme manager
theme_manager = ThemeManager()