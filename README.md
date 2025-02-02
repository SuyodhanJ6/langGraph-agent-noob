# Template GenAI Project

## Setup

### Prerequisites
- Python 3.12 or higher
- pip (for installing uv)

### Initial Setup

1. Install uv:
```bash
pip install uv
```

2. Create and activate virtual environment:
```bash
uv lock
uv sync --frozen
source .venv/bin/activate
```

## Package Management

### Adding New Packages

1. Add the package to `pyproject.toml` under the `dependencies` section:
```toml
[project]
dependencies = [
    "your-new-package>=1.0.0",
]
```

2. Update the lockfile and sync:
```bash
uv lock  # Updates uv.lock with new dependencies
uv sync --frozen  # Installs packages from lockfile
```

### Development Dependencies

For development-only packages (like testing frameworks), add them to the `[project.optional-dependencies]` section:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
]
```

To install development dependencies:
```bash
uv pip install -e ".[dev]"
```

### Upgrading Packages

1. Update the version specification in `pyproject.toml`
2. Run:
```bash
uv lock
uv sync --frozen
```

### View Installed Packages
```bash
uv pip list
```

## Project Structure
```
template_genai/
├── .venv/                 # Virtual environment (generated)
├── pyproject.toml        # Project configuration and dependencies
├── uv.lock              # Lockfile for dependencies
├── README.md           # This file
└── src/               # Source code directory
```

## Development Guidelines

1. Always use the virtual environment when working on the project
2. Keep dependencies up to date
3. Document new dependencies in this README if they require special setup
4. Test your changes before committing

## Troubleshooting

### Common Issues

1. If `uv sync` fails:
   - Check if `uv.lock` exists
   - Try removing `uv.lock` and running `uv lock` again

2. Virtual environment issues:
   - Ensure you've activated the environment: `source .venv/bin/activate`
   - Try recreating the environment:
     ```bash
     rm -rf .venv
     uv lock
     uv sync --frozen
     ```
