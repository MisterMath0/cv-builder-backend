# app/data/default_templates.py
from uuid import uuid4

MODERN_TEMPLATE = {
    "id": str(uuid4()),
    "name": "Modern Professional",
    "description": "A clean, modern layout with emphasis on readability and professional appearance",
    "thumbnail_url": "/templates/modern.png",
    "category": "Professional",
    "is_public": True,
    "style_config": {
        "font_family": "Inter, sans-serif",
        "colors": {
            "primary": "#2563eb",  # Blue
            "secondary": "#64748b",  # Slate
            "text": "#1e293b",      # Dark slate
            "background": "#ffffff", # White
            "accent": "#dbeafe"     # Light blue
        },
        "spacing": {
            "section_gap": "2rem",
            "item_gap": "1rem",
            "padding": "2rem"
        },
        "layout": "single-column",
        "custom_css": """
            .section-title {
                color: var(--primary);
                font-size: 1.25rem;
                font-weight: 600;
                border-bottom: 2px solid var(--primary);
                padding-bottom: 0.5rem;
                margin-bottom: 1rem;
            }
        """
    },
    "sections": [
        {
            "type": "contact",
            "title": "Contact Information",
            "required": True,
            "order_index": 0,
            "style_config": {
                "layout": "grid",
                "columns": 2,
                "align": "left"
            }
        },
        {
            "type": "text",
            "title": "Professional Summary",
            "required": True,
            "order_index": 1,
            "style_config": {
                "font_size": "1rem",
                "line_height": "1.5"
            }
        },
        {
            "type": "experience",
            "title": "Work Experience",
            "required": True,
            "order_index": 2,
            "style_config": {
                "item_spacing": "1.5rem",
                "company_style": "font-bold text-lg",
                "date_style": "text-sm text-secondary",
                "position_style": "font-semibold text-primary"
            }
        },
        {
            "type": "education",
            "title": "Education",
            "required": True,
            "order_index": 3,
            "style_config": {
                "item_spacing": "1.5rem",
                "institution_style": "font-bold",
                "degree_style": "text-primary"
            }
        },
        {
            "type": "skills",
            "title": "Skills",
            "required": True,
            "order_index": 4,
            "style_config": {
                "layout": "grid",
                "columns": 2
            }
        },
        {
            "type": "languages",
            "title": "Languages",
            "required": False,
            "order_index": 5,
            "style_config": {
                "layout": "grid",
                "columns": 2
            }
        }
    ]
}

MINIMAL_TEMPLATE = {
    "id": str(uuid4()),
    "name": "Minimal Classic",
    "description": "A minimalist design focusing on content with subtle styling",
    "thumbnail_url": "/templates/minimal.png",
    "category": "Professional",
    "is_public": True,
    "style_config": {
        "font_family": "system-ui, sans-serif",
        "colors": {
            "primary": "#18181b",   # Almost black
            "secondary": "#71717a",  # Gray
            "text": "#27272a",      # Dark gray
            "background": "#ffffff", # White
            "accent": "#f4f4f5"     # Light gray
        },
        "spacing": {
            "section_gap": "1.5rem",
            "item_gap": "0.75rem",
            "padding": "1.5rem"
        },
        "layout": "single-column",
        "custom_css": """
            .section-title {
                font-size: 1.125rem;
                font-weight: 600;
                margin-bottom: 0.75rem;
            }
        """
    },
    "sections": [
        # Similar section structure with different styling
    ]
}

CREATIVE_TEMPLATE = {
    "id": str(uuid4()),
    "name": "Creative Bold",
    "description": "A creative layout with bold colors and modern design elements",
    "thumbnail_url": "/templates/creative.png",
    "category": "Creative",
    "is_public": True,
    "style_config": {
        "font_family": "Poppins, sans-serif",
        "colors": {
            "primary": "#7c3aed",   # Purple
            "secondary": "#a78bfa",  # Light purple
            "text": "#1f2937",      # Gray
            "background": "#ffffff", # White
            "accent": "#f3f4f6"     # Light gray
        },
        "spacing": {
            "section_gap": "2.5rem",
            "item_gap": "1.25rem",
            "padding": "2rem"
        },
        "layout": "two-column",
        "custom_css": """
            .section-title {
                color: var(--primary);
                font-size: 1.5rem;
                font-weight: 700;
                margin-bottom: 1.25rem;
                position: relative;
            }
            .section-title::after {
                content: '';
                position: absolute;
                bottom: -0.5rem;
                left: 0;
                width: 2rem;
                height: 0.25rem;
                background-color: var(--primary);
                border-radius: 0.125rem;
            }
        """
    },
    "sections": [
        # Similar section structure with creative styling
    ]
}

# Add more templates...

DEFAULT_TEMPLATES = [
    MODERN_TEMPLATE,
    MINIMAL_TEMPLATE,
    CREATIVE_TEMPLATE,
    # Add more templates here
]