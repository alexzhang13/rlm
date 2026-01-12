"""Tests for LocalREPL persistence features.

These tests verify LocalREPL's multi-context and multi-history capabilities
which support the persistent=True mode in RLM for multi-turn conversations.
"""

from rlm.environments.local_repl import LocalREPL


class TestLocalREPLMultiContext:
    """Tests for multi-context support in persistent mode."""

    def test_add_context_versioning(self):
        """Test that add_context creates versioned variables."""
        repl = LocalREPL()
        repl.add_context("First", 0)
        repl.add_context("Second", 1)
        assert repl.locals["context_0"] == "First"
        assert repl.locals["context_1"] == "Second"
        assert repl.locals["context"] == "First"
        assert repl.get_context_count() == 2
        repl.cleanup()

    def test_update_handler_address(self):
        """Test handler address can be updated."""
        repl = LocalREPL(lm_handler_address=("127.0.0.1", 5000))
        repl.update_handler_address(("127.0.0.1", 6000))
        assert repl.lm_handler_address == ("127.0.0.1", 6000)
        repl.cleanup()

    def test_add_context_auto_increment(self):
        """Test that add_context auto-increments when no index provided."""
        repl = LocalREPL()
        idx1 = repl.add_context("First")
        idx2 = repl.add_context("Second")
        assert idx1 == 0
        assert idx2 == 1
        assert repl.locals["context_0"] == "First"
        assert repl.locals["context_1"] == "Second"
        assert repl.get_context_count() == 2
        repl.cleanup()

    def test_contexts_accessible_in_code(self):
        """Test that multiple contexts can be accessed in code execution."""
        repl = LocalREPL()
        repl.add_context("Document A content")
        repl.add_context("Document B content")

        result = repl.execute_code("combined = f'{context_0} + {context_1}'")
        assert result.stderr == ""
        assert repl.locals["combined"] == "Document A content + Document B content"
        repl.cleanup()

    def test_context_alias_points_to_first(self):
        """Test that 'context' always aliases context_0."""
        repl = LocalREPL()
        repl.add_context("First")
        repl.add_context("Second")
        repl.add_context("Third")

        result = repl.execute_code("is_first = context == context_0")
        assert result.stderr == ""
        assert repl.locals["is_first"] is True
        repl.cleanup()


class TestLocalREPLHistory:
    """Tests for message history storage in LocalREPL for persistent sessions."""

    def test_add_history_basic(self):
        """Test that add_history stores message history correctly."""
        repl = LocalREPL()

        history = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        index = repl.add_history(history)

        assert index == 0
        assert "history_0" in repl.locals
        assert "history" in repl.locals  # alias
        assert repl.locals["history_0"] == history
        assert repl.locals["history"] == history
        assert repl.get_history_count() == 1

        repl.cleanup()

    def test_add_multiple_histories(self):
        """Test adding multiple conversation histories."""
        repl = LocalREPL()

        history1 = [{"role": "user", "content": "First conversation"}]
        history2 = [{"role": "user", "content": "Second conversation"}]

        repl.add_history(history1)
        repl.add_history(history2)

        assert repl.get_history_count() == 2
        assert repl.locals["history_0"] == history1
        assert repl.locals["history_1"] == history2
        assert repl.locals["history"] == history1  # alias stays on first

        repl.cleanup()

    def test_history_accessible_via_code(self):
        """Test that stored history is accessible via code execution."""
        repl = LocalREPL()

        history = [{"role": "user", "content": "Test message"}]
        repl.add_history(history)

        result = repl.execute_code("msg = history[0]['content']")
        assert result.stderr == ""
        assert repl.locals["msg"] == "Test message"

        repl.cleanup()

    def test_history_is_copy(self):
        """Test that stored history is a copy, not a reference."""
        repl = LocalREPL()

        history = [{"role": "user", "content": "Original"}]
        repl.add_history(history)

        history[0]["content"] = "Modified"

        assert repl.locals["history_0"][0]["content"] == "Original"

        repl.cleanup()

    def test_can_iterate_histories_in_code(self):
        """Test iterating through multiple histories in code."""
        repl = LocalREPL()

        repl.add_history([{"role": "user", "content": "Query 1"}])
        repl.add_history([{"role": "user", "content": "Query 2"}])
        repl.add_history([{"role": "user", "content": "Query 3"}])

        code = """
all_contents = [
    history_0[0]['content'],
    history_1[0]['content'],
    history_2[0]['content'],
]
"""
        result = repl.execute_code(code)
        assert result.stderr == ""
        assert repl.locals["all_contents"] == ["Query 1", "Query 2", "Query 3"]

        repl.cleanup()


class TestLocalREPLPersistentState:
    """Tests for state persistence across multiple operations in a single REPL instance."""

    def test_variables_persist_with_contexts(self):
        """Variables and contexts should coexist."""
        repl = LocalREPL()

        repl.add_context("My context data")
        repl.execute_code("summary = context.upper()")
        assert repl.locals["summary"] == "MY CONTEXT DATA"

        repl.add_context("New context")

        assert repl.locals["summary"] == "MY CONTEXT DATA"
        assert repl.locals["context_1"] == "New context"

        repl.cleanup()

    def test_variables_persist_with_histories(self):
        """Variables and histories should coexist."""
        repl = LocalREPL()

        repl.add_history([{"role": "user", "content": "Hello"}])
        repl.execute_code("extracted = history[0]['content']")
        assert repl.locals["extracted"] == "Hello"

        repl.add_history([{"role": "user", "content": "World"}])

        assert repl.locals["extracted"] == "Hello"
        assert repl.locals["history_1"][0]["content"] == "World"

        repl.cleanup()

    def test_full_persistent_session_simulation(self):
        """Simulate a multi-turn persistent session."""
        repl = LocalREPL()

        repl.add_context("Document: Sales were $1000")
        repl.execute_code("sales = 1000")

        repl.add_context("Document: Costs were $400")
        result = repl.execute_code("profit = sales - 400")
        assert result.stderr == ""
        assert repl.locals["profit"] == 600

        repl.add_history(
            [
                {"role": "user", "content": "What were the sales?"},
                {"role": "assistant", "content": "Sales were $1000"},
            ]
        )

        code = """
summary = f"Sales: {context_0}, Costs: {context_1}, Profit: {profit}"
prev_question = history_0[0]['content']
"""
        result = repl.execute_code(code)
        assert result.stderr == ""
        assert "Profit: 600" in repl.locals["summary"]
        assert repl.locals["prev_question"] == "What were the sales?"

        assert repl.get_context_count() == 2
        assert repl.get_history_count() == 1

        repl.cleanup()
