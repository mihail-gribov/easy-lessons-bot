"""Service registry for initializing all services in the DI container."""

import logging

from core.di_container import get_container, register_service
from core.llm_client import LLMClient
from core.prompt_store import PromptStore
from core.session_state import SessionManager
from core.persistence.database import DatabaseManager
from core.graceful_degradation import GracefulDegradationManager
from core.error_messages import ErrorMessageStore
from core.prompts.prompt_loader import PromptLoader
from core.context.context_analyzer import ContextAnalyzer
from core.dialog.dialog_builder import DialogBuilder

logger = logging.getLogger(__name__)


def initialize_services() -> None:
    """Initialize all services in the DI container."""
    logger.info("Initializing services in DI container")
    
    # Register core services
    register_service("llm_client", LLMClient, singleton=True)
    register_service("prompt_store", PromptStore, singleton=True)
    register_service("session_manager", SessionManager, singleton=True)
    register_service("database_manager", DatabaseManager, singleton=True)
    register_service("graceful_degradation_manager", GracefulDegradationManager, singleton=True)
    register_service("error_message_store", ErrorMessageStore, singleton=True)
    
    # Register new refactored services
    register_service("prompt_loader", PromptLoader, singleton=True)
    register_service("context_analyzer", ContextAnalyzer, singleton=True)
    register_service("dialog_builder", DialogBuilder, singleton=True)
    
    logger.info("All services registered in DI container")


def get_llm_client() -> LLMClient:
    """Get LLM client from DI container."""
    from core.di_container import get_service
    return get_service("llm_client")


def get_prompt_store() -> PromptStore:
    """Get prompt store from DI container."""
    from core.di_container import get_service
    return get_service("prompt_store")


def get_session_manager() -> SessionManager:
    """Get session manager from DI container."""
    from core.di_container import get_service
    return get_service("session_manager")


def get_database_manager() -> DatabaseManager:
    """Get database manager from DI container."""
    from core.di_container import get_service
    return get_service("database_manager")


def get_graceful_degradation_manager() -> GracefulDegradationManager:
    """Get graceful degradation manager from DI container."""
    from core.di_container import get_service
    return get_service("graceful_degradation_manager")


def get_error_message_store() -> ErrorMessageStore:
    """Get error message store from DI container."""
    from core.di_container import get_service
    return get_service("error_message_store")


def get_prompt_loader() -> PromptLoader:
    """Get prompt loader from DI container."""
    from core.di_container import get_service
    return get_service("prompt_loader")


def get_context_analyzer() -> ContextAnalyzer:
    """Get context analyzer from DI container."""
    from core.di_container import get_service
    return get_service("context_analyzer")


def get_dialog_builder() -> DialogBuilder:
    """Get dialog builder from DI container."""
    from core.di_container import get_service
    return get_service("dialog_builder")
