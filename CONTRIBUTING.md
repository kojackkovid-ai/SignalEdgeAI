# Contribution Guidelines

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Write/update tests
5. Run linting and tests locally
6. Commit: `git commit -m 'Add amazing feature'`
7. Push: `git push origin feature/amazing-feature`
8. Open a Pull Request

## Code Standards

### Python (Backend)
- PEP 8 compliance (use Black formatter)
- Type hints required
- Async/await for I/O operations
- Comprehensive docstrings

```bash
# Format code
black backend/app

# Check code
flake8 backend/app
mypy backend/app
```

### TypeScript/React (Frontend)
- ESLint compliance
- TypeScript strict mode
- Component documentation
- Proper error handling

```bash
# Format code
cd frontend
npm run lint

# Fix issues
npm run lint -- --fix
```

## Testing Requirements

- Backend: Minimum 80% code coverage
- Frontend: Unit tests for components and utilities
- Integration tests for critical paths

```bash
# Run tests
npm test              # Frontend
pytest tests/ -v      # Backend
```

## Commit Messages

Use conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring

Example:
```
feat(api): add prediction filtering by sport

- Add sport parameter to predictions endpoint
- Update prediction service with filter logic
- Add tests for sport filtering
```

## Pull Request Process

1. Update README.md with changes if needed
2. Update docs if behavior changed
3. Ensure CI/CD passes
4. Request review from maintainers
5. Address review feedback
6. Squash commits if requested

## Development Workflow

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start services
docker-compose up -d

# 4. Run migrations
python -m alembic upgrade head

# 5. Start development servers
npm run dev  # Frontend
python -m uvicorn app.main:app --reload  # Backend

# 6. Run tests
pytest tests/
npm test
```

## Documentation

- Update docstrings for new functions
- Add inline comments for complex logic
- Update ARCHITECTURE.md for structural changes
- Update ML_MODELS.md for model changes

## Reporting Issues

When reporting bugs, include:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Python version, Node version)
- Error logs/screenshots

## Feature Requests

For feature requests:
- Clear use case
- Proposed implementation (if possible)
- Acceptance criteria
- Performance considerations

## Questions?

- Check existing issues/PRs
- Review documentation
- Open a discussion
