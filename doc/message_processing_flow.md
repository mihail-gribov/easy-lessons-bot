# Схема преобразования входящего сообщения в выходящее

## Обзор архитектуры

Easy Lessons Bot использует двухмодельную архитектуру для обработки сообщений:
1. **Вспомогательная модель** - анализирует контекст и определяет сценарий
2. **Диалоговая модель** - генерирует финальный ответ

## Диаграмма потока обработки сообщений

```mermaid
flowchart TD
    A[Incoming Message] --> B{Message Type}
    
    B -->|Text| C[handle_text_message]
    B -->|Voice| D[handle_voice_message]
    B -->|Photo| E[handle_photo_message]
    B -->|Document| F[handle_document_message]
    
    C --> G["UnifiedMessageProcessor<br/>Main Processing Coordinator"]
    D --> G
    E --> G
    F --> G
    
    G --> H{Media Type}
    
    H -->|Text| I[Text Processing]
    H -->|Voice| J[Transcription via Whisper API]
    H -->|Image| K["Vision API Analysis"]
    
    I --> L[Add to Session History]
    J --> L
    K --> L
    
    L --> M["ContextAnalyzer<br/>Auxiliary Model Context Analysis"]
    M --> N["Context Processor<br/>Merge with Current Context"]
    N --> O["DialogBuilder<br/>Prepare Data for Dialog Model"]
    
    O --> P["Load Prompts Based on Scenario"]
    PS[PromptStorage] --> P
    P --> Q["Base Prompt + Dynamic Context + Scenario Prompt"]
    Q --> R["Dialog Model<br/>Generate Response"]
    
    R --> S{Success?}
    S -->|Yes| T[Add Response to History]
    S -->|No| U[Graceful Degradation]
    
    T --> V[Save Session to DB]
    U --> V
    
    V --> W[Format for Telegram]
    W --> X[Send Response to User]
    
    %% Model connections
    WHISPER[Whisper Model] --> J
    VISION[GPT-4 Vision Model] --> K
    AUX_MODEL[Auxiliary LLM Model] --> M
    DIALOG_MODEL[Dialog LLM Model] --> R
    
    style A fill:#e3f2fd
    style X fill:#e3f2fd
    style G fill:#e8f5e8
    style N fill:#e8f5e8
    style O fill:#e8f5e8
    style I fill:#e8f5e8
    style M fill:#fff3e0
    style R fill:#fff3e0
    style K fill:#fff3e0
    style J fill:#fff3e0
    style L fill:#f3e5f5
    style P fill:#f3e5f5
    style PS fill:#f3e5f5
    style T fill:#f3e5f5
    style V fill:#f3e5f5
    style U fill:#ffebee
    style WHISPER fill:#fff3e0
    style VISION fill:#fff3e0
    style AUX_MODEL fill:#fff3e0
    style DIALOG_MODEL fill:#fff3e0
```

## Детальная схема загрузки промптов

```mermaid
flowchart TD
    A[DialogBuilder.build_dialog_context] --> B[Get Scenario from Dynamic Context]
    B --> C{Scenario Type}
    
    C -->|discussion| D[Load system_discussion.txt]
    C -->|explanation| E[Load system_explanation.txt]
    C -->|unknown| F[Load system_unknown.txt]
    C -->|image_analysis| G[Load system_image_analysis.txt]
    
    D --> H[PromptLoader.get_scenario_prompt]
    E --> H
    F --> H
    G --> H
    
    H --> I[Load Base Prompt]
    I --> J[Load system_base.txt]
    J --> K[Load Understanding Level Prompt]
    
    K --> L{Understanding Level}
    L -->|0-2| M[Load understanding_low.txt]
    L -->|3-6| N[Load understanding_medium.txt]
    L -->|7-9| O[Load understanding_high.txt]
    
    M --> P[Combine All Prompts]
    N --> P
    O --> P
    
    P --> Q["Final System Prompt:<br/>Base + Dynamic Context + Scenario + Understanding"]
    Q --> R[Send to Dialog Model]
    
    style A fill:#e8f5e8
    style H fill:#f3e5f5
    style P fill:#fff3e0
    style Q fill:#c8e6c9
```

## Детальная схема компонентов

