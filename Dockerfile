# Используем официальный легкий образ Python
FROM python:3.13-slim

# Копируем бинарник uv из официального образа Astral
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Устанавливаем рабочую директорию
WORKDIR /app

# 1. Сначала копируем ТОЛЬКО файлы зависимостей (для эффективного кэширования слоев Docker)
COPY pyproject.toml uv.lock ./

# 2. Устанавливаем зависимости строго по uv.lock (без установки самого текущего проекта)
RUN uv sync --frozen --no-install-project --no-dev

# 3. Копируем исходный код проекта
COPY . .

# 4. Финальная синхронизация проекта
RUN uv sync --frozen --no-dev

# Добавляем .venv в PATH, чтобы не писать каждый раз `uv run`
ENV PATH="/app/.venv/bin:$PATH"
