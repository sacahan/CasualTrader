---
description: "Python development standards and best practices"
applyTo: "**/*.py"
---

# Guidelines for Python

## SUPPORT_EXPERT

- Favor elegant, maintainable solutions over verbose code.
  Assume understanding of language idioms and design patterns.
- Highlight potential performance implications and optimization opportunities.
- Frame solutions within broader architectural contexts and suggest design alternatives.
- Focus comments on 'why' not 'what'—assume code readability through well-named functions and variables.
- Proactively address edge cases, race conditions, and security considerations.
- When debugging, provide targeted diagnostic approaches.
- Suggest comprehensive testing strategies, including mocking, test organization, and coverage.
- Always apply the latest version of Python best practices and PEP standards, like PEP 8, PEP 20, PEP 257, Python 3.12 above etc.

---

## SWAGGER

- Define comprehensive schemas for all request and response objects.
- Use semantic versioning in API paths for backward compatibility.
- Implement detailed descriptions for endpoints, parameters, and {{domain_specific_concepts}}.
- Configure security schemes for authentication and authorization requirements.
- Use tags to group related endpoints by resource or functional area.
- Implement examples for all endpoints to facilitate integration.

---

## FASTAPI

- Use Pydantic models for request/response validation with strict type checking and custom validators.
- Implement dependency injection for services and database sessions.
- Use async endpoints for I/O-bound operations, especially for {{high_load_endpoints}}.
- Leverage FastAPI's background tasks for non-critical operations.
- Implement proper exception handling with HTTPException and custom handlers for {{error_scenarios}}.
- Use path operation decorators consistently with appropriate HTTP methods.

---

## TEST & DEBUG

- Use fixtures for test setup and dependency injection.
- Implement parameterized tests for {{function_types}}.
- Use monkeypatch for mocking dependencies.
- Prefer using logger instead of print for logging.

---

## PLAYWRIGHT

- Initialize configuration only with Chromium/Desktop Chrome browser.
- Use browser contexts for isolating test environments.
- Implement the Page Object Model for maintainable tests.
- Use locators for resilient element selection.
- Leverage API testing for backend validation.
- Implement visual comparison with expect(page).toHaveScreenshot().
- Use the codegen tool for test recording.
- Leverage trace viewer for debugging test failures.
- Implement test hooks for setup and teardown.
- Use expect assertions with specific matchers.
- Leverage parallel execution for faster test runs.

## Package Management

- Use `pyproject.toml` for Python dependency management.
- Use `uv` (An extremely fast Python package and project manager, written in Rust.) as package manager (replacing pip).
  - uv init: Create a new Python project.
  - uv venv: Create a new virtual environment.
  - uv add: Add a dependency to the project.
  - uv remove: Remove a dependency from the project.
  - uv sync: Sync the project's dependencies with the environment.
  - uv lock: Create a lockfile for the project's dependencies.
  - uv run: Run a command in the project environment.
  - uv build: Build the project into distribution archives.
- Make sure to use `uv` to manage my Python environment and dependencies.
- Pin dependencies to specific versions to ensure reproducibility.
- Use virtual environments (e.g., `venv`) to isolate project dependencies.
- Regularly update dependencies and test for compatibility.
- Document dependency management practices in the project README.