```mermaid
graph LR
    subgraph "Input Layer"
        A[Telegram API] --> B[aiogram handlers]
        B --> C[UnifiedMessageProcessor]
    end
    
    subgraph "Media Processing"
        C --> D[MediaProcessor]
        D --> E[AudioHandler]
        D --> F[ImageAnalyzer]
        E --> G[Whisper API]
        F --> H[Vision API]
    end
    
    subgraph "State Management"
        C --> I[SessionManager]
        I --> J[SessionState]
        I --> K[PersistenceAdapter]
        K --> L[SQLite Database]
    end
    
    subgraph "Two-Model Architecture"
        C --> M[PromptStore]
        M --> N[ContextAnalyzer]
        N --> O[Auxiliary Model]
        O --> P[Context Processor]
        P --> Q[DialogBuilder]
        Q --> R[PromptLoader]
        R --> S[Dialog Model]
    end
    
    subgraph "Prompt Files"
        R --> T[system_base.txt]
        R --> U[system_discussion.txt]
        R --> V[system_explanation.txt]
        R --> W[system_unknown.txt]
        R --> X[understanding_*.txt]
    end
    
    subgraph "Formatting & Output"
        S --> Y[TelegramFormatter]
        Y --> Z[MathConverter]
        Y --> AA[EducationalTemplates]
        Y --> BB[HTML Formatting]
        BB --> CC[Send to Telegram]
    end
    
    style O fill:#fff3e0
    style S fill:#fff3e0
    style L fill:#f3e5f5
    style CC fill:#c8e6c9
    style R fill:#e8f5e8
```

## Последовательность обработки

```mermaid
sequenceDiagram
    participant U as User
    participant TG as Telegram API
    participant H as Handlers
    participant MP as MessageProcessor
    participant SM as SessionManager
    participant PS as PromptStore
    participant CA as ContextAnalyzer
    participant CP as ContextProcessor
    participant DB as DialogBuilder
    participant PL as PromptLoader
    participant LLM as LLM Client
    participant TF as TelegramFormatter
    
    U->>TG: Message (text/voice/photo)
    TG->>H: Update
    H->>MP: process_message()
    
    MP->>SM: get_session(chat_id)
    SM-->>MP: SessionState
    
    alt Media Message
        MP->>MP: _extract_media_content()
        MP->>LLM: Transcription/Analysis
        LLM-->>MP: Extracted Content
    end
    
    MP->>SM: add_message("user", content)
    
    MP->>PS: analyze_context_with_auxiliary_model()
    PS->>CA: analyze_context_with_auxiliary_model()
    CA->>LLM: Context Analysis
    LLM-->>CA: Analysis Result
    CA-->>PS: Context
    PS-->>MP: Context
    
    MP->>CP: process_aux_result()
    CP-->>MP: Dynamic Context
    
    MP->>PS: build_dialog_context()
    PS->>DB: build_dialog_context()
    DB->>PL: get_scenario_prompt(scenario)
    PL-->>DB: Scenario Prompt
    DB->>PL: get_system_prompt("system_base")
    PL-->>DB: Base Prompt
    DB->>PL: get_system_prompt("understanding_level")
    PL-->>DB: Understanding Prompt
    DB-->>PS: Combined Messages
    PS-->>MP: Messages
    
    MP->>LLM: generate_response()
    LLM-->>MP: Response
    
    MP->>SM: add_message("assistant", response)
    MP->>SM: save_session()
    
    MP->>TF: format_message()
    TF-->>MP: Formatted Text
    
    MP-->>H: Response
    H->>TG: send_message()
    TG-->>U: Response
```

## Ключевые компоненты

### 1. UnifiedMessageProcessor
- **Назначение**: Единая точка обработки всех типов сообщений
- **Функции**:
  - Извлечение контента из медиа-файлов
  - Координация двухмодельной архитектуры
  - Обработка ошибок и graceful degradation

### 2. SessionManager
- **Назначение**: Управление состоянием пользователей
- **Функции**:
  - Загрузка/сохранение сессий из SQLite
  - In-memory кеширование
  - Graceful degradation при недоступности БД

### 3. ContextAnalyzer
- **Назначение**: Анализ контекста вспомогательной моделью
- **Функции**:
  - Определение сценария (discussion/explanation/unknown)
  - Выявление темы и вопроса
  - Оценка уровня понимания (0-9)

### 4. ContextProcessor
- **Назначение**: Обработка результатов вспомогательной модели
- **Функции**:
  - Объединение с состоянием сессии
  - Определение новых тем/вопросов
  - Генерация рекомендаций

### 5. DialogBuilder
- **Назначение**: Построение контекста для диалоговой модели
- **Функции**:
  - Сборка системного промпта
  - Формирование истории диалога
  - Применение сценариев

