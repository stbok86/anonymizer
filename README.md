# 🔒 Anonymizer - Document Anonymization System

Система анонимизации документов с микросервисной архитектурой для обработки DOCX файлов с извлечением и анонимизацией чувствительных данных.

## 🎯 Ключевые возможности

- ✅ **Полное извлечение header/footer данных** из DOCX файлов
- ✅ **Поддержка SDT элементов** для колонтитулов
- ✅ **Нормализация текста** с обработкой неразрывных пробелов
- ✅ **Микросервисная архитектура** с 6 независимыми сервисами
- ✅ **Windows-ready** с .bat скриптами запуска
- ✅ **Virtual environments** для изолированных зависимостей

## 🏗️ Архитектура системы

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │  Orchestrator   │
│  (Streamlit)    │◄──►│   (FastAPI)     │◄──►│   (FastAPI)     │
│   Port: 8501    │    │   Port: 8000    │    │   Port: 8002    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
          ┌─────────▼────┐ ┌────▼──────┐ ┌──▼────────┐
          │   Document   │ │    NLP    │ │   Rule    │
          │  Processing  │ │ Service   │ │  Engine   │
          │ Port: 8001   │ │Port: 8003 │ │Port: 8004 │
          └──────────────┘ └───────────┘ └───────────┘
```

## 📁 Структура проекта

```
Anonymizer/
├── 📂 frontend/                    # Streamlit UI
├── 📂 gateway/                     # API Gateway
├── 📂 orchestrator/               # Service orchestration
├── 📂 unified_document_service/   # 🔥 Document processing (CRITICAL)
│   ├── app/
│   │   ├── main.py               # FastAPI endpoints
│   │   ├── block_builder.py      # 🔴 CRITICAL: Header/footer extraction
│   │   └── document_io.py        # DOCX parsing utilities
│   ├── test_docs/                # Test documents
│   └── test_block_builder.py     # Validation tests
├── 📂 nlp_service/               # NLP processing
├── 📂 rule_engine/               # Business rules
├── 🚀 start_*.bat                # Service startup scripts
└── 📋 *.md                       # Documentation
```

## 🚀 Быстрый старт

### Запуск всех сервисов одной командой:
```bash
start_all_services.bat
```

### Запуск отдельных сервисов:
```bash
start_frontend.bat           # Streamlit UI (8501)
start_gateway.bat           # API Gateway (8000)
start_orchestrator.bat      # Orchestrator (8002)
start_unified_document_service.bat  # Document processor (8001)
start_nlp_service.bat       # NLP service (8003)
start_rule_engine.bat       # Rule engine (8004)
```

## 🔥 Критичные исправления (v1.0.0)

### ✅ BlockBuilder - решена проблема с колонтитулами
- **Проблема**: Данные из headers/footers (например, "ЕИСУФХД.13/ОК-2023.3.ПМ.1") не извлекались
- **Решение**: Добавлена поддержка SDT элементов с расширенным XPath
- **Результат**: 100% извлечение чувствительных данных для анонимизации

### 🔧 Ключевые улучшения:
1. **Расширенный XPath**: `.//w:t | .//w:instrText | .//a:t | .//w:fldSimple/@w:instr`
2. **Нормализация текста**: замена `\xa0` → пробел, сжатие пробелов
3. **Метаданные**: `applies_to: "section"` для понимания области применения
4. **Пост-обработка**: поиск вхождений header-текста в теле документа

## 📊 Тестирование

### Запуск тестов BlockBuilder:
```bash
cd unified_document_service
C:\Projects\Anonymizer\venv_unified_document_service\Scripts\python.exe test_block_builder.py
```

### Результаты тестирования:
- ✅ **131 блок** обработано
- ✅ **2 header_sdt блока** с критичными данными
- ✅ **Нормализация текста** работает корректно
- ✅ **Метаданные** добавлены для всех header/footer блоков

## 🔒 Безопасность и анонимизация

### Критично: Header/Footer обработка
- **SDT элементы**: полное извлечение структурированных данных
- **Секции документа**: один header применяется ко всем страницам секции
- **Нормализация**: устранение скрытых символов (`\xa0`, множественные пробелы)
- **Пометка sensitive**: автоматическое выявление чувствительных данных

### Гарантии системы:
- 🛡️ Никакие данные из колонтитулов не будут пропущены
- 🔍 Полное покрытие всех типов DOCX элементов
- 📋 Метаданные для точной анонимизации
- ✅ Готовность к продакшн использованию

