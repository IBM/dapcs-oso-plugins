curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install commitizen detect-secrets pre-commit ruff
pre-commit install
pre-commit install --hook-type commit-msg
