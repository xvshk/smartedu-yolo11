"""
后端服务模块
Backend services model - 业务逻辑层
"""
# 服务接口
from .InterfaceService import (
    IDetectionService, IAuthService, IRuleEngineService,
    IDashboardService, IUserManagementService, IStudentPortraitService
)

# 服务实现
from .DetectionService import DetectionService
from .AuthService import AuthService
from .Rule_engineService import RuleEngine
from .PortraitService import PortraitService

# 依赖注入容器
from .ContainerService import ServiceContainer, get_container, get_service, register_service
from .RegistryService import (
    register_services, configure_default_services,
    get_detection_service, get_auth_service, get_rule_engine_service
)

__all__ = [
    # 接口
    'IDetectionService', 'IAuthService', 'IRuleEngineService',
    'IDashboardService', 'IUserManagementService', 'IStudentPortraitService',
    
    # 实现
    'DetectionService', 'AuthService', 'RuleEngine', 'PortraitService',
    
    # 容器
    'ServiceContainer', 'get_container', 'get_service', 'register_service',
    
    # 注册
    'register_services', 'configure_default_services',
    'get_detection_service', 'get_auth_service', 'get_rule_engine_service'
]
