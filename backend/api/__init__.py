# API blueprints
from .auth import auth_bp
from .user import user_bp
from .portrait import portrait_bp
from .alert import alert_bp
from .detection import detection_bp
from .settings import settings_bp

__all__ = ['auth_bp', 'user_bp', 'portrait_bp', 'alert_bp', 'detection_bp', 'settings_bp']
