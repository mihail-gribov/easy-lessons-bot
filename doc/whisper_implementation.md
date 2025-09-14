# Реализация локальной модели Whisper

## Обзор

Данный документ описывает план реализации локальной модели Whisper для транскрипции аудиосообщений в Easy Lessons Bot.

## Проблема

OpenRouter не поддерживает Whisper API, что приводит к ошибке 405 Method Not Allowed при попытке транскрипции аудио. Это блокирует основную функциональность бота по обработке голосовых сообщений.

## Решение

Реализовать локальную модель Whisper от OpenAI для транскрипции аудио без зависимости от внешних API.

## Технические детали

### Модели Whisper

| Модель | Размер | Скорость | Качество | Рекомендация |
|--------|--------|----------|----------|--------------|
| tiny | 39 MB | Очень быстро | Низкое | Для тестирования |
| base | 74 MB | Быстро | Среднее | Для разработки |
| small | 244 MB | Средне | Хорошее | **Рекомендуется** |
| medium | 769 MB | Медленно | Очень хорошее | Для продакшена |
| large | 1550 MB | Очень медленно | Отличное | Максимальное качество |

### Архитектура решения

```
AudioHandler
├── LocalWhisperTranscriber
│   ├── ModelLoader (загрузка модели)
│   ├── AudioPreprocessor (подготовка аудио)
│   ├── Transcriber (транскрипция)
│   └── PostProcessor (обработка результата)
├── CacheManager (кэширование результатов)
└── FallbackHandler (fallback на OpenAI API)
```

### Зависимости

```python
# Основные зависимости
whisper>=20231117
torch>=2.0.0
torchaudio>=2.0.0
ffmpeg-python>=0.2.0

# Опциональные для GPU
torch-audio>=2.0.0  # для CUDA поддержки
```

### Конфигурация

```python
# settings/config.py
whisper_model_size: str = Field(
    default="small",
    description="Whisper model size (tiny, base, small, medium, large)"
)
whisper_device: str = Field(
    default="auto",  # auto, cpu, cuda
    description="Device for Whisper inference"
)
whisper_cache_enabled: bool = Field(
    default=True,
    description="Enable transcription result caching"
)
whisper_cache_ttl: int = Field(
    default=3600,  # 1 hour
    description="Cache TTL in seconds"
)
```

### Реализация

#### 1. LocalWhisperTranscriber

```python
class LocalWhisperTranscriber:
    def __init__(self, model_size: str = "small", device: str = "auto"):
        self.model_size = model_size
        self.device = self._get_device(device)
        self.model = None
        self._load_model()
    
    def _get_device(self, device: str) -> str:
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    def _load_model(self):
        """Load Whisper model"""
        import whisper
        self.model = whisper.load_model(self.model_size, device=self.device)
    
    async def transcribe(self, audio_path: Path) -> Dict[str, Any]:
        """Transcribe audio file"""
        result = self.model.transcribe(
            str(audio_path),
            language="ru",  # Russian
            task="transcribe"
        )
        
        return {
            "transcript": result["text"].strip(),
            "language": result["language"],
            "duration": result.get("duration", 0),
            "confidence": self._calculate_confidence(result),
            "segments": result.get("segments", [])
        }
```

#### 2. CacheManager

```python
class TranscriptionCache:
    def __init__(self, ttl: int = 3600):
        self.cache = {}
        self.ttl = ttl
    
    def get_cache_key(self, file_path: Path) -> str:
        """Generate cache key from file hash"""
        import hashlib
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return f"whisper_{file_hash}"
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached result"""
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return result
            else:
                del self.cache[key]
        return None
    
    async def set(self, key: str, result: Dict[str, Any]):
        """Cache result"""
        self.cache[key] = (result, time.time())
```

#### 3. Интеграция с AudioHandler

