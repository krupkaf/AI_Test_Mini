# syntax=docker/dockerfile:1

FROM python:3.11-slim

# Nastavení prostředí
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instalace uv pro rychlou správu závislostí
RUN pip install --no-cache-dir uv

# Pracovní adresář
WORKDIR /app

# Kopírování souborů pro závislosti
COPY pyproject.toml ./

# Instalace závislostí do virtualenv (pro kompatibilitu s uv run)
RUN uv sync --no-dev

# Kopírování zdrojového kódu
COPY app.py config.py graph.py state.py tools.py ./
COPY abra_mcp/ ./abra_mcp/
COPY chainlit.md ./

# Port pro Chainlit
EXPOSE 8000

# Spuštění aplikace
CMD ["uv", "run", "chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
