# Contributing to Unreal Miner

Thank you for your interest in contributing to Unreal Miner! This document provides guidelines for contributing to the project.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/Unreal-Miner.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Commit and push
7. Open a Pull Request

## Development Setup

### Prerequisites
- Python 3.9+
- SNAP Toolbox with gpt CLI
- GDAL 3.0+

### Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Coding Standards

### Python Code Style
- Follow PEP 8
- Use Black for formatting: `black scripts/`
- Use isort for imports: `isort scripts/`
- Max line length: 100 characters

### Running Linters
```bash
black scripts/ tests/
isort scripts/ tests/
flake8 scripts/ tests/
```

### Type Hints
Use type hints where appropriate:
```python
def process_raster(path: Path, band: int = 1) -> np.ndarray:
    ...
```

## Testing

### Run Tests
```bash
pytest tests/
```

### Test Coverage
```bash
pytest --cov=scripts tests/
```

### Write Tests
- Unit tests for all Python functions
- Integration tests for pipeline stages
- Place tests in `tests/` directory

## Branch Naming

- `feature/<short-description>`: New features
- `fix/<issue-id>-<description>`: Bug fixes
- `docs/<description>`: Documentation updates
- `refactor/<description>`: Code refactoring

## Commit Messages

Use conventional commit format:
```
type(scope): short description

Longer description if needed

Fixes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] CHANGELOG.md updated

### PR Template

When opening a PR, include:
- Description of changes
- Motivation and context
- Related issue numbers
- Screenshots (if applicable)
- Test results

## Issue Reporting

### Bug Reports

Include:
- OS and Python version
- SNAP and GDAL versions
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs
- Sample data (if possible)

### Feature Requests

Include:
- Clear description
- Use case / motivation
- Proposed implementation (optional)
- Alternative solutions considered

## Documentation

- Update relevant `.md` files in `docs/`
- Add docstrings to all functions
- Include examples in docstrings
- Update README.md if needed

## Data Policy

- **Never commit large files** (>10 MB)
- Use sample data in `data/sample_tile/`
- Include download scripts instead of data
- Add large files to `.gitignore`

## Contact

Questions? Open an issue or contact maintainers.

Thank you for contributing! 🎉
