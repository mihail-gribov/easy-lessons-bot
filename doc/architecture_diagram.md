# Архитектурная диаграмма Easy Lessons Bot

## Общая архитектура системы

```mermaid
graph TB
    subgraph "Внешние сервисы"
        TG[Telegram API]
        OR[OpenRouter API]
        WH[Whisper API]
        VISION[GPT-4 Vision API]
    end
    
    subgraph "Easy Lessons Bot"
        subgraph "Входной слой"
            MAIN[app/main.py]
            HANDLERS[bot/handlers.py]
            MEDIA[bot/media_handlers.py]
        end
        
        subgraph "Ядро системы"
            MP[core/message_processor.py]
            SM[core/session_state.py]
            PS[core/prompt_store.py]
            LLM[core/llm_client.py]
        end
        
        subgraph "Обработка медиа"
            MEDIAP[core/media_processor.py]
            AUDIO[core/audio_handler.py]
            IMAGE[core/image_analyzer.py]
        end
        
        subgraph "Контекст и диалог"
            CA[core/context/context_analyzer.py]
            CP[core/context_processor.py]
            DB[core/dialog/dialog_builder.py]
        end
        
        subgraph "Форматирование"
            TF[core/formatting/telegram_formatter.py]
            MC[core/formatting/math_converter.py]
            ET[core/formatting/educational_templates.py]
        end
        
        subgraph "Персистентность"
            PA[core/persistence/session_adapter.py]
            REPO[core/persistence/repositories.py]
            DB_MGR[core/persistence/database.py]
        end
        
        subgraph "Конфигурация"
            CONFIG[settings/config.py]
            DI[core/service_registry.py]
        end
        
        subgraph "Данные"
            SQLITE[(SQLite Database)]
            TEMP[data/temp/]
            LOGS[log/app.log]
        end
    end
    
    TG --> HANDLERS
    HANDLERS --> MP
    MEDIA --> MEDIAP
    
    MP --> SM
    MP --> PS
    MP --> LLM
    
    MEDIAP --> AUDIO
    MEDIAP --> IMAGE
    
    PS --> CA
    PS --> DB
    CA --> CP
    
    MP --> TF
    TF --> MC
    TF --> ET
    
    SM --> PA
    PA --> REPO
    REPO --> DB_MGR
    DB_MGR --> SQLITE
    
    LLM --> OR
    AUDIO --> WH
    IMAGE --> VISION
    
    CONFIG --> DI
    DI --> MP
    DI --> SM
    DI --> PS
    
    MEDIAP --> TEMP
    MAIN --> LOGS
    
    style TG fill:#e3f2fd
    style OR fill:#fff3e0
    style WH fill:#fff3e0
    style VISION fill:#fff3e0
    style SQLITE fill:#f3e5f5
    style LOGS fill:#f3e5f5
```

## Детальная схема потока данных

```mermaid
flowchart TD
    START([Пользователь отправляет сообщение]) --> TYPE{Тип сообщения}
    
    TYPE -->|Текст| TEXT[Текстовое сообщение]
    TYPE -->|Голос| VOICE[Голосовое сообщение]
    TYPE -->|Фото| PHOTO[Фото сообщение]
    TYPE -->|Документ| DOC[Документ сообщение]
    
    TEXT --> EXTRACT[Извлечение контента]
    VOICE --> DOWNLOAD1[Скачивание аудио]
    PHOTO --> DOWNLOAD2[Скачивание изображения]
    DOC --> DOWNLOAD3[Скачивание документа]
    
    DOWNLOAD1 --> TRANSCRIBE[Транскрипция через Whisper]
    DOWNLOAD2 --> ANALYZE[Анализ через Vision API]
    DOWNLOAD3 --> ANALYZE
    
    TRANSCRIBE --> EXTRACT
    ANALYZE --> EXTRACT
    
    EXTRACT --> SESSION[Получение сессии]
    SESSION --> ADD_MSG[Добавление сообщения в историю]
    
    ADD_MSG --> AUX_ANALYSIS[Анализ контекста вспомогательной моделью]
    AUX_ANALYSIS --> CONTEXT_PROC[Обработка контекста]
    
    CONTEXT_PROC --> BUILD_DIALOG[Построение диалогового контекста]
    BUILD_DIALOG --> DIALOG_GEN[Генерация ответа диалоговой моделью]
    
    DIALOG_GEN --> SUCCESS{Успешно?}
    SUCCESS -->|Да| ADD_RESPONSE[Добавление ответа в историю]
    SUCCESS -->|Нет| GRACEFUL[Graceful Degradation]
    
    ADD_RESPONSE --> SAVE[Сохранение сессии]
    GRACEFUL --> SAVE
    
    SAVE --> FORMAT[Форматирование для Telegram]
    FORMAT --> SEND[Отправка ответа]
    SEND --> END([Конец])
    
    style START fill:#e1f5fe
    style END fill:#c8e6c9
    style AUX_ANALYSIS fill:#fff3e0
    style DIALOG_GEN fill:#fff3e0
    style GRACEFUL fill:#ffebee
    style TRANSCRIBE fill:#e8f5e8
    style ANALYZE fill:#e8f5e8
```

