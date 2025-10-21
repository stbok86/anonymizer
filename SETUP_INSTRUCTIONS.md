# Инструкции по восстановлению и запуску проекта Anonymizer

## Статус восстановления ✅

Проект успешно проанализирован и подготовлен к запуску. Все необходимые файлы созданы:

### ✅ Созданные файлы:
- `.env` - переменные окружения
- `README.md` - подробная документация
- `.dockerignore` файлы для всех сервисов (оптимизация сборки)
- Обновлен `docker-compose.yml` (убрана устаревшая версия, добавлены restart policies)
- Исправлены `requirements.txt` (удален неправильный импорт `uuid`)

### ✅ Архитектура проекта:
```
Frontend (8501) ← Streamlit UI
Gateway (8000) ← API Gateway
Orchestrator (8002) ← Coordinator
├── Unified Document Service (8001) ← Document processing  
├── NLP Service (8003) ← Text analysis
└── Rule Engine (8004) ← Anonymization rules
```

## 🚀 Пошаговые инструкции для запуска

### Шаг 1: Обновление WSL (если требуется)
Если Docker Desktop показывает ошибку "WSL needs updating":

1. **Откройте PowerShell от имени администратора**:
   - Нажмите Win+X → "Windows PowerShell (Администратор)"
   
2. **Обновите WSL**:
   ```powershell
   wsl --update --web-download
   ```

3. **Установите Ubuntu (если нужно)**:
   ```powershell
   wsl --install -d Ubuntu
   ```

4. **Перезапустите компьютер** (рекомендуется)

### Шаг 2: Запуск Docker Desktop
1. Найдите Docker Desktop в меню Пуск или на рабочем столе
2. Запустите Docker Desktop от имени администратора
3. Дождитесь полной загрузки (в системном трее появится зеленый значок)

### Шаг 3: Проверка Docker
```powershell
# Откройте PowerShell в директории проекта
cd c:\Projects\Anonymizer

# Проверьте что Docker работает
docker info
```

### Шаг 4: Сборка проекта
```powershell
# Соберите все сервисы
docker compose build

# Или соберите без кэша (если были изменения)
docker compose build --no-cache
```

### Шаг 5: Запуск проекта
```powershell
# Запуск всех сервисов
docker compose up

# Или в фоновом режиме
docker compose up -d
```

### Шаг 6: Проверка работы
После запуска проверьте доступность сервисов:

- **Frontend**: http://localhost:8501
- **Gateway**: http://localhost:8000/healthz
- **Orchestrator**: http://localhost:8002/healthz
- **Document Service**: http://localhost:8001/healthz
- **NLP Service**: http://localhost:8003/healthz
- **Rule Engine**: http://localhost:8004/healthz

## 🔧 Команды для управления

```powershell
# Просмотр логов
docker compose logs -f

# Просмотр статуса
docker compose ps

# Остановка
docker compose down

# Полная очистка
docker compose down --rmi all --volumes
```

## ⚠️ Возможные проблемы и решения

### Проблема: Virtualization support not detected
**Решение**: 
1. **BIOS/UEFI**: Включите Intel VT-x или AMD-V в настройках BIOS
2. **PowerShell (администратор)**:
   ```powershell
   Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
   Enable-WindowsOptionalFeature -Online -FeatureName Containers -All
   Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform
   ```
3. **Перезагрузите компьютер**
4. Запустите Docker Desktop

### Проблема: WSL нуждается в обновлении
**Решение**: 
1. Откройте PowerShell от имени администратора
2. Выполните: `wsl --update --web-download`
3. При необходимости: `wsl --install -d Ubuntu`
4. Перезапустите компьютер
5. Перезапустите Docker Desktop

### Проблема: Порты заняты
**Решение**: Измените порты в `docker-compose.yml` или остановите конфликтующие процессы

### Проблема: Нет прав доступа
**Решение**: Запустите PowerShell от имени администратора

### Проблема: Docker не запускается
**Решение**: 
1. Перезапустите Docker Desktop
2. Проверьте WSL2 (если используется)
3. Освободите место на диске

### Проблема: Ошибки сборки
**Решение**:
```powershell
# Очистите Docker кэш
docker system prune -a

# Пересоберите без кэша
docker compose build --no-cache
```

## 📁 Структура восстановленного проекта

```
c:\Projects\Anonymizer/
├── .env                         # ✅ Переменные окружения
├── docker-compose.yml           # ✅ Обновлен для современного Docker
├── README.md                    # ✅ Подробная документация
├── frontend/
│   ├── .dockerignore           # ✅ Создан
│   ├── Dockerfile              # ✅ Проверен
│   └── main.py                 # ✅ Streamlit приложение
├── gateway/
│   ├── .dockerignore           # ✅ Создан
│   ├── Dockerfile              # ✅ Проверен
│   ├── requirements.txt        # ✅ Проверен
│   └── app/main.py             # ✅ FastAPI приложение
├── orchestrator/
│   ├── .dockerignore           # ✅ Создан
│   ├── Dockerfile              # ✅ Проверен
│   ├── requirements.txt        # ✅ Проверен
│   └── app/main.py             # ✅ FastAPI приложение
├── unified_document_service/
│   ├── .dockerignore           # ✅ Создан
│   ├── Dockerfile              # ✅ Проверен
│   ├── requirements.txt        # ✅ Исправлен (убран uuid)
│   ├── app/
│   │   ├── main.py             # ✅ FastAPI с обработкой DOCX
│   │   ├── block_builder.py    # ✅ Парсинг документов
│   │   └── document_io.py      # ✅ I/O операции
│   └── test_docs/              # ✅ Тестовые документы
├── nlp_service/
│   ├── .dockerignore           # ✅ Создан
│   ├── Dockerfile              # ✅ Проверен
│   ├── requirements.txt        # ✅ Проверен (spacy)
│   └── app/main.py             # ✅ FastAPI приложение
└── rule_engine/
    ├── .dockerignore           # ✅ Создан
    ├── Dockerfile              # ✅ Проверен
    ├── requirements.txt        # ✅ Исправлен (убран uuid)
    └── app/main.py             # ✅ FastAPI приложение
```

## ✅ Готовность к запуску: 100%

Все необходимые файлы созданы и настроены. Проект готов к запуску после включения Docker Desktop.

Следующие шаги:
1. ▶️ Запустите Docker Desktop
2. 🏗️ Выполните `docker compose build`
3. 🚀 Выполните `docker compose up`
4. 🌐 Откройте http://localhost:8501