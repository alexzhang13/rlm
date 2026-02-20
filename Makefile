.PHONY: help install install-dev install-modal run-all \
        quickstart docker-repl lm-repl modal-repl \
        lint format test check \
        build-vlm-all build-vlm-basic test-vlm test-vlm-basic

help:
	@echo "RLM Examples Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make install        - Install base dependencies with uv"
	@echo "  make install-dev    - Install dev dependencies with uv"
	@echo "  make install-modal  - Install modal dependencies with uv"
	@echo "  make run-all        - Run all examples (requires all deps and API keys)"
	@echo ""
	@echo "Examples:"
	@echo "  make quickstart     - Run quickstart.py (needs OPENAI_API_KEY)"
	@echo "  make docker-repl    - Run docker_repl_example.py (needs Docker)"
	@echo "  make lm-repl        - Run lm_in_repl.py (needs PORTKEY_API_KEY)"
	@echo "  make modal-repl     - Run modal_repl_example.py (needs Modal)"
	@echo ""
	@echo "Development:"
	@echo "  make lint           - Run ruff linter"
	@echo "  make format         - Run ruff formatter"
	@echo "  make test           - Run tests"
	@echo "  make check          - Run lint + format + tests"
	@echo ""
	@echo "VLM Tests (require Docker + OPENAI_API_KEY):"
	@echo "  make test-vlm       - Build all VLM images and run all VLM tests"
	@echo "  make test-vlm-basic - Build and run test_one_image + test_pdf2image only"

install:
	uv sync

install-dev:
	uv sync --group dev --group test

install-modal:
	uv pip install -e ".[modal]"

run-all: quickstart docker-repl lm-repl modal-repl

quickstart: install
	uv run python -m examples.quickstart

docker-repl: install
	uv run python -m examples.docker_repl_example

lm-repl: install
	uv run python -m examples.lm_in_repl

modal-repl: install-modal
	uv run python -m examples.modal_repl_example

lint: install-dev
	uv run ruff check .

format: install-dev
	uv run ruff format .

test: install-dev
	uv run pytest

check: lint format test

# VLM Tests (require Docker and OPENAI_API_KEY)
VLM_DOCKERFILE = tests/vlm/Dockerfile
VLM_FIXTURES   = test_one_image test_n_images test_pdf2image test_supported_formats

build-vlm-all:
	@for fixture in $(VLM_FIXTURES); do \
		echo "Building rlm-vlm-$$fixture..."; \
		docker build -f $(VLM_DOCKERFILE) --build-arg FIXTURE=$$fixture -t rlm-vlm-$$fixture . ; \
	done

build-vlm-basic:
	docker build -f $(VLM_DOCKERFILE) --build-arg FIXTURE=test_one_image -t rlm-vlm-test-one-image .
	docker build -f $(VLM_DOCKERFILE) --build-arg FIXTURE=test_pdf2image  -t rlm-vlm-test-pdf2image  .

docker-rm-all:
	@for fixture in $(VLM_FIXTURES); do \
		echo "Removing rlm-vlm-$$fixture..."; \
		docker rmi rlm-vlm-$$fixture; \
	done

MAX_ITERATIONS ?= 10

test-vlm: build-vlm-all
	uv run pytest tests/vlm/ -v --max-iterations=$(MAX_ITERATIONS)

test-vlm-basic: build-vlm-basic
	uv run pytest tests/vlm/ -k "test_one_image or test_pdf2image" -v --max-iterations=$(MAX_ITERATIONS)

clean:
	docker-rm-all