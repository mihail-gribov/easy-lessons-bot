"""Tests for service registry functionality."""

import pytest
from unittest.mock import patch, MagicMock

from core.service_registry import (
    initialize_services,
    get_llm_client,
    get_prompt_store,
    get_session_manager,
    get_database_manager,
    get_graceful_degradation_manager,
    get_error_message_store,
)


class TestServiceRegistry:
    """Test cases for service registry."""

    def test_initialize_services(self):
        """Test that initialize_services registers all services."""
        with patch("core.service_registry.register_service") as mock_register:
            initialize_services()
            
            # Verify all services are registered
            expected_services = [
                "llm_client",
                "prompt_store", 
                "session_manager",
                "database_manager",
                "graceful_degradation_manager",
                "error_message_store",
            ]
            
            assert mock_register.call_count == len(expected_services)
            
            # Check that all expected services were registered
            registered_services = [call[0][0] for call in mock_register.call_args_list]
            for service in expected_services:
                assert service in registered_services

    def test_get_llm_client(self):
        """Test getting LLM client from container."""
        with patch("core.di_container.get_service") as mock_get_service:
            mock_client = MagicMock()
            mock_get_service.return_value = mock_client
            
            result = get_llm_client()
            
            assert result == mock_client
            mock_get_service.assert_called_once_with("llm_client")

    def test_get_prompt_store(self):
        """Test getting prompt store from container."""
        with patch("core.di_container.get_service") as mock_get_service:
            mock_store = MagicMock()
            mock_get_service.return_value = mock_store
            
            result = get_prompt_store()
            
            assert result == mock_store
            mock_get_service.assert_called_once_with("prompt_store")

    def test_get_session_manager(self):
        """Test getting session manager from container."""
        with patch("core.di_container.get_service") as mock_get_service:
            mock_manager = MagicMock()
            mock_get_service.return_value = mock_manager
            
            result = get_session_manager()
            
            assert result == mock_manager
            mock_get_service.assert_called_once_with("session_manager")

    def test_get_database_manager(self):
        """Test getting database manager from container."""
        with patch("core.di_container.get_service") as mock_get_service:
            mock_manager = MagicMock()
            mock_get_service.return_value = mock_manager
            
            result = get_database_manager()
            
            assert result == mock_manager
            mock_get_service.assert_called_once_with("database_manager")

    def test_get_graceful_degradation_manager(self):
        """Test getting graceful degradation manager from container."""
        with patch("core.di_container.get_service") as mock_get_service:
            mock_manager = MagicMock()
            mock_get_service.return_value = mock_manager
            
            result = get_graceful_degradation_manager()
            
            assert result == mock_manager
            mock_get_service.assert_called_once_with("graceful_degradation_manager")

    def test_get_error_message_store(self):
        """Test getting error message store from container."""
        with patch("core.di_container.get_service") as mock_get_service:
            mock_store = MagicMock()
            mock_get_service.return_value = mock_store
            
            result = get_error_message_store()
            
            assert result == mock_store
            mock_get_service.assert_called_once_with("error_message_store")
