SHELL := /bin/bash

.SILENT:

.PHONY: all install add-deps add-prod-deps format test precommit docs check ci clean venv poetry debug

# === CI vs Local Environment Setup ===
ifdef CI
    export PRE_COMMIT_HOME := ~/.cache/pre-commit
    export RUN := poetry run
    export INSTALL_CMD := poetry install --no-cache --with dev,docs --no-interaction
else
    export VENV_PATH := /tmp/darca-space-venv
    export POETRY_HOME := /tmp/poetry-space-cache
    export POETRY_CONFIG_DIR := /tmp/poetry-space-config
    export POETRY_CACHE_DIR := $(POETRY_HOME)
    export POETRY_VIRTUALENVS_PATH := $(VENV_PATH)
    export PYTHONPYCACHEPREFIX := /tmp/space-pycache
    export PYTHON_KEYRING_BACKEND := keyring.backends.null.Keyring
    export POETRY_BIN := $(VENV_PATH)/bin/poetry
    export RUN := $(POETRY_BIN) run
    export INSTALL_CMD := $(POETRY_BIN) install --no-cache --with dev,docs --no-interaction
    export PRE_COMMIT_HOME := /tmp/precommit-space-cache
endif

# Poetry runner abstraction
export RUN_POETRY := $(POETRY_BIN)

# === Virtual Environment ===
venv:
ifeq ($(CI),true)
	@echo "📦 Skipping venv creation in CI..."
else
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "📦 Creating virtual environment in $(VENV_PATH)..."; \
		python3 -m venv $(VENV_PATH); \
		$(VENV_PATH)/bin/pip install --quiet --upgrade pip; \
		echo "✅ Virtual environment created!"; \
	fi
endif

# === Poetry Installation ===
poetry: venv
ifeq ($(CI),true)
	@echo "🚀 Skipping Poetry install in CI (using system Poetry)..."
else
	@if [ ! -f "$(POETRY_BIN)" ]; then \
		echo "🚀 Installing Poetry inside the virtual environment..."; \
		$(VENV_PATH)/bin/pip install --quiet poetry; \
		echo "✅ Poetry installed successfully in $(VENV_PATH)!"; \
	fi
endif

# === Dependency Installation ===
install: poetry
	@echo "📦 Installing dependencies using Poetry..."
	@$(INSTALL_CMD)

# === Add Dependencies ===
add-deps:
	@if [ -z "$(group)" ] || [ -z "$(deps)" ]; then \
		echo "❌ Usage: make add-deps group=<group-name> deps='<package1> <package2>'"; \
		exit 1; \
	fi
	@echo "🔄 Adding dependencies to group '$(group)': $(deps)"
	@$(RUN_POETRY) add --group $(group) $(deps)
	@echo "✅ Dependencies added successfully!"

add-prod-deps:
	@if [ -z "$(deps)" ]; then \
		echo "❌ Usage: make add-prod-deps deps='<package1> <package2>'"; \
		exit 1; \
	fi
	@echo "🔄 Adding production dependencies: $(deps)"
	@$(RUN_POETRY) add $(deps)
	@echo "✅ Dependencies added successfully!"

# === Formatting ===
format:
	@echo "🎨 Auto-formatting code..."
	@$(RUN) isort -l79 --profile black .
	@$(RUN) black -l79 .
	@echo "✅ Formatting complete!"

# === Pre-commit Hooks ===
precommit:
	@echo "🔍 Running pre-commit hooks (checks only)..."
	@$(RUN) pre-commit run --all-files --show-diff-on-failure
	@echo "✅ Pre-commit checks completed!"

# === Tests ===
test:
	@echo "🧪 Running tests..."
	@COVERAGE_FILE=/tmp/.coverage $(RUN) pytest --cov=src \
		--cov-report=html \
		--cov-report=term \
		--cov-report=json:coverage.json \
		-n auto -vv tests/
	@echo "📊 Generating coverage badge..."
	@COVERAGE_FILE=/tmp/.coverage $(RUN) coverage-badge -o coverage.svg -f
	@cp coverage.svg docs/source/_static/.
	@echo "✅ Tests completed, coverage report saved as coverage.json!"

# === Documentation ===
docs:
	@echo "📖 Building documentation..."
	@$(RUN) sphinx-build -E -W -b html docs/source docs/build/html
	@echo "✅ Documentation built!"

# === Check Everything ===
check: install format precommit test docs
	@echo "✅ All checks passed!"

# === CI Workflow ===
ci: install precommit test docs
	@echo "✅ CI checks completed!"

# === Cleanup ===
clean:
	@echo "🗑 Removing virtual environment and caches..."
	@rm -rf $(VENV_PATH) $(POETRY_HOME) $(POETRY_CONFIG_DIR) $(PYTHONPYCACHEPREFIX)
	@echo "✅ Cleaned up!"

# === Debug Target ===
debug:
	@echo "🧠 Debug info:"
	@echo "  VENV_PATH: $(VENV_PATH)"
	@echo "  POETRY_BIN: $(POETRY_BIN)"
	@echo "  POETRY_HOME: $(POETRY_HOME)"
	@echo "  POETRY_CONFIG_DIR: $(POETRY_CONFIG_DIR)"
	@echo "  POETRY_CACHE_DIR: $(POETRY_CACHE_DIR)"
	@echo "  POETRY_VIRTUALENVS_PATH: $(POETRY_VIRTUALENVS_PATH)"
	@echo "  PYTHONPYCACHEPREFIX: $(PYTHONPYCACHEPREFIX)"
	@echo "  PRE_COMMIT_HOME: $(PRE_COMMIT_HOME)"
	@echo "  RUN: $(RUN)"
	@echo "  RUN_POETRY: $(RUN_POETRY)"
	@echo "  INSTALL_CMD: $(INSTALL_CMD)"
