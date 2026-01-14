"""
服务容器 - 依赖注入容器
Service Container for Dependency Injection
"""
import logging
from typing import Any, Dict, Type, TypeVar, Optional, Callable
from .InterfaceService import (
    IDetectionService, IAuthService, IRuleEngineService,
    IDashboardService, IUserManagementService, IStudentPortraitService
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceContainer:
    """服务容器 - 管理服务实例和依赖注入"""
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}
    
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """
        注册单例服务
        
        Args:
            interface: 服务接口类型
            implementation: 服务实现类型
        """
        self._services[interface] = implementation
        logger.info(f"Registered singleton: {interface.__name__} -> {implementation.__name__}")
    
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """
        注册瞬态服务（每次获取都创建新实例）
        
        Args:
            interface: 服务接口类型
            implementation: 服务实现类型
        """
        self._services[interface] = implementation
        logger.info(f"Registered transient: {interface.__name__} -> {implementation.__name__}")
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """
        注册工厂方法
        
        Args:
            interface: 服务接口类型
            factory: 工厂方法
        """
        self._factories[interface] = factory
        logger.info(f"Registered factory for: {interface.__name__}")
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """
        注册服务实例
        
        Args:
            interface: 服务接口类型
            instance: 服务实例
        """
        self._singletons[interface] = instance
        logger.info(f"Registered instance: {interface.__name__}")
    
    def get(self, interface: Type[T]) -> T:
        """
        获取服务实例
        
        Args:
            interface: 服务接口类型
            
        Returns:
            服务实例
            
        Raises:
            ValueError: 如果服务未注册
        """
        # 检查是否有已注册的实例
        if interface in self._singletons:
            return self._singletons[interface]
        
        # 检查是否有工厂方法
        if interface in self._factories:
            instance = self._factories[interface]()
            self._singletons[interface] = instance
            return instance
        
        # 检查是否有注册的实现类
        if interface in self._services:
            implementation = self._services[interface]
            try:
                # 尝试创建实例
                instance = implementation()
                self._singletons[interface] = instance
                return instance
            except Exception as e:
                logger.error(f"Failed to create instance of {implementation.__name__}: {e}")
                raise
        
        raise ValueError(f"Service not registered: {interface.__name__}")
    
    def get_optional(self, interface: Type[T]) -> Optional[T]:
        """
        获取可选服务实例
        
        Args:
            interface: 服务接口类型
            
        Returns:
            服务实例或None
        """
        try:
            return self.get(interface)
        except ValueError:
            return None
    
    def is_registered(self, interface: Type[T]) -> bool:
        """
        检查服务是否已注册
        
        Args:
            interface: 服务接口类型
            
        Returns:
            是否已注册
        """
        return (interface in self._services or 
                interface in self._factories or 
                interface in self._singletons)
    
    def clear(self) -> None:
        """清空所有注册的服务"""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        logger.info("Service container cleared")


# 全局服务容器实例
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """获取全局服务容器"""
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container


def configure_services() -> ServiceContainer:
    """
    配置默认服务
    
    Returns:
        配置好的服务容器
    """
    container = get_container()
    
    # 这里可以注册默认的服务实现
    # 实际的服务注册应该在应用启动时进行
    
    logger.info("Services configured")
    return container


# 便捷方法
def get_service(interface: Type[T]) -> T:
    """获取服务实例的便捷方法"""
    return get_container().get(interface)


def register_service(interface: Type[T], implementation: Type[T]) -> None:
    """注册服务的便捷方法"""
    get_container().register_singleton(interface, implementation)