# Contributing to Race Analytics

Thank you for your interest in contributing! This document provides guidelines and instructions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/race-analytics.git
   cd race-analytics
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Setup development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install pytest black flake8 mypy  # Development tools
   ```

## Development Workflow

### Code Style

- Follow **PEP 8** Python style guide
- Use **Type hints** for function signatures
- Maximum line length: **88 characters** (Black formatter)
- Write **docstrings** for all public functions/classes

Example:
```python
def build_race_facts(
    race_name: str,
    track_name: str,
    telemetry_clean: pd.DataFrame,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Build enriched race facts JSON from telemetry and metrics.
    
    Args:
        race_name: Name of the race event
        track_name: Name of the track/venue
        telemetry_clean: Normalized telemetry DataFrame
        **kwargs: Additional optional data sources
        
    Returns:
        Dictionary containing enriched race data with drivers, events, laps
        
    Raises:
        ValueError: If required columns are missing from telemetry
        
    Example:
        >>> race_facts = build_race_facts(
        ...     "Race 1", "Road America", telemetry_df, per_lap=per_lap_df
        ... )
        >>> len(race_facts['drivers']) > 0
        True
    """
```

### Code Quality

**Format code with Black:**
```bash
black src/ --line-length 88
```

**Check for style issues:**
```bash
flake8 src/ --max-line-length 88
```

**Type checking:**
```bash
mypy src/ --ignore-missing-imports
```

### Testing

**Run tests:**
```bash
pytest tests/ -v
```

**Run tests with coverage:**
```bash
pytest tests/ --cov=src --cov-report=html
```

**Add new tests for features:**
```python
# tests/test_new_feature.py
def test_new_feature():
    """Test description."""
    result = new_function(test_input)
    assert result == expected_output

def test_edge_case():
    """Test edge case handling."""
    with pytest.raises(ValueError):
        new_function(invalid_input)
```

## Making Changes

### File Organization

**Source Code:** `src/race_engine/`
```
src/race_engine/
├── analysis_engine.py      # Core race analysis
├── sector_analysis.py       # Track section analysis
├── what_if.py              # Scenario simulation
├── llm/
│   └── ollama.py           # LLM integration
└── processing/
    ├── lap_processing.py   # Lap metrics
    ├── event_detection.py  # Incident detection
    └── converter.py        # Data conversion
```

**Examples:** Root level scripts
```
examples_complete_workflow.py   # End-to-end demo
race_analytics_pipeline.py      # Main pipeline
race_llm_analyzer.py            # LLM integration
```

### Naming Conventions

- **Functions/variables:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private methods:** `_leading_underscore`

### Commits

Write clear, descriptive commit messages:

```
git commit -m "feat: Add sector-by-sector consistency analysis

- Analyze lap time variance within each sector
- Generate consistency metrics per driver
- Add visualization for sector consistency patterns

Fixes #42"
```

**Commit message format:**
- Type: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Subject: Imperative, lowercase, <50 characters
- Body: Explain what and why (not how), wrap at 72 characters

## Pull Requests

1. **Before submitting:**
   - Run all tests: `pytest tests/`
   - Format code: `black src/`
   - Check types: `mypy src/`
   - Update documentation if needed

2. **PR Description:**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   - [ ] Unit tests added
   - [ ] Integration tests added
   - [ ] Manual testing completed
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex logic
   - [ ] Documentation updated
   - [ ] No new warnings generated
   ```

3. **Link to issue:** Include `Closes #123` or `Fixes #123` in PR description

## Reporting Issues

**Bug Report Template:**
```markdown
## Description
Clear, concise description of the issue

## Steps to Reproduce
1. Step one
2. Step two
3. Expected behavior vs actual behavior

## Environment
- Python version
- OS (Windows/Mac/Linux)
- Relevant versions

## Logs/Error Messages
```
Include full error trace
```
```

**Feature Request Template:**
```markdown
## Description
Clear description of desired feature

## Motivation
Why is this feature needed?

## Suggested Implementation
How should it work?

## Example Usage
```python
Code example
```
```

## Documentation

- Update `README.md` for user-facing changes
- Add docstrings to all public functions/classes
- Update `docs/` folder for architecture changes
- Include examples in docstrings

## Areas for Contribution

### High Priority
- [ ] Performance optimizations
- [ ] Additional LLM backend support
- [ ] Real-time analysis capabilities
- [ ] Visualization improvements

### Medium Priority
- [ ] Multi-race analysis
- [ ] Championship aggregation
- [ ] Advanced filtering options
- [ ] Data export formats

### Nice to Have
- [ ] Web dashboard
- [ ] REST API
- [ ] Docker containerization
- [ ] CI/CD pipelines

## Community Guidelines

- Be respectful and inclusive
- Welcome different perspectives
- Ask questions before major changes
- Help others in discussions
- Share knowledge and experience

## Questions?

- Open a GitHub Discussion for questions
- Check existing issues before asking
- Read documentation first
- Be specific and provide context

---

**Thank you for contributing to Race Analytics! 🏁**
