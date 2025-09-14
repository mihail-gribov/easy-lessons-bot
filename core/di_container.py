"""Dependency Injection container for managing service instances."""

import logging
from typing import Any, Callable, Dict, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceContainer:
    """Dependency injection container for managing service instances."""

    def __init__(self):
        """Initialize service container."""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}
        self._singleton_flags: Dict[str, bool] = {}

    def register(
        self,
        service_name: str,
        factory: Callable[[], Any],
        singleton: bool = True
    ) -> None:
        """
        Register a service with the container.

        Args:
            service_name: Name of the service
            factory: Factory function to create the service
            singleton: Whether to create singleton instances
        """
        self._factories[service_name] = factory
        self._singleton_flags[service_name] = singleton
        logger.debug("Registered service: %s (singleton=%s)", service_name, singleton)

    def register_instance(self, service_name: str, instance: Any) -> None:
        """
        Register a service instance directly.

        Args:
            service_name: Name of the service
            instance: Service instance
        """
        self._services[service_name] = instance
        logger.debug("Registered service instance: %s", service_name)

    def get(self, service_name: str) -> Any:
        """
        Get a service instance.

        Args:
            service_name: Name of the service

        Returns:
            Service instance

        Raises:
            KeyError: If service is not registered
        """
        # Check if we have a direct instance
        if service_name in self._services:
            return self._services[service_name]

        # Check if we have a factory
        if service_name in self._factories:
            factory = self._factories[service_name]
            is_singleton = self._singleton_flags.get(service_name, True)
            
            # For singletons, check if we already have an instance
            if is_singleton and service_name in self._singletons:
                return self._singletons[service_name]
            
            # Create new instance
            instance = factory()
            
            # Store singleton instance only if it's a singleton
            if is_singleton:
                self._singletons[service_name] = instance
                logger.debug("Created singleton service instance: %s", service_name)
            else:
                logger.debug("Created non-singleton service instance: %s", service_name)
            
            return instance

        raise KeyError(f"Service '{service_name}' is not registered")

    def is_registered(self, service_name: str) -> bool:
        """
        Check if a service is registered.

        Args:
            service_name: Name of the service

        Returns:
            True if service is registered
        """
        return (
            service_name in self._services or
            service_name in self._factories
        )

    def clear(self) -> None:
        """Clear all registered services and instances."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._singleton_flags.clear()
        logger.debug("Cleared all services from container")

    def get_all_services(self) -> Dict[str, Any]:
        """
        Get all registered service names.

        Returns:
            Dictionary of service names and their types
        """
        services = {}
        
        # Add direct instances
        for name, instance in self._services.items():
            services[name] = type(instance).__name__
        
        # Add factory services
        for name in self._factories:
            if name not in services:
                services[name] = "Factory"
        
        return services


# Global service container instance
_container: ServiceContainer | None = None


def get_container() -> ServiceContainer:
    """Get global service container instance."""
    global _container  # noqa: PLW0603
    if _container is None:
        _container = ServiceContainer()
    return _container


def register_service(
    service_name: str,
    factory: Callable[[], Any],
    singleton: bool = True
) -> None:
    """
    Register a service with the global container.

    Args:
        service_name: Name of the service
        factory: Factory function to create the service
        singleton: Whether to create singleton instances
    """
    container = get_container()
    container.register(service_name, factory, singleton)


def register_instance(service_name: str, instance: Any) -> None:
    """
    Register a service instance with the global container.

    Args:
        service_name: Name of the service
        instance: Service instance
    """
    container = get_container()
    container.register_instance(service_name, instance)


def get_service(service_name: str) -> Any:
    """
    Get a service from the global container.

    Args:
        service_name: Name of the service

    Returns:
        Service instance
    """
    container = get_container()
    return container.get(service_name)


def is_service_registered(service_name: str) -> bool:
    """
    Check if a service is registered in the global container.

    Args:
        service_name: Name of the service

    Returns:
        True if service is registered
    """
    container = get_container()
    return container.is_registered(service_name)
