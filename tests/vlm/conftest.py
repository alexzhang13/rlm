import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum number of RLM iterations per test (default: 10)",
    )


@pytest.fixture
def max_iterations(request: pytest.FixtureRequest) -> int:
    return request.config.getoption("--max-iterations")