## Схема компонентов и их взаимодействий

```mermaid
graph LR
    subgraph "Telegram Layer"
        A[Telegram API] --> B[aiogram Bot]
        B --> C[Dispatcher]
        C --> D[Router]
    end
    
    subgraph "Handler Layer"
        D --> E[Text Handler]
        D --> F[Voice Handler]
        D --> G[Photo Handler]
        D --> H[Document Handler]
    end
    
    subgraph "Processing Layer"
        E --> I[UnifiedMessageProcessor]
        F --> I
        G --> I
        H --> I
    end
    
    subgraph "Media Processing"
        I --> J[MediaProcessor]
        J --> K[AudioHandler]
        J --> L[ImageAnalyzer]
        K --> M[Whisper API]
        L --> N[Vision API]
    end
    
    subgraph "State Management"
        I --> O[SessionManager]
        O --> P[SessionState]
        O --> Q[PersistenceAdapter]
        Q --> R[SessionRepository]
        R --> S[SQLite Database]
    end
    
    subgraph "Context Analysis"
        I --> T[PromptStore]
        T --> U[ContextAnalyzer]
        U --> V[Auxiliary Model]
        V --> W[ContextProcessor]
    end
    
    subgraph "Dialog Generation"
        W --> X[DialogBuilder]
        X --> Y[Dialog Model]
        Y --> Z[LLMClient]
        Z --> AA[OpenRouter API]
    end
    
    subgraph "Formatting & Output"
        Y --> BB[TelegramFormatter]
        BB --> CC[MathConverter]
        BB --> DD[EducationalTemplates]
        BB --> EE[HTML Formatter]
        EE --> FF[Telegram Response]
    end
    
    style V fill:#fff3e0
    style Y fill:#fff3e0
    style M fill:#e8f5e8
    style N fill:#e8f5e8
    style AA fill:#fff3e0
    style S fill:#f3e5f5
```

## Схема данных и состояний

```mermaid
erDiagram
    SESSIONS {
        TEXT chat_id PK
        TEXT scenario
        TEXT question
        TEXT topic
        BOOLEAN is_new_question
        BOOLEAN is_new_topic
        INTEGER understanding_level
        INTEGER previous_understanding_level
        TEXT previous_topic
        TEXT user_preferences
        TEXT last_image_analysis
        INTEGER image_analysis_count
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
    
    MESSAGES {
        INTEGER id PK
        TEXT chat_id FK
        TEXT role
        TEXT content
        TIMESTAMP timestamp
    }
    
    MEDIA_FILES {
        INTEGER id PK
        TEXT chat_id FK
        TEXT file_id
        TEXT file_type
        TEXT file_path
        TEXT analysis_result
        TIMESTAMP created_at
    }
    
    MIGRATIONS {
        INTEGER version PK
        TEXT name
        TIMESTAMP applied_at
    }
    
    SESSIONS ||--o{ MESSAGES : "has many"
    SESSIONS ||--o{ MEDIA_FILES : "has many"
```

## Схема конфигурации и зависимостей

```mermaid
graph TD
    subgraph "Environment Variables"
        ENV1[TELEGRAM_BOT_TOKEN]
        ENV2[OPENROUTER_API_KEY]
        ENV3[OPENROUTER_MODEL]
        ENV4[DATABASE_ENABLED]
        ENV5[AUDIO_ENABLED]
        ENV6[IMAGE_ANALYSIS_ENABLED]
        ENV7[LLM_TEMPERATURE]
        ENV8[LLM_MAX_TOKENS]
    end
    
    subgraph "Configuration Layer"
        CONFIG[settings/config.py]
        SETTINGS[Settings Class]
    end
    
    subgraph "Dependency Injection"
        DI[core/service_registry.py]
        REGISTRY[Service Registry]
    end
    
    subgraph "Service Instances"
        LLM_CLIENT[LLMClient]
        SESSION_MGR[SessionManager]
        PROMPT_STORE[PromptStore]
        MEDIA_PROC[MediaProcessor]
        FORMATTER[TelegramFormatter]
    end
    
    ENV1 --> CONFIG
    ENV2 --> CONFIG
    ENV3 --> CONFIG
    ENV4 --> CONFIG
    ENV5 --> CONFIG
    ENV6 --> CONFIG
    ENV7 --> CONFIG
    ENV8 --> CONFIG
    
    CONFIG --> SETTINGS
    SETTINGS --> DI
    DI --> REGISTRY
    
    REGISTRY --> LLM_CLIENT
    REGISTRY --> SESSION_MGR
    REGISTRY --> PROMPT_STORE
    REGISTRY --> MEDIA_PROC
    REGISTRY --> FORMATTER
    
    style CONFIG fill:#e8f5e8
    style DI fill:#fff3e0
    style REGISTRY fill:#f3e5f5
```

## Схема обработки ошибок и graceful degradation

```mermaid
graph TD
    START([Начало обработки]) --> TRY[Попытка выполнения]
    
    TRY --> SUCCESS{Успешно?}
    
    SUCCESS -->|Да| NORMAL[Нормальная обработка]
    SUCCESS -->|Нет| ERROR_TYPE{Тип ошибки}
    
    ERROR_TYPE -->|LLM Timeout| RETRY1[Повтор через 0.5s]
    ERROR_TYPE -->|LLM 5xx| RETRY2[Повтор через 0.5s]
    ERROR_TYPE -->|LLM Rate Limit| RATE_LIMIT[Ошибка rate limit]
    ERROR_TYPE -->|DB Unavailable| IN_MEMORY[In-memory режим]
    ERROR_TYPE -->|Media Error| FALLBACK[Fallback на текст]
    ERROR_TYPE -->|Other| GENERIC[Общая ошибка]
    
    RETRY1 --> TRY
    RETRY2 --> TRY
    
    RATE_LIMIT --> USER_ERROR[Сообщение пользователю]
    IN_MEMORY --> CONTINUE[Продолжить без БД]
    FALLBACK --> CONTINUE
    GENERIC --> USER_ERROR
    
    NORMAL --> END([Успешное завершение])
    CONTINUE --> END
    USER_ERROR --> END
    
    style START fill:#e1f5fe
    style END fill:#c8e6c9
    style RETRY1 fill:#fff3e0
    style RETRY2 fill:#fff3e0
    style IN_MEMORY fill:#e8f5e8
    style FALLBACK fill:#e8f5e8
    style USER_ERROR fill:#ffebee
```

## Схема логирования и мониторинга

```mermaid
graph LR
    subgraph "Application Components"
        A[Bot Handlers]
        B[Message Processor]
        C[LLM Client]
        D[Session Manager]
        E[Media Processor]
        F[Database Manager]
    end
    
    subgraph "Logging System"
        G[Python Logging]
        H[Log Formatter]
        I[File Handler]
    end
    
    subgraph "Log Output"
        J[/log/app.log]
        K[Console Output]
    end
    
    subgraph "Log Content"
        L[User Messages]
        M[LLM Requests/Responses]
        N[Database Operations]
        O[Media Processing]
        P[Errors & Exceptions]
        Q[Performance Metrics]
    end
    
    A --> G
    B --> G
    C --> G
    D --> G
    E --> G
    F --> G
    
    G --> H
    H --> I
    I --> J
    I --> K
    
    J --> L
    J --> M
    J --> N
    J --> O
    J --> P
    J --> Q
    
    style G fill:#e8f5e8
    style J fill:#f3e5f5
    style P fill:#ffebee
    style Q fill:#fff3e0
```

Эта архитектурная диаграмма показывает полную структуру Easy Lessons Bot, включая все компоненты, их взаимодействия, потоки данных, обработку ошибок и системы логирования.