```python
class AudioHandler:
    def __init__(self):
        self.settings = get_settings()
        self.local_transcriber = None
        self.cache = TranscriptionCache(self.settings.whisper_cache_ttl)
        
        # Initialize local Whisper if enabled
        if self.settings.whisper_local_enabled:
            self.local_transcriber = LocalWhisperTranscriber(
                model_size=self.settings.whisper_model_size,
                device=self.settings.whisper_device
            )
    
    async def transcribe_audio(self, file_path: Path) -> Dict[str, Any]:
        """Transcribe audio with fallback strategy"""
        # Check cache first
        cache_key = self.cache.get_cache_key(file_path)
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info("Using cached transcription result")
            return cached_result
        
        # Try local Whisper first
        if self.local_transcriber:
            try:
                result = await self.local_transcriber.transcribe(file_path)
                await self.cache.set(cache_key, result)
                return result
            except Exception as e:
                logger.warning(f"Local Whisper failed: {e}")
        
        # Fallback to OpenAI API
        if self.settings.openai_api_key:
            try:
                result = await self._transcribe_with_openai(file_path)
                return result
            except Exception as e:
                logger.error(f"OpenAI API failed: {e}")
        
        # Final fallback
        return {
            "transcript": "[Голосовое сообщение получено, но транскрипция недоступна]",
            "language": "ru",
            "duration": 0,
            "confidence": 0.0,
            "fallback": True
        }
```

### Установка и настройка

#### 1. Установка зависимостей

```bash
# Установка Whisper
pip install openai-whisper

# Установка PyTorch (CPU)
pip install torch torchaudio

# Установка PyTorch (GPU) - опционально
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# Установка FFmpeg
sudo apt update
sudo apt install ffmpeg
```

#### 2. Настройка переменных окружения

```bash
# .env
WHISPER_LOCAL_ENABLED=true
WHISPER_MODEL_SIZE=small
WHISPER_DEVICE=auto
WHISPER_CACHE_ENABLED=true
WHISPER_CACHE_TTL=3600
```

#### 3. Первый запуск

При первом запуске Whisper автоматически загрузит выбранную модель. Это может занять некоторое время в зависимости от размера модели и скорости интернета.

### Производительность

#### Время транскрипции (примерные значения)

| Модель | CPU (Intel i7) | GPU (RTX 3080) | Качество |
|--------|----------------|----------------|----------|
| tiny | 2-3 сек | 0.5 сек | 60% |
| base | 4-5 сек | 1 сек | 70% |
| small | 8-10 сек | 2 сек | 80% |
| medium | 20-25 сек | 4 сек | 90% |
| large | 40-50 сек | 8 сек | 95% |

#### Оптимизации

1. **Кэширование**: Избегать повторной транскрипции одинаковых файлов
2. **GPU ускорение**: Использовать CUDA если доступно
3. **Модель по умолчанию**: Использовать `small` как компромисс между скоростью и качеством
4. **Асинхронность**: Не блокировать основной поток при транскрипции

### Мониторинг и логирование

```python
# Логирование производительности
logger.info(f"Whisper transcription completed: "
           f"model={model_size}, device={device}, "
           f"duration={processing_time:.2f}s, "
           f"confidence={confidence:.2f}")
```

### Тестирование

#### Тестовые случаи

1. **Базовое тестирование**: Транскрипция короткого аудио (2-5 сек)
2. **Качество на русском**: Тестирование с русской речью
3. **Производительность**: Измерение времени транскрипции
4. **Кэширование**: Проверка работы кэша
5. **Fallback**: Тестирование fallback на OpenAI API
6. **Ошибки**: Обработка некорректных аудио файлов

#### Метрики качества

- **WER (Word Error Rate)**: Процент ошибок в словах
- **Время транскрипции**: Скорость обработки
- **Использование памяти**: Потребление RAM/VRAM
- **Стабильность**: Отсутствие крашей при длительной работе

### Развертывание

#### Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Download Whisper model
RUN python -c "import whisper; whisper.load_model('small')"

CMD ["python", "-m", "app.main"]
```

#### Production considerations

1. **Модель**: Использовать `small` или `medium` для продакшена
2. **GPU**: Рекомендуется GPU для лучшей производительности
3. **Кэш**: Настроить Redis для распределенного кэширования
4. **Мониторинг**: Добавить метрики производительности
5. **Масштабирование**: Рассмотреть отдельный сервис для транскрипции

## Заключение

Реализация локальной модели Whisper решит проблему с транскрипцией аудио и обеспечит независимость от внешних API. Рекомендуется начать с модели `small` как компромисса между качеством и производительностью.


