"""Tests for new services in service registry."""

from unittest.mock import MagicMock, patch

import pytest

from core.service_registry import (
    get_prompt_loader,
    get_context_analyzer,
    get_dialog_builder,
    initialize_services,
)


class TestNewServices:
    """Test cases for new services in service registry."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear container before each test
        from core.di_container import get_container
        get_container().clear()

    def test_initialize_services_registers_new_services(self):
        """Test that initialize_services registers new services."""
        initialize_services()
        
        from core.di_container import get_container
        container = get_container()
        
        # Check that new services are registered
        assert container.is_registered("prompt_loader")
        assert container.is_registered("context_analyzer")
        assert container.is_registered("dialog_builder")

    def test_get_prompt_loader(self):
        """Test getting prompt loader from DI container."""
        initialize_services()
        
        prompt_loader = get_prompt_loader()
        assert prompt_loader is not None
        assert hasattr(prompt_loader, "get_system_prompt")
        assert hasattr(prompt_loader, "get_scenario_prompt")

    def test_get_context_analyzer(self):
        """Test getting context analyzer from DI container."""
        initialize_services()
        
        context_analyzer = get_context_analyzer()
        assert context_analyzer is not None
        assert hasattr(context_analyzer, "analyze_context_with_auxiliary_model")
        assert hasattr(context_analyzer, "identify_topic_with_llm")

    def test_get_dialog_builder(self):
        """Test getting dialog builder from DI container."""
        initialize_services()
        
        dialog_builder = get_dialog_builder()
        assert dialog_builder is not None
        assert hasattr(dialog_builder, "build_context")
        assert hasattr(dialog_builder, "build_dialog_context")

    def test_services_are_singletons(self):
        """Test that new services are singletons."""
        initialize_services()
        
        prompt_loader1 = get_prompt_loader()
        prompt_loader2 = get_prompt_loader()
        assert prompt_loader1 is prompt_loader2
        
        context_analyzer1 = get_context_analyzer()
        context_analyzer2 = get_context_analyzer()
        assert context_analyzer1 is context_analyzer2
        
        dialog_builder1 = get_dialog_builder()
        dialog_builder2 = get_dialog_builder()
        assert dialog_builder1 is dialog_builder2

    def test_prompt_store_uses_di_services(self):
        """Test that PromptStore uses services from DI container."""
        initialize_services()
        
        from core.prompt_store import PromptStore
        prompt_store = PromptStore()
        
        # Should use services from DI container
        assert prompt_store._prompt_loader is get_prompt_loader()
        assert prompt_store._context_analyzer is get_context_analyzer()
        assert prompt_store._dialog_builder is get_dialog_builder()
