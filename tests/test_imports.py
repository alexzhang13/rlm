"""Tests to verify all imports are correct and non-conflicting."""

import importlib
import sys
from collections import defaultdict

import pytest


class TestTopLevelImports:
    """Test top-level package imports."""

    def test_rlm_import(self):
        """Test that main rlm package can be imported."""
        import rlm

        assert hasattr(rlm, "RLM")
        assert "RLM" in rlm.__all__

    def test_rlm_rlm_import(self):
        """Test that RLM class can be imported from rlm."""
        from rlm import RLM

        assert RLM is not None

    def test_rlm_core_rlm_import(self):
        """Test that RLM can be imported from rlm.core.rlm."""
        from rlm.core.rlm import RLM

        assert RLM is not None


class TestClientImports:
    """Test client module imports."""

    def test_clients_module_import(self):
        """Test that clients module can be imported."""
        import rlm.clients

        assert hasattr(rlm.clients, "get_client")
        assert hasattr(rlm.clients, "BaseLM")

    def test_base_lm_import(self):
        """Test BaseLM import."""
        from rlm.clients.base_lm import BaseLM

        assert BaseLM is not None

    def test_openai_client_import(self):
        """Test OpenAIClient import."""
        pytest.importorskip("openai")
        from rlm.clients.openai import OpenAIClient

        assert OpenAIClient is not None

    def test_anthropic_client_import(self):
        """Test AnthropicClient import."""
        pytest.importorskip("anthropic")
        from rlm.clients.anthropic import AnthropicClient

        assert AnthropicClient is not None

    def test_portkey_client_import(self):
        """Test PortkeyClient import."""
        pytest.importorskip("portkey_ai")
        from rlm.clients.portkey import PortkeyClient

        assert PortkeyClient is not None

    def test_litellm_client_import(self):
        """Test LiteLLMClient import."""
        pytest.importorskip("litellm")
        from rlm.clients.litellm import LiteLLMClient

        assert LiteLLMClient is not None

    def test_get_client_function(self):
        """Test get_client function import."""
        from rlm.clients import get_client

        assert callable(get_client)


class TestCoreImports:
    """Test core module imports."""

    def test_core_types_import(self):
        """Test core types imports."""
        from rlm.core.types import (
            ClientBackend,
            CodeBlock,
            ModelUsageSummary,
            QueryMetadata,
            REPLResult,
            RLMIteration,
            RLMMetadata,
            UsageSummary,
        )

        assert ClientBackend is not None
        assert CodeBlock is not None
        assert ModelUsageSummary is not None
        assert QueryMetadata is not None
        assert REPLResult is not None
        assert RLMIteration is not None
        assert RLMMetadata is not None
        assert UsageSummary is not None

    def test_core_rlm_import(self):
        """Test core RLM import."""
        from rlm.core.rlm import RLM

        assert RLM is not None

    def test_core_lm_handler_import(self):
        """Test LMHandler import."""
        from rlm.core.lm_handler import LMHandler

        assert LMHandler is not None

    def test_core_comms_utils_import(self):
        """Test comms_utils imports."""
        from rlm.core.comms_utils import (
            LMRequest,
            LMResponse,
            send_lm_request,
            send_lm_request_batched,
            socket_recv,
            socket_send,
        )

        assert LMRequest is not None
        assert LMResponse is not None
        assert callable(send_lm_request)
        assert callable(send_lm_request_batched)
        assert callable(socket_recv)
        assert callable(socket_send)


class TestEnvironmentImports:
    """Test environment module imports."""

    def test_environments_module_import(self):
        """Test that environments module can be imported."""
        import rlm.environments

        assert hasattr(rlm.environments, "get_environment")
        assert hasattr(rlm.environments, "BaseEnv")
        assert hasattr(rlm.environments, "LocalREPL")

    def test_base_env_import(self):
        """Test BaseEnv import."""
        from rlm.environments.base_env import BaseEnv, IsolatedEnv, NonIsolatedEnv

        assert BaseEnv is not None
        assert IsolatedEnv is not None
        assert NonIsolatedEnv is not None

    def test_local_repl_import(self):
        """Test LocalREPL import."""
        from rlm.environments.local_repl import LocalREPL

        assert LocalREPL is not None

    def test_modal_repl_import(self):
        """Test ModalREPL import."""
        pytest.importorskip("modal")
        from rlm.environments.modal_repl import ModalREPL

        assert ModalREPL is not None

    def test_docker_repl_import(self):
        """Test DockerREPL import."""
        from rlm.environments.docker_repl import DockerREPL

        assert DockerREPL is not None

    def test_prime_repl_import(self):
        """Test PrimeREPL import."""
        pytest.importorskip("prime_sandboxes")
        from rlm.environments.prime_repl import PrimeREPL

        assert PrimeREPL is not None

    def test_get_environment_function(self):
        """Test get_environment function import."""
        from rlm.environments import get_environment

        assert callable(get_environment)


