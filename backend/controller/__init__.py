# API blueprints
from .AuthController import auth_bp
from .UserController import user_bp
from .PortraitController import portrait_bp
from .AlertController import alert_bp
from .DetectionController import detection_bp
from .SettingsController import settings_bp
from .NotificationController import notification_bp
from .DashboardController import dashboard_bp

__all__ = ['auth_bp', 'user_bp', 'portrait_bp', 'alert_bp', 'detection_bp', 'settings_bp', 'notification_bp', 'dashboard_bp']