### 6. PromptLoader
- **Назначение**: Загрузка промптов из файлов
- **Функции**:
  - Загрузка базовых промптов (`system_base.txt`)
  - Загрузка промптов сценариев (`system_discussion.txt`, `system_explanation.txt`, `system_unknown.txt`)
  - Загрузка промптов уровня понимания (`understanding_low.txt`, `understanding_medium.txt`, `understanding_high.txt`)
  - Кеширование загруженных промптов

### 7. TelegramFormatter
- **Назначение**: Форматирование ответов для Telegram
- **Функции**:
  - Конвертация математических выражений
  - Применение образовательных шаблонов
  - HTML форматирование

## Загрузка промптов по сценариям

### Момент загрузки:
Промпты загружаются в **DialogBuilder** на этапе подготовки данных для диалоговой модели, **после** определения сценария вспомогательной моделью.

### Структура промптов:
1. **Базовый промпт** (`system_base.txt`) - основные принципы работы
2. **Динамический контекст** - текущая тема, сценарий, уровень понимания
3. **Промпт сценария** - зависит от определенного сценария:
   - `system_discussion.txt` - для обсуждения темы
   - `system_explanation.txt` - для разъяснения вопроса
   - `system_unknown.txt` - для свободного общения
   - `system_image_analysis.txt` - для анализа изображений
4. **Промпт уровня понимания** - зависит от уровня (0-9):
   - `understanding_low.txt` - для уровней 0-2
   - `understanding_medium.txt` - для уровней 3-6
   - `understanding_high.txt` - для уровней 7-9

### Итоговый системный промпт:
```
[Базовый промпт]

[Динамический контекст]

[Промпт сценария]

[Промпт уровня понимания]
```

## Типы сообщений и их обработка

### Текстовые сообщения
1. Прямое использование текста
2. Анализ контекста вспомогательной моделью
3. Генерация ответа диалоговой моделью

### Голосовые сообщения
1. Скачивание аудио-файла из Telegram
2. Транскрипция через Whisper API
3. Анализ намерения из транскрипта
4. Передача в основной пайплайн как текст

### Изображения
1. Скачивание изображения из Telegram
2. Анализ через GPT-4 Vision API
3. Извлечение текста и определение типа контента
4. Генерация образовательного ответа

## Сценарии работы

### 1. Discussion (Обсуждение темы)
- **Триггер**: Новая тема или общее обсуждение
- **Поведение**: Объяснение темы с учетом уровня понимания
- **Промпт**: `system_discussion.txt`

### 2. Explanation (Разъяснение вопроса)
- **Триггер**: Конкретный вопрос
- **Поведение**: Детальное разъяснение с примерами
- **Промпт**: `system_explanation.txt`

### 3. Unknown (Неизвестный)
- **Триггер**: Свободное общение
- **Поведение**: Дружелюбная поддержка, наводки на учебные темы
- **Промпт**: `system_unknown.txt`

### 4. Image Analysis (Анализ изображений)
- **Триггер**: Отправка фото/изображения
- **Поведение**: Анализ контента и образовательный ответ
- **Промпт**: `system_image_analysis.txt`

## Обработка ошибок

### Graceful Degradation
- При недоступности LLM: использование предустановленных ответов
- При недоступности БД: работа в in-memory режиме
- При ошибках медиа-обработки: fallback на текстовый режим
- При ошибках загрузки промптов: использование встроенных fallback промптов

### Retry Logic
- 1 повтор для сетевых ошибок
- Экспоненциальная задержка (0.5s → 1.0s)
- Таймаут 30 секунд

## Персистентность данных

### SQLite Database
- **Sessions**: Состояние пользователей
- **Messages**: История диалогов
- **Migrations**: Версионирование схемы

### Graceful Degradation
- При недоступности БД: работа в памяти
- Автоматическое восстановление при доступности БД
- Миграции при старте приложения

## Конфигурация

### Переменные окружения
- `TELEGRAM_BOT_TOKEN`: Токен бота
- `OPENROUTER_API_KEY`: API ключ для LLM
- `OPENROUTER_MODEL`: Модель по умолчанию (gpt-4o-mini)
- `DATABASE_ENABLED`: Включение БД
- `AUDIO_ENABLED`: Включение обработки аудио
- `IMAGE_ANALYSIS_ENABLED`: Включение анализа изображений

### Настройки форматирования
- `ENABLE_HTML_FORMATTING`: HTML форматирование
- `USE_MATHEMATICAL_UNICODE`: Математические символы
- `USE_EDUCATIONAL_EMOJIS`: Образовательные эмодзи