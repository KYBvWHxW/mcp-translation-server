# Contributing to MCP Translation Server

## Welcome!

Thank you for considering contributing to the MCP Translation Server! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/mcp-translation-server.git
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

## Development Process

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Run tests:
   ```bash
   python -m pytest tests/
   ```

4. Run linting:
   ```bash
   flake8 .
   black .
   ```

5. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

## Commit Message Guidelines

We follow the Conventional Commits specification:

- feat: A new feature
- fix: A bug fix
- docs: Documentation changes
- style: Code style changes (formatting, etc)
- refactor: Code refactoring
- test: Adding or modifying tests
- chore: Maintenance tasks

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the documentation if you're changing functionality
3. Add tests for your changes
4. Ensure all tests pass
5. Submit your pull request

## Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for functions and classes
- Keep functions focused and small
- Add comments for complex logic

## Testing

- Write unit tests for new features
- Include integration tests where appropriate
- Ensure all tests pass before submitting PR
- Aim for good test coverage

## Documentation

- Update API documentation for new endpoints
- Add usage examples for new features
- Keep README.md up to date
- Document any new dependencies

## Questions or Problems?

- Open an issue for bugs
- Use discussions for questions
- Join our community chat for real-time help

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms.