## 🛠️ Технологический стек

- **Backend**: FastAPI, Python 3.11+
- **Frontend**: Streamlit
- **Document Processing**: python-docx, lxml
- **Architecture**: Microservices
- **Environment**: Windows + Virtual Environments
- **Testing**: Custom test harness

Проект состоит из следующих сервисов:

- **Frontend** (port 8501) - Streamlit интерфейс пользователя
- **Gateway** (port 8000) - API шлюз для маршрутизации запросов
- **Orchestrator** (port 8002) - Координатор взаимодействия между сервисами
- **Unified Document Service** (port 8001) - Сервис обработки документов
- **NLP Service** (port 8003) - Сервис обработки естественного языка
- **Rule Engine** (port 8004) - Движок правил анонимизации

## Требования

- Docker
- Docker Compose
- Windows PowerShell (для Windows)

## Запуск проекта

### 1. Клонирование и переход в директорию проекта

```powershell
cd c:\Projects\Anonymizer
```

### 2. Сборка и запуск всех сервисов

```powershell
docker-compose up --build
```

### 3. Запуск в фоновом режиме

```powershell
docker-compose up -d --build
```

### 4. Просмотр логов

```powershell
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f frontend
docker-compose logs -f gateway
docker-compose logs -f orchestrator
```

### 5. Остановка сервисов

```powershell
docker-compose down
```

### 6. Полная очистка (с удалением образов)

```powershell
docker-compose down --rmi all --volumes --remove-orphans
```

## Доступ к сервисам

После запуска сервисы будут доступны по следующим адресам:

- **Frontend**: http://localhost:8501
- **Gateway**: http://localhost:8000
- **Orchestrator**: http://localhost:8002
- **Unified Document Service**: http://localhost:8001
- **NLP Service**: http://localhost:8003
- **Rule Engine**: http://localhost:8004

## Проверка состояния сервисов

Каждый сервис имеет health check endpoints:

```powershell
# Gateway
curl http://localhost:8000/healthz

# Orchestrator  
curl http://localhost:8002/healthz

# Unified Document Service
curl http://localhost:8001/healthz

# NLP Service
curl http://localhost:8003/healthz

# Rule Engine
curl http://localhost:8004/healthz
```

## Разработка

### Структура проекта

```
Anonymizer/
├── docker-compose.yml          # Конфигурация Docker Compose
├── .env                        # Переменные окружения
├── README.md                   # Документация
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   └── main.py
├── gateway/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   └── app/
│       └── main.py
├── orchestrator/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   └── app/
│       └── main.py
├── unified_document_service/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── block_builder.py
│   │   └── document_io.py
│   ├── modules/
│   └── test_docs/
├── nlp_service/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   └── app/
│       └── main.py
└── rule_engine/
    ├── Dockerfile
    ├── .dockerignore
    ├── requirements.txt
    └── app/
        └── main.py
```

### Отладка

1. **Проверка состояния контейнеров:**
   ```powershell
   docker-compose ps
   ```

2. **Подключение к контейнеру:**
   ```powershell
   docker-compose exec <service_name> /bin/bash
   ```

3. **Просмотр логов в реальном времени:**
   ```powershell
   docker-compose logs -f --tail=100
   ```

4. **Пересборка конкретного сервиса:**
   ```powershell
   docker-compose build <service_name>
   docker-compose up -d <service_name>
   ```

## Устранение неполадок

### Проблемы с портами

Если порты заняты, измените их в `docker-compose.yml`:

```yaml
ports:
  - "8501:8501"  # изменить первый порт, например на "8502:8501"
```

### Проблемы с правами доступа

В Windows убедитесь, что Docker Desktop запущен с правами администратора.

### Проблемы с сетью

Проверьте, что Docker daemon запущен:

```powershell
docker version
```

## Переменные окружения

Основные переменные находятся в файле `.env`. Для изменения настроек отредактируйте этот файл и перезапустите сервисы.

## Тестирование

Для тестирования API используйте:

- Postman
- curl
- Swagger UI (доступен на каждом FastAPI сервисе по адресу `/docs`)

Примеры endpoints:
- http://localhost:8001/docs - Swagger для Unified Document Service
- http://localhost:8002/docs - Swagger для Orchestrator
- http://localhost:8003/docs - Swagger для NLP Service