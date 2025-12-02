# Contributing to tail-lookup

Thank you for your interest in contributing!

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ryakel/tail-lookup.git
   cd tail-lookup
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Build the database**
   ```bash
   python scripts/update_faa_data.py data/aircraft.db
   ```

4. **Run the development server**
   ```bash
   DB_PATH=data/aircraft.db uvicorn app.main:app --reload --port 8080
   ```

5. **Test your changes**
   - Web UI: http://localhost:8080
   - API docs: http://localhost:8080/docs
   - Health check: http://localhost:8080/api/v1/health

## Commit Message Convention

We use Angular commit message format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Example: `feat: add bulk lookup endpoint`

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit with meaningful messages
6. Push to your fork
7. Open a Pull Request

### PR Checklist

- [ ] Code follows project style
- [ ] Tests pass (if applicable)
- [ ] Documentation updated (if needed)
- [ ] Commit messages follow convention
- [ ] No breaking changes (or clearly documented)

## Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Keep functions focused and well-named
- Add docstrings for public APIs

## Questions?

Feel free to open a discussion or reach out via GitHub issues!
