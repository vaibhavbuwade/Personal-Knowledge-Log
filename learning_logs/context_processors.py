"""
Context processors for AI Notes & Document Assistant.
Provides global template variables for AI service status and application branding.
"""

from .ai_service import get_ai_service_status


def ai_status_processor(request):
    """
    Exposes active AI provider status to all templates.
    Enables user-friendly status indicators and setup hints without exposing secrets.
    """
    return {
        'ai_status': get_ai_service_status(),
        'app_brand_name': 'AI Notes & Document Assistant',
    }