class TestLoggerImports:
    """Test logger module imports."""

    def test_logger_module_import(self):
        """Test that logger module can be imported."""
        import rlm.logger

        assert hasattr(rlm.logger, "RLMLogger")
        assert hasattr(rlm.logger, "VerbosePrinter")
        assert "RLMLogger" in rlm.logger.__all__
        assert "VerbosePrinter" in rlm.logger.__all__

    def test_rlm_logger_import(self):
        """Test RLMLogger import."""
        from rlm.logger.rlm_logger import RLMLogger

        assert RLMLogger is not None

    def test_verbose_import(self):
        """Test VerbosePrinter import."""
        from rlm.logger.verbose import VerbosePrinter

        assert VerbosePrinter is not None


class TestUtilsImports:
    """Test utils module imports."""

    def test_parsing_import(self):
        """Test parsing module import."""
        from rlm.utils.parsing import (
            find_code_blocks,
            find_final_answer,
            format_execution_result,
            format_iteration,
        )

        assert callable(find_code_blocks)
        assert callable(find_final_answer)
        assert callable(format_iteration)
        assert callable(format_execution_result)

    def test_prompts_import(self):
        """Test prompts module import."""
        from rlm.utils.prompts import (
            RLM_SYSTEM_PROMPT,
            USER_PROMPT,
            build_rlm_system_prompt,
            build_user_prompt,
        )

        assert RLM_SYSTEM_PROMPT is not None
        assert USER_PROMPT is not None
        assert callable(build_rlm_system_prompt)
        assert callable(build_user_prompt)

    def test_rlm_utils_import(self):
        """Test rlm_utils module import."""
        from rlm.utils.rlm_utils import filter_sensitive_keys

        assert callable(filter_sensitive_keys)


class TestImportConflicts:
    """Test for import conflicts and naming issues."""

    def test_no_duplicate_names_in_rlm_all(self):
        """Test that __all__ in rlm.__init__ has no duplicates."""
        import rlm

        if hasattr(rlm, "__all__"):
            all_items = rlm.__all__
            assert len(all_items) == len(set(all_items)), (
                f"Duplicate items in rlm.__all__: {all_items}"
            )

    def test_no_duplicate_names_in_logger_all(self):
        """Test that __all__ in rlm.logger.__init__ has no duplicates."""
        import rlm.logger

        if hasattr(rlm.logger, "__all__"):
            all_items = rlm.logger.__all__
            assert len(all_items) == len(set(all_items)), (
                f"Duplicate items in rlm.logger.__all__: {all_items}"
            )

    def test_all_declarations_match_exports(self):
        """Test that __all__ declarations match actual exports."""
        import rlm
        import rlm.logger

        # Test rlm.__all__
        if hasattr(rlm, "__all__"):
            for name in rlm.__all__:
                assert hasattr(rlm, name), f"rlm.__all__ declares '{name}' but it's not exported"

        # Test rlm.logger.__all__
        if hasattr(rlm.logger, "__all__"):
            for name in rlm.logger.__all__:
                assert hasattr(rlm.logger, name), (
                    f"rlm.logger.__all__ declares '{name}' but it's not exported"
                )

    def test_no_circular_imports(self):
        """Test that modules can be imported without circular import errors."""
        # Core modules that should always be importable
        core_modules = [
            "rlm",
            "rlm.clients",
            "rlm.clients.base_lm",
            "rlm.core",
            "rlm.core.types",
            "rlm.core.rlm",
            "rlm.core.lm_handler",
            "rlm.core.comms_utils",
            "rlm.environments",
            "rlm.environments.base_env",
            "rlm.environments.local_repl",
            "rlm.environments.docker_repl",
            "rlm.logger",
            "rlm.logger.rlm_logger",
            "rlm.logger.verbose",
            "rlm.utils",
            "rlm.utils.parsing",
            "rlm.utils.prompts",
            "rlm.utils.rlm_utils",
        ]

        # Optional modules that may not be available
        optional_modules = [
            ("rlm.clients.openai", "openai"),
            ("rlm.clients.anthropic", "anthropic"),
            ("rlm.clients.portkey", "portkey_ai"),
            ("rlm.clients.litellm", "litellm"),
            ("rlm.environments.modal_repl", "modal"),
            ("rlm.environments.prime_repl", "prime_sandboxes"),
        ]

        # Test core modules
        for module_name in core_modules:
            # Remove from sys.modules if present to test fresh import
            if module_name in sys.modules:
                del sys.modules[module_name]
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

        # Test optional modules (skip if dependency not available)
        for module_name, dependency in optional_modules:
            # Check if dependency is available
            try:
                importlib.import_module(dependency)
            except ImportError:
                continue  # Skip this module if dependency not available

            # If dependency is available, test the module import
            if module_name in sys.modules:
                del sys.modules[module_name]
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    def test_no_naming_conflicts_across_modules(self):
        """Test that there are no naming conflicts across different modules."""
        # Collect all public names from each module
        module_exports: dict[str, set[str]] = {}

        # Check main modules
        import rlm
        import rlm.clients
        import rlm.environments
        import rlm.logger

        if hasattr(rlm, "__all__"):
            module_exports["rlm"] = set(rlm.__all__)
        else:
            module_exports["rlm"] = {name for name in dir(rlm) if not name.startswith("_")}

        if hasattr(rlm.clients, "__all__"):
            module_exports["rlm.clients"] = set(rlm.clients.__all__)
        else:
            module_exports["rlm.clients"] = {
                name for name in dir(rlm.clients) if not name.startswith("_")
            }

        if hasattr(rlm.environments, "__all__"):
            module_exports["rlm.environments"] = set(rlm.environments.__all__)
        else:
            module_exports["rlm.environments"] = {
                name for name in dir(rlm.environments) if not name.startswith("_")
            }

        if hasattr(rlm.logger, "__all__"):
            module_exports["rlm.logger"] = set(rlm.logger.__all__)
        else:
            module_exports["rlm.logger"] = {
                name for name in dir(rlm.logger) if not name.startswith("_")
            }

        # Check for conflicts (same name in multiple modules)
        name_to_modules: dict[str, list[str]] = defaultdict(list)
        for module_name, exports in module_exports.items():
            for export_name in exports:
                name_to_modules[export_name].append(module_name)

        conflicts = {name: modules for name, modules in name_to_modules.items() if len(modules) > 1}
        # Filter out common Python builtins/dunders and typing imports that are expected
        expected_duplicates = {
            "__file__",
            "__name__",
            "__package__",
            "__path__",
            "__doc__",
            "__loader__",
            "__spec__",
            "__cached__",
            "Any",  # Common typing import
            "Literal",  # Common typing import
            "Optional",  # Common typing import
            "Union",  # Common typing import
            "Dict",  # Common typing import
            "List",  # Common typing import
            "Tuple",  # Common typing import
            "Callable",  # Common typing import
        }
        conflicts = {
            name: modules for name, modules in conflicts.items() if name not in expected_duplicates
        }

        if conflicts:
            conflict_msg = "\n".join(
                f"  '{name}' exported from: {', '.join(modules)}"
                for name, modules in conflicts.items()
            )
            pytest.fail(f"Found naming conflicts across modules:\n{conflict_msg}")


