"""Tests for dependency injection container functionality."""

import pytest
from unittest.mock import MagicMock

from core.di_container import ServiceContainer, get_container, register_service, get_service


class TestServiceContainer:
    """Test cases for service container."""

    def test_register_and_get_service(self):
        """Test registering and getting a service."""
        container = ServiceContainer()
        
        # Create a mock factory
        mock_instance = MagicMock()
        mock_factory = MagicMock(return_value=mock_instance)
        
        # Register service
        container.register("test_service", mock_factory, singleton=True)
        
        # Get service
        result = container.get("test_service")
        
        # Verify
        assert result == mock_instance
        mock_factory.assert_called_once()

    def test_register_and_get_singleton(self):
        """Test that singleton services return the same instance."""
        container = ServiceContainer()
        
        # Create a mock factory
        mock_instance = MagicMock()
        mock_factory = MagicMock(return_value=mock_instance)
        
        # Register service as singleton
        container.register("test_service", mock_factory, singleton=True)
        
        # Get service multiple times
        result1 = container.get("test_service")
        result2 = container.get("test_service")
        
        # Verify same instance returned
        assert result1 == result2 == mock_instance
        # Factory should only be called once for singleton
        mock_factory.assert_called_once()

    def test_register_and_get_non_singleton(self):
        """Test that non-singleton services return new instances."""
        container = ServiceContainer()
        
        # Create a mock factory that returns different instances
        instance1 = MagicMock()
        instance2 = MagicMock()
        mock_factory = MagicMock(side_effect=[instance1, instance2])
        
        # Register service as non-singleton
        container.register("test_service", mock_factory, singleton=False)
        
        # Get service multiple times
        result1 = container.get("test_service")
        result2 = container.get("test_service")
        
        # Verify different instances returned
        assert result1 == instance1
        assert result2 == instance2
        assert result1 != result2
        # Factory should be called for each request
        assert mock_factory.call_count == 2

    def test_register_instance(self):
        """Test registering a service instance directly."""
        container = ServiceContainer()
        
        # Create a mock instance
        mock_instance = MagicMock()
        
        # Register instance
        container.register_instance("test_service", mock_instance)
        
        # Get service
        result = container.get("test_service")
        
        # Verify
        assert result == mock_instance

    def test_get_unregistered_service_raises_error(self):
        """Test that getting unregistered service raises KeyError."""
        container = ServiceContainer()
        
        with pytest.raises(KeyError, match="Service 'test_service' is not registered"):
            container.get("test_service")

    def test_is_registered(self):
        """Test checking if service is registered."""
        container = ServiceContainer()
        
        # Initially not registered
        assert not container.is_registered("test_service")
        
        # Register service
        container.register("test_service", MagicMock(), singleton=True)
        assert container.is_registered("test_service")
        
        # Register instance
        container.register_instance("test_instance", MagicMock())
        assert container.is_registered("test_instance")

    def test_clear(self):
        """Test clearing all services."""
        container = ServiceContainer()
        
        # Register some services
        container.register("service1", MagicMock(), singleton=True)
        container.register_instance("service2", MagicMock())
        
        # Verify registered
        assert container.is_registered("service1")
        assert container.is_registered("service2")
        
        # Clear
        container.clear()
        
        # Verify cleared
        assert not container.is_registered("service1")
        assert not container.is_registered("service2")

    def test_get_all_services(self):
        """Test getting all registered services."""
        container = ServiceContainer()
        
        # Register some services
        mock_instance = MagicMock()
        container.register("factory_service", MagicMock(), singleton=True)
        container.register_instance("instance_service", mock_instance)
        
        # Get all services
        services = container.get_all_services()
        
        # Verify
        assert "factory_service" in services
        assert "instance_service" in services
        assert services["factory_service"] == "Factory"
        assert services["instance_service"] == type(mock_instance).__name__


class TestGlobalContainer:
    """Test cases for global container functions."""

    def test_get_container_singleton(self):
        """Test that get_container returns singleton."""
        container1 = get_container()
        container2 = get_container()
        
        assert container1 is container2

    def test_register_and_get_service_globally(self):
        """Test registering and getting service using global functions."""
        # Create a mock factory
        mock_instance = MagicMock()
        mock_factory = MagicMock(return_value=mock_instance)
        
        # Register service
        register_service("test_service", mock_factory, singleton=True)
        
        # Get service
        result = get_service("test_service")
        
        # Verify
        assert result == mock_instance
        mock_factory.assert_called_once()

    def test_register_service_with_default_singleton(self):
        """Test that register_service defaults to singleton=True."""
        # Clear container to avoid state from other tests
        container = get_container()
        container.clear()
        
        # Create a mock factory
        mock_instance = MagicMock()
        mock_factory = MagicMock(return_value=mock_instance)
        
        # Register service without specifying singleton
        register_service("test_service", mock_factory)
        
        # Get service multiple times
        result1 = get_service("test_service")
        result2 = get_service("test_service")
        
        # Verify same instance returned (singleton behavior)
        assert result1 == result2 == mock_instance
        mock_factory.assert_called_once()
