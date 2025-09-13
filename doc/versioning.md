# Система версионирования Easy Lessons Bot

## Обзор

Проект использует автоматическую систему версионирования с поддержкой:
- Автоматического обновления версии при коммитах
- Создания тегов и релизов
- CI/CD интеграции
- Docker образов с метаданными версии

## Компоненты системы

### 1. Скрипты версионирования

- **`scripts/bump_version.py`** - основной скрипт для обновления версии
- **`scripts/health_check.py`** - health check с информацией о версии
- **`core/version_info.py`** - утилиты для получения информации о версии

### 2. Git Hooks

- **`.git/hooks/pre-commit`** - автоматически обновляет patch версию при изменениях в коде
- **`.git/hooks/commit-msg`** - создает minor/major версии на основе сообщения коммита

### 3. GitHub Actions

- **`.github/workflows/ci.yml`** - CI/CD с тестированием
- **`.github/workflows/release.yml`** - создание релизов
- **`.github/workflows/version-bump.yml`** - автоматическое создание тегов

## Использование

### Ручное управление версиями

```bash
# Обновить patch версию (0.1.0 -> 0.1.1)
make bump-patch

# Обновить minor версию (0.1.0 -> 0.2.0)
make bump-minor

# Обновить major версию (0.1.0 -> 1.0.0)
make bump-major

# Создать тег для текущей версии
make create-tag

# Создать полный релиз (bump + tag + push)
make release
```

### Автоматическое версионирование

#### Pre-commit hook
Автоматически обновляет patch версию при коммитах с изменениями в исходном коде:

```bash
# Обычный коммит - автоматически обновит patch версию
git add .
git commit -m "fix: исправлена ошибка в обработке сообщений"
# Версия автоматически обновится с 0.1.0 до 0.1.1
```

#### Commit-msg hook
Создает minor/major версии на основе сообщения коммита:

```bash
# Minor версия для новой функциональности
git commit -m "feat: добавлена команда /version"
# Версия обновится с 0.1.0 до 0.2.0

# Major версия для breaking changes
git commit -m "feat!: изменен API бота"
# Версия обновится с 0.1.0 до 1.0.0
```

### CI/CD интеграция

#### Автоматические релизы
При создании тега автоматически создается релиз:

```bash
# Создать тег
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions автоматически:
# 1. Запустит тесты
# 2. Соберет Docker образ
# 3. Создаст GitHub Release
```

#### Ручное создание релиза
Через GitHub Actions можно создать релиз вручную:

1. Перейти в Actions -> Release
2. Нажать "Run workflow"
3. Указать версию (например, 1.0.0)
4. Workflow создаст релиз автоматически

## Docker образы

### Метаданные версии
Docker образы содержат метаданные версии:

```bash
# Собрать образ с метаданными
make docker-build-version

# Проверить метаданные
docker inspect easy-lessons-bot:0.1.0 | grep -A 10 "Labels"
```

### Health Check
Образы содержат health check с информацией о версии:

```bash
# Запустить health check
docker run --rm -e TELEGRAM_BOT_TOKEN=test -e OPENROUTER_API_KEY=test \
  easy-lessons-bot:0.1.0 python scripts/health_check.py
```

## Telegram команды

### Команда /version
Пользователи могут получить информацию о версии бота:

```
/version
```

Ответ:
```
🤖 Easy Lessons Bot

📊 Информация о версии:
version=0.1.0, commit=d34885e, branch=main, python=3.12.11
```

## Логирование

### Информация о версии в логах
При запуске бота в логах отображается информация о версии:

```
2025-09-13 18:18:04,255 INFO __main__ - Bot info: version=0.1.0, commit=d34885e, branch=main, python=3.12.11
```

### Health Check логи
Health check показывает версию и статус системы:

```
Health check passed: version=0.1.0, commit=d34885e, branch=main, python=3.12.11, Database OK
```

## Конвенции

### Сообщения коммитов
Используйте конвенции Conventional Commits:

- `feat:` - новая функциональность (minor версия)
- `fix:` - исправление ошибок (patch версия)
- `feat!:` или `BREAKING CHANGE:` - breaking changes (major версия)
- `docs:`, `style:`, `refactor:`, `test:`, `chore:` - patch версия

### Теги
Теги создаются автоматически в формате `v{version}`:
- `v0.1.0` - patch версия
- `v0.2.0` - minor версия  
- `v1.0.0` - major версия

## Troubleshooting

### Проблемы с git hooks
Если hooks не работают:

```bash
# Проверить права доступа
ls -la .git/hooks/

# Установить права
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg
```

### Проблемы с версией в Docker
Если версия не отображается в Docker образе:

```bash
# Пересобрать образ
make docker-build-version

# Проверить метаданные
docker inspect easy-lessons-bot:latest | grep -A 10 "Labels"
```

### Проблемы с CI/CD
Если GitHub Actions не запускаются:

1. Проверить права доступа к репозиторию
2. Убедиться, что workflows находятся в `.github/workflows/`
3. Проверить синтаксис YAML файлов

