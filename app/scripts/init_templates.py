# app/scripts/init_templates.py
from ..database import supabase
from ..data.default_templates import DEFAULT_TEMPLATES

async def init_default_templates():
    """Initialize default templates in the database"""
    try:
        # Check if templates already exist
        existing = supabase.table('templates')\
            .select('name')\
            .execute()
            
        existing_names = [t['name'] for t in existing.data]
        
        # Insert only new templates
        for template in DEFAULT_TEMPLATES:
            if template['name'] not in existing_names:
                supabase.table('templates')\
                    .insert(template)\
                    .execute()
                
        print(f"Successfully initialized {len(DEFAULT_TEMPLATES)} default templates")
    except Exception as e:
        print(f"Error initializing templates: {str(e)}")

# Call this function when setting up the application
if __name__ == "__main__":
    init_default_templates()