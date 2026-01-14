"""
服务注册配置
Service registration configuration for dependency injection
"""
import logging
from .ContainerService import ServiceContainer
from .InterfaceService import (
    IDetectionService, IAuthService, IRuleEngineService,
    IDashboardService, IUserManagementService, IStudentPortraitService
)
from .DetectionService import DetectionService
from .AuthService import AuthService
from .Rule_engineService import RuleEngine

logger = logging.getLogger(__name__)


def register_services(container: ServiceContainer) -> None:
    """
    注册所有服务到容器
    
    Args:
        container: 服务容器实例
    """
    # 注册检测服务
    container.register_singleton(IDetectionService, DetectionService)
    
    # 注册认证服务
    container.register_singleton(IAuthService, AuthService)
    
    # 注册规则引擎服务
    container.register_singleton(IRuleEngineService, RuleEngine)
    
    logger.info("All services registered successfully")


def configure_default_services() -> ServiceContainer:
    """
    配置默认服务容器
    
    Returns:
        配置好的服务容器
    """
    from .ContainerService import get_container
    
    container = get_container()
    register_services(container)
    
    return container


def get_detection_service() -> IDetectionService:
    """获取检测服务实例"""
    from .ContainerService import get_service
    return get_service(IDetectionService)


def get_auth_service() -> IAuthService:
    """获取认证服务实例"""
    from .ContainerService import get_service
    return get_service(IAuthService)


def get_rule_engine_service() -> IRuleEngineService:
    """获取规则引擎服务实例"""
    from .ContainerService import get_service
    return get_service(IRuleEngineService)