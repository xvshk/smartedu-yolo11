"""
Flask后端应用主入口
Classroom Behavior Detection System - Backend API
"""
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import Config
from backend.api import auth_bp, user_bp, portrait_bp
from backend.api.settings import settings_bp
from backend.api.detection import detection_bp
from backend.api.alert import alert_bp
from backend.api.notification import notification_bp
from backend.api.dashboard import dashboard_bp

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化扩展
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    JWTManager(app)
    
    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(portrait_bp, url_prefix='/api/portrait')
    app.register_blueprint(detection_bp, url_prefix='/api/detection')
    app.register_blueprint(alert_bp, url_prefix='/api/alert')
    app.register_blueprint(notification_bp, url_prefix='/api/notification')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    
    # 健康检查
    @app.route('/api/health')
    def health_check():
        return {'status': 'ok', 'message': 'Server is running'}
    
    logger.info("Flask application created successfully")
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
