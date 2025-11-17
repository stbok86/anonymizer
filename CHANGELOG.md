# CHANGELOG

## [v1.4] - 2025-11-17

### 🎯 Major Architecture Improvements & Critical Bug Fixes

#### ✅ Critical Bug Fixes
- **Fixed NLP detections not showing in UI** - Removed aggressive deduplication logic that was incorrectly removing all NLP results as "duplicates"
- **Fixed anonymization function errors** - Resolved 'category' field KeyError by adding proper error handling with `item.get('category', 'unknown')`
- **Fixed duplicate NLP service calls** - Removed duplicate NLP calls from Rule Engine to eliminate redundant processing
- **Fixed Form parameter handling** - Corrected `/anonymize_selected` endpoint to properly receive `selected_items` using `Form()` parameter

#### 🔧 Architecture Enhancements
- **Clear service separation** - Rule Engine now handles only structured data (regex patterns), NLP Service handles unstructured data (entities, names, organizations)
- **Enhanced request logging** - Added comprehensive logging middleware to Gateway and Unified Document Service for better debugging
- **Improved error handling** - Better exception handling across all services with user-friendly error messages
- **Modular detection strategies** - Implemented detection factory pattern in NLP Service for extensible detection methods

#### 🎨 UI/UX Improvements
- **Added Block ID column** - New column in sensitive data table showing exact document block (`table_0`, `paragraph_74`, etc.) where data was found
- **Better source attribution** - Clear indication of whether data was found by Rule Engine vs NLP Service
- **Improved table configuration** - Proper column widths, tooltips, and user guidance
- **Enhanced visual feedback** - Better error messages and status indicators

#### 🛠️ Technical Improvements
- **Better JSON serialization** - Improved data handling for anonymization requests with proper defaults
- **Enhanced pattern loading** - More robust pattern file loading with fallback paths
- **Improved configuration management** - Better separation of concerns and configuration handling
- **Code quality improvements** - Better modular design and maintainability

#### 📋 System Reliability
- **Comprehensive logging** - Request/response logging across all services for debugging
- **Better service communication** - More reliable HTTP API communication between microservices
- **Improved data validation** - Better handling of missing or malformed data
- **Enhanced error recovery** - Graceful handling of service failures

### 🔄 Migration Notes
- No breaking changes for existing users
- Services automatically restart to pick up new configurations
- All existing data and patterns remain compatible

### 📊 System Performance
- Reduced duplicate processing by eliminating redundant NLP calls
- Improved memory usage through better data handling
- Faster error detection and resolution through enhanced logging

---

## [1.3.0] - 2025-11-13

### 🚀 Major Features

#### NLP Service Integration
- **Полная интеграция NLP Service** для обработки неструктурированных данных
- **Микросервисная архитектура**: Rule Engine (8003) → NLP Service (8006) → Unified Service (8009) → Gateway (8002) → Frontend (8501)
- **Объединенный workflow**: одновременный анализ документов через Rule Engine и NLP Service
- **Единый интерфейс результатов** с показом источника обнаружения

#### Advanced Detection Methods
- **spaCy NER (PER/ORG/LOC)**: использование предтренированной русской модели `ru_core_news_sm`
- **Морфологический анализ (улучш.)**: продвинутый анализ с помощью pymorphy3
- **4-уровневая система обнаружения имен**: 
  - spaCy NER (confidence: 0.8)
  - Morphological Enhanced (confidence: 0.7) 
  - Contextual Analysis (confidence: 0.6)
  - Custom Patterns (confidence: 0.9)
- **Regex паттерны**: специализированные паттерны для различных типов данных

#### User Interface Enhancements
- **Новая колонка "Метод обнаружения"** в таблице результатов
- **Детальная информация о методах**: показывает точный алгоритм обнаружения
- **Источник данных**: различение между Rule Engine и NLP Service результатами
- **Улучшенная визуализация**: понятные названия методов на русском языке

### 🔧 Technical Improvements

#### Architecture
- **Unified Document Service**: новый координирующий сервис для объединения результатов
- **Async/Await поддержка**: улучшенная производительность API
- **Proper error handling**: детальная обработка ошибок по всей цепочке сервисов
- **Health checks**: проверки состояния всех микросервисов

#### Data Processing
- **Block-based analysis**: интеллектуальное разбиение документов на блоки
- **Confidence scoring**: система оценки уверенности для каждого обнаружения
- **Deduplication**: удаление дубликатов между разными методами обнаружения
- **Context validation**: проверка контекста для повышения точности

### 🐛 Bug Fixes

#### Regex Pattern Improvements
- **Исправлен IGNORECASE флаг для person_name**: убран `re.IGNORECASE` для категории `person_name` чтобы избежать ложных срабатываний
- **Решена проблема ложных обнаружений**: фразы типа "Государственный контракт от", "на выполнение работ" больше не определяются как имена
- **Улучшена точность ФИО паттернов**: теперь ищет только слова с заглавной буквы

#### Frontend Fixes
- **Исправлено отображение методов**: корректная передача полей `method` и `spacy_label` из API
- **Улучшена обработка данных**: правильное маппирование полей между сервисами
- **Стабилизирован UI**: убраны временные отладочные сообщения

### 📚 Dependencies

#### New Dependencies
- **spaCy**: `>=3.4.0` - для NLP анализа
- **ru_core_news_sm**: русская языковая модель spaCy
- **pymorphy3**: `>=1.2.0` - морфологический анализатор
- **dawg**: для быстрого словарного поиска

#### Updated Dependencies
- **uvicorn**: обновлен для всех сервисов
- **fastapi**: версии синхронизированы
- **streamlit**: улучшена совместимость

### 🏗️ Development

#### Code Quality
- **Удален отладочный код**: очищены все временные debug сообщения
- **Улучшена документация**: детальные комментарии в коде
- **Consistent naming**: унифицированы названия методов и переменных

#### Testing Infrastructure
- **Pattern validation**: тестирование regex паттернов
- **Service integration tests**: проверки взаимодействия сервисов
- **Method detection verification**: валидация корректности обнаружений

### 📊 Performance

- **Параллельная обработка**: одновременная работа Rule Engine и NLP Service
- **Оптимизированная загрузка моделей**: кеширование spaCy и pymorphy3
- **Reduced memory usage**: эффективное управление памятью в NLP процессах
- **Faster document processing**: улучшена скорость анализа документов

### 🔐 Security

- **Input validation**: проверка входных данных во всех сервисах
- **Error sanitization**: безопасная обработка ошибок
- **Service isolation**: изоляция между микросервисами

### 📖 Documentation

- **API documentation**: детальное описание всех endpoints
- **Method explanations**: объяснение алгоритмов обнаружения
- **Architecture diagrams**: схемы взаимодействия сервисов

---

## [1.2.0] - 2025-11-10
- Previous version features...

## [1.1.0] - 2025-11-05
- Previous version features...

## [1.0.0] - 2025-11-01
- Initial release