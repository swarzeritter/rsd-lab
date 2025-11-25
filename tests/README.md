# Тестування API

Для тестування використовується [Hurl](https://hurl.dev/).

## Встановлення Hurl

### Windows
Завантажте з [офіційного сайту](https://hurl.dev/docs/installation.html) або через Chocolatey:
```bash
choco install hurl
```

### Linux/Mac
```bash
curl -sSL https://install.hurl.dev | bash
```

## Запуск тестів

1. Переконайтеся, що сервер запущений:
```bash
uvicorn main:app --reload
```

2. Запустіть тести:
```bash
hurl --test tests/ --variables-file tests/variables.properties
```

Або якщо файл змінних називається інакше:
```bash
hurl --test tests/ --variable base_url=http://localhost:8000
```

## Структура тестів

Тести знаходяться в директорії `tests/` та використовують формат Hurl.