class TestImportCompleteness:
    """Test that all expected imports are available."""

    def test_all_client_classes_importable(self):
        """Test that all client classes can be imported."""
        from rlm.clients.base_lm import BaseLM

        # Verify BaseLM is a class
        assert isinstance(BaseLM, type)

        # Test optional client classes
        try:
            pytest.importorskip("openai")
            from rlm.clients.openai import OpenAIClient

            assert isinstance(OpenAIClient, type)
        except Exception:
            pass

        try:
            pytest.importorskip("anthropic")
            from rlm.clients.anthropic import AnthropicClient

            assert isinstance(AnthropicClient, type)
        except Exception:
            pass

        try:
            pytest.importorskip("portkey_ai")
            from rlm.clients.portkey import PortkeyClient

            assert isinstance(PortkeyClient, type)
        except Exception:
            pass

        try:
            pytest.importorskip("litellm")
            from rlm.clients.litellm import LiteLLMClient

            assert isinstance(LiteLLMClient, type)
        except Exception:
            pass

    def test_all_environment_classes_importable(self):
        """Test that all environment classes can be imported."""
        from rlm.environments.base_env import BaseEnv, IsolatedEnv, NonIsolatedEnv
        from rlm.environments.docker_repl import DockerREPL
        from rlm.environments.local_repl import LocalREPL

        # Verify they're all classes
        assert isinstance(BaseEnv, type)
        assert isinstance(IsolatedEnv, type)
        assert isinstance(NonIsolatedEnv, type)
        assert isinstance(LocalREPL, type)
        assert isinstance(DockerREPL, type)

        # Test optional ModalREPL
        try:
            pytest.importorskip("modal")
            from rlm.environments.modal_repl import ModalREPL

            assert isinstance(ModalREPL, type)
        except Exception:
            pass

        # Test optional PrimeREPL
        try:
            pytest.importorskip("prime_sandboxes")
            from rlm.environments.prime_repl import PrimeREPL

            assert isinstance(PrimeREPL, type)
        except Exception:
            pass
