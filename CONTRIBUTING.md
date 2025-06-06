# Contributing to talk2n8n

Thank you for considering contributing to talk2n8n! This document outlines the process for contributing to the project and helps to make the contribution process easy and effective for everyone involved.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Setting Up Your Development Environment](#setting-up-your-development-environment)
- [Development Workflow](#development-workflow)
  - [Code Style](#code-style)
  - [Type Hints](#type-hints)
  - [Documentation](#documentation)
  - [Testing](#testing)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)
- [Code Review Process](#code-review-process)
- [Release Process](#release-process)
- [Community](#community)

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before participating. We are committed to fostering a welcoming and inclusive environment for all contributors.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- [Poetry](https://python-poetry.org/) for dependency management
- n8n instance (self-hosted or cloud)
- Claude API key from [Anthropic](https://www.anthropic.com/)
- Slack app (if using the Slack integration)
- [pre-commit](https://pre-commit.com/) (recommended)

### Setting Up Your Development Environment

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/talk2n8n.git
cd talk2n8n
```

2. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install dependencies:
```bash
poetry install --with dev
```

4. Install pre-commit hooks:
```bash
poetry run pre-commit install
```

5. Create your .env file:
```bash
cp .env.example .env
# Edit .env with your settings
```
   poetry install --with dev,docs
   
   # Activate the virtual environment
   poetry shell
   ```
4. **Set up pre-commit hooks** (recommended):
   ```bash
   pre-commit install
   ```
5. **Configure environment variables** by creating a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Development Workflow

1. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b type/scope/description
   # Example: git checkout -b feat/workflows/add-new-trigger
   ```
   Branch types: `feat/`, `fix/`, `docs/`, `style/`, `refactor/`, `perf/`, `test/`, `chore/`

2. **Make your changes**, following our coding guidelines

3. **Add tests** for your changes

4. **Run tests and checks** before committing:
   ```bash
   ### Common Development Commands

All development commands are managed through Poetry:

```bash
# Run tests
poetry run test

# Run tests with coverage
poetry run coverage

# Format code
poetry run format

# Run linting
poetry run lint

# Build documentation
poetry run docs

# Serve documentation locally
poetry run serve-docs

# Run all pre-commit checks
poetry run check
```

You can also run Python scripts directly in the Poetry environment:

```bash
# Run a specific script
poetry run python examples/simple.py

# Start an interactive Python shell
poetry run python
```

   # Run all tests
   pytest
   
   # Run tests with coverage
   pytest --cov=src --cov-report=term-missing
   
   # Run linters and type checking
   pre-commit run --all-files
   ```

5. **Commit your changes** following the [commit guidelines](#commit-guidelines)

### Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **Flake8** for linting
- **mypy** for static type checking

Run the formatters and linters before committing:
```bash
black .
isort .
flake8
mypy .
```

### Type Hints

All new code should include type hints. We use Python's native type hints and enforce them with mypy.

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

### Documentation

- Document all public APIs using Google-style docstrings
- Update the relevant documentation in the `docs/` directory
- Add examples for new features

### Testing

- Write unit tests for new features and bug fixes
- Aim for good test coverage (minimum 80%)
- Use descriptive test names that explain the test case
- Use fixtures for common test data
- Mark slow tests with `@pytest.mark.slow`

## Commit Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. Each commit message should be structured as follows:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc.)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools and libraries

Example:
```
feat(workflows): add support for new n8n trigger

Add support for the new webhook trigger in n8n workflows. This allows users to trigger workflows
from external services.

Closes #123
```

## Pull Request Process

1. Fork the repository and create your branch from `main`
2. Make sure your code passes all tests and linters
3. Update the documentation as needed
4. Add unit or integration tests for any new or changed functionality
5. Ensure your commits are well-documented and follow the commit guidelines
6. Open a pull request with a clear description of the changes
7. Reference any related issues in the PR description
8. Wait for the CI build to complete and ensure all checks pass
9. Request review from one of the core maintainers

## Reporting Issues

When reporting issues, please include:

1. A clear, descriptive title
2. Steps to reproduce the issue
3. Expected vs. actual behavior
4. Environment details (Python version, OS, etc.)
5. Any relevant logs or error messages
6. If possible, a minimal reproducible example

## Feature Requests

We welcome feature requests! Please open an issue and:

1. Describe the feature you'd like to see
2. Explain why this feature would be valuable
3. Include any relevant use cases or examples

## Code Review Process

1. A maintainer will review your PR as soon as possible
2. The reviewer may request changes or ask questions
3. Once approved, your PR will be merged into the main branch
4. The maintainer will handle the release process

## Release Process

1. Update the version number in `pyproject.toml` following semantic versioning
2. Update the `CHANGELOG.md` with the changes in the new version
3. Create a git tag with the version number (e.g., `v1.0.0`)
4. Push the tag to trigger the release workflow
5. The CI will automatically publish the package to PyPI

## Community

- Join our [Discord/Slack channel]() for discussions
- Follow us on [Twitter]()
- Check out our [blog]() for updates and tutorials
   ```bash
   flake8
   ```

6. Commit your changes with a descriptive commit message:
   ```bash
   git commit -m "Add feature: your feature description"
   ```

7. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

8. Submit a pull request to the main repository

## Pull Request Process

1. Ensure your PR description clearly describes the problem and solution
2. Include any relevant issue numbers in the PR description
3. Update the README.md or documentation with details of changes if applicable
4. The PR must pass all CI checks before it will be merged
5. A project maintainer will review your changes and may request additional changes
6. Once approved, a maintainer will merge your PR

## Coding Guidelines

### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use 4 spaces for indentation (not tabs)
- Use meaningful variable and function names
- Add docstrings to all functions, classes, and modules
- Keep lines under 100 characters

### Logging

- Use the built-in logging module for all logging
- Keep logs concise and focused
- Use appropriate log levels:
  - `DEBUG`: Detailed information, typically useful only for diagnosing problems
  - `INFO`: Confirmation that things are working as expected
  - `WARNING`: Indication that something unexpected happened, but the application still works
  - `ERROR`: Due to a more serious problem, the application has not been able to perform a function
  - `CRITICAL`: A serious error, indicating that the application itself may be unable to continue running

### Testing

- Write tests for all new features and bug fixes
- Aim for high test coverage
- Tests should be independent and not rely on external services when possible

## Contributor License Agreement

Before your contribution can be accepted, you need to sign our Contributor License Agreement (CLA). This is a one-time process that you'll complete when you submit your first pull request. See [CLA.md](CLA.md) for more details.

## Communication

- For bugs and feature requests, please use GitHub Issues
- For general questions or discussions, use GitHub Discussions
- For security issues, please see our [Security Policy](SECURITY.md)

## Project Structure

```
talk2n8n/
├── agent/              # Agent implementation
├── n8n/                # n8n client and workflow handling
├── slack/              # Slack integration
├── tests/              # Test suite
├── docs/               # Documentation
├── config/             # Configuration files
└── main.py             # Application entry point
```

## License

By contributing to talk2n8n, you agree that your contributions will be licensed under the project's license. See [LICENSE](LICENSE) for details.
