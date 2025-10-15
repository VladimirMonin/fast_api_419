# 📊 Диаграммы архитектуры FastAPI + Celery + Redis

## 1. Общая архитектура системы

```mermaid
graph TB
    subgraph "Клиентская часть"
        Client[👤 Клиент<br/>Браузер/Postman]
    end
    
    subgraph "Backend - FastAPI Application"
        FastAPI[🚀 FastAPI Server<br/>uvicorn main:app<br/>Port: 8000]
        Routes[📍 Routes<br/>products.py]
        Tasks[📦 Tasks Module<br/>notifications.py]
        Config[⚙️ Config<br/>settings from .env]
    end
    
    subgraph "Message Broker & Backend"
        Redis[(🗄️ Redis Server<br/>Port: 6379<br/>Database: 0)]
        Queue[📬 Task Queue<br/>Задачи в очереди]
        Results[📋 Results Backend<br/>Результаты выполнения]
    end
    
    subgraph "Background Worker"
        Celery[⚙️ Celery Worker<br/>celery worker --pool=solo]
        Executor[🔧 Task Executor<br/>send_tg_notification]
    end
    
    Client -->|HTTP Request| FastAPI
    FastAPI --> Routes
    Routes --> Tasks
    Tasks -->|.delay()| Redis
    Redis --> Queue
    Queue -->|Poll| Celery
    Celery --> Executor
    Executor -->|Save Result| Results
    Results --> Redis
    FastAPI -->|Read Settings| Config
    Celery -->|Read Settings| Config
    
    style FastAPI fill:#61dafb,stroke:#333,stroke-width:2px
    style Redis fill:#dc382d,stroke:#333,stroke-width:2px
    style Celery fill:#37814a,stroke:#333,stroke-width:2px
    style Client fill:#ffd700,stroke:#333,stroke-width:2px
```

---

## 2. Поток создания товара с фоновой задачей

```mermaid
graph LR
    A[👤 Клиент] -->|POST /products/| B[🚀 FastAPI]
    B -->|1. Валидация| C{Данные OK?}
    C -->|❌ Нет| D[400 Bad Request]
    C -->|✅ Да| E[Создать товар]
    E -->|2. Сохранить| F[📝 products list]
    E -->|3. Запустить задачу| G[send_tg_notification.delay]
    G -->|Отправить в очередь| H[(🗄️ Redis Queue)]
    B -->|4. Вернуть ответ| I[201 Created]
    I --> A
    H -->|Celery забирает| J[⚙️ Celery Worker]
    J -->|5. Выполнить 30 сек| K[📱 Send to Telegram]
    K -->|6. Сохранить результат| L[(🗄️ Redis Backend)]
    
    style A fill:#ffd700
    style B fill:#61dafb
    style H fill:#dc382d
    style J fill:#37814a
    style I fill:#90EE90
    style D fill:#ffcccb
```

---

## 3. Жизненный цикл задачи Celery

```mermaid
stateDiagram-v2
    [*] --> Pending: Задача создана<br/>.delay()
    Pending --> Received: Worker получил задачу
    Received --> Started: Начало выполнения
    Started --> Success: Выполнено успешно
    Started --> Retry: Ошибка (попытка 1)
    Retry --> Started: Повтор через 5 сек
    Retry --> Retry: Ошибка (попытка 2)
    Retry --> Failed: max_retries=3<br/>Все попытки исчерпаны
    Success --> [*]: Результат в Redis
    Failed --> [*]: Задача провалена
    
    note right of Pending
        task.id = UUID
        task.state = 'PENDING'
    end note
    
    note right of Started
        task.state = 'STARTED'
        Выполняется 30 секунд
    end note
    
    note right of Success
        task.state = 'SUCCESS'
        task.result = {...}
    end note
    
    note right of Retry
        self.retry(countdown=5)
        max_retries=3
    end note
```

---

## 4. Компоненты системы и их взаимодействие

```mermaid
graph TB
    subgraph "Process 1: FastAPI"
        A1[main.py<br/>FastAPI app]
        A2[routes/products.py<br/>Маршруты API]
        A3[tasks/notifications.py<br/>Определение задач]
        A4[config.py<br/>Настройки из .env]
        
        A1 --> A2
        A2 --> A3
        A1 --> A4
    end
    
    subgraph "Process 2: Redis Server"
        B1[(Redis Database 0)]
        B2[Queue: celery]
        B3[Results: celery-task-meta-*]
        
        B1 --> B2
        B1 --> B3
    end
    
    subgraph "Process 3: Celery Worker"
        C1[tasks/celery_app.py<br/>Инициализация]
        C2[tasks/notifications.py<br/>Исполнение задач]
        C3[Конфигурация<br/>worker_pool=solo]
        
        C1 --> C2
        C1 --> C3
    end
    
    A3 -->|send_tg_notification.delay| B2
    B2 -->|Poll for tasks| C2
    C2 -->|Save result| B3
    
    style A1 fill:#61dafb
    style B1 fill:#dc382d
    style C1 fill:#37814a
```

---

## 5. Конфигурация Celery для Windows

```mermaid
mindmap
  root((Celery Config<br/>Windows))
    Broker
      Redis URL
        redis://localhost:6379/0
      Retry on Startup
        broker_connection_retry_on_startup=True
    Backend
      Redis URL
        redis://localhost:6379/0
      Store Results
        Сохранение в Redis
    Worker Pool
      Type: solo
        worker_pool="solo"
      Concurrency: 1
        worker_concurrency=1
      Причина
        Windows не поддерживает fork
    Task Settings
      Acknowledge
        task_acks_late=True
      Max Retries
        max_retries=3
      Retry Countdown
        countdown=5 сек
```

---

## 6. Порядок запуска системы

```mermaid
sequenceDiagram
    participant Dev as 👨‍💻 Разработчик
    participant T1 as Terminal 1
    participant T2 as Terminal 2
    participant T3 as Terminal 3
    participant Redis as Redis Server
    participant FastAPI as FastAPI App
    participant Celery as Celery Worker
    
    Note over Dev,Celery: Инициализация окружения (один раз)
    Dev->>Dev: python -m venv venv
    Dev->>Dev: pip install -r requirements.txt
    Dev->>Dev: Copy .env.example → .env
    
    Note over Dev,Celery: Запуск системы (каждый раз)
    
    Dev->>T1: Открыть терминал 1
    T1->>Redis: redis-server
    activate Redis
    Redis-->>T1: Redis server started<br/>Port: 6379
    
    Dev->>T2: Открыть терминал 2
    T2->>T2: .\venv\Scripts\Activate.ps1
    T2->>FastAPI: uvicorn main:app --reload
    activate FastAPI
    FastAPI->>FastAPI: Загрузка config.py
    FastAPI->>FastAPI: Регистрация routes
    FastAPI->>FastAPI: Импорт tasks
    FastAPI-->>T2: Uvicorn running on<br/>http://0.0.0.0:8000
    
    Dev->>T3: Открыть терминал 3
    T3->>T3: .\venv\Scripts\Activate.ps1
    T3->>Celery: celery -A tasks.celery_app<br/>worker --pool=solo -l info
    activate Celery
    Celery->>Redis: Подключение к брокеру
    Redis-->>Celery: Подключено
    Celery->>Celery: Регистрация задач
    Celery-->>T3: celery@WIN-... ready
    
    Note over Dev,Celery: ✅ Система готова к работе!
    
    Dev->>FastAPI: Открыть http://localhost:8000/docs
    FastAPI-->>Dev: Swagger UI
```

---

## 7. Обработка ошибок и повторные попытки

```mermaid
flowchart TD
    Start([Задача получена<br/>Celery Worker]) --> Execute[Выполнение<br/>send_tg_notification]
    Execute --> Check{Успешно?}
    
    Check -->|✅ Да| SaveResult[Сохранить результат<br/>в Redis Backend]
    SaveResult --> ACK[Подтвердить выполнение<br/>task_acks_late=True]
    ACK --> Done([Задача завершена])
    
    Check -->|❌ Нет| CountRetries{Попытки < 3?}
    CountRetries -->|Да| Wait[Ожидание<br/>countdown=5 сек]
    Wait --> Retry[Повторная попытка]
    Retry --> Execute
    
    CountRetries -->|Нет| Failed[Задача провалена<br/>FAILED]
    Failed --> SaveError[Сохранить ошибку<br/>в Redis]
    SaveError --> Done
    
    style Start fill:#90EE90
    style Done fill:#90EE90
    style Failed fill:#ffcccb
    style SaveResult fill:#87CEEB
    style ACK fill:#87CEEB
```

---

## 8. Структура файлов проекта

```mermaid
graph TD
    Root[fast_api_419/]
    
    Root --> Main[main.py<br/>🚀 FastAPI app]
    Root --> Config[config.py<br/>⚙️ Settings]
    Root --> Data[data.py<br/>📊 Products data]
    Root --> Env[.env<br/>🔐 Environment vars]
    Root --> Req[requirements.txt<br/>📦 Dependencies]
    
    Root --> Routes[routes/]
    Routes --> RoutesInit[__init__.py]
    Routes --> Products[products.py<br/>📍 API endpoints]
    
    Root --> Schemas[schemas/]
    Schemas --> SchemasInit[__init__.py]
    Schemas --> Product[product.py<br/>📋 Pydantic models]
    
    Root --> Tasks[tasks/]
    Tasks --> TasksInit[__init__.py]
    Tasks --> CeleryApp[celery_app.py<br/>⚙️ Celery config]
    Tasks --> Notifications[notifications.py<br/>📨 Task functions]
    
    Root --> Doc[doc/]
    Doc --> DetailedExpl[celery_detailed_explanation.md]
    Doc --> Diagrams[architecture_diagrams.md]
    
    style Main fill:#61dafb
    style CeleryApp fill:#37814a
    style Config fill:#ffa500
    style Products fill:#61dafb
```

---

## 9. Redis: Структура данных

```mermaid
graph TB
    subgraph Redis[(Redis Server<br/>localhost:6379)]
        DB0[Database 0]
        
        subgraph "Broker - Очередь задач"
            Queue[Queue: 'celery'<br/>Type: List]
            Task1[Task 1: JSON]
            Task2[Task 2: JSON]
            Task3[Task 3: JSON]
            
            Queue --> Task1
            Queue --> Task2
            Queue --> Task3
        end
        
        subgraph "Backend - Результаты"
            Meta1[celery-task-meta-uuid1<br/>Type: String<br/>TTL: 1 day]
            Meta2[celery-task-meta-uuid2<br/>Type: String<br/>TTL: 1 day]
            
            Result1[Status: SUCCESS<br/>Result: {...}]
            Result2[Status: PENDING<br/>Result: null]
            
            Meta1 --> Result1
            Meta2 --> Result2
        end
        
        DB0 --> Queue
        DB0 --> Meta1
        DB0 --> Meta2
    end
    
    FastAPI[FastAPI] -->|LPUSH| Queue
    Celery[Celery Worker] -->|BRPOP| Queue
    Celery -->|SET| Meta1
    
    style Redis fill:#dc382d,color:#fff
    style Queue fill:#ff6b6b
    style Meta1 fill:#4ecdc4
    style Meta2 fill:#4ecdc4
```

---

## 10. Сравнение: С Celery vs Без Celery

```mermaid
graph TB
    subgraph "❌ БЕЗ Celery - Синхронное выполнение"
        A1[Клиент] -->|POST /products/| B1[FastAPI]
        B1 --> C1[Создать товар]
        C1 --> D1[Отправить в Telegram<br/>⏱️ 30 секунд ОЖИДАНИЕ]
        D1 --> E1[Вернуть ответ]
        E1 --> A1
        
        Note1[Клиент ждёт 30 секунд!<br/>Плохой UX<br/>Блокировка потока]
    end
    
    subgraph "✅ С Celery - Асинхронное выполнение"
        A2[Клиент] -->|POST /products/| B2[FastAPI]
        B2 --> C2[Создать товар]
        C2 --> D2[Отправить задачу<br/>в очередь ⚡ 1мс]
        D2 --> E2[Вернуть ответ<br/>немедленно]
        E2 --> A2
        
        D2 -.->|Асинхронно| F2[Celery Worker]
        F2 --> G2[Отправить в Telegram<br/>⏱️ 30 секунд в фоне]
        
        Note2[Клиент получает ответ<br/>мгновенно!<br/>Отличный UX<br/>Без блокировки]
    end
    
    style Note1 fill:#ffcccb
    style Note2 fill:#90EE90
    style D1 fill:#ff6b6b
    style D2 fill:#4ecdc4
```

---

## 📝 Пояснения к диаграммам

### Диаграмма 1: Общая архитектура

Показывает все компоненты системы и их взаимосвязи. Три основных процесса работают независимо.

### Диаграмма 2: Поток создания товара

Демонстрирует путь HTTP-запроса от клиента через FastAPI к Redis и Celery Worker.

### Диаграмма 3: Жизненный цикл задачи

State-диаграмма показывает все возможные состояния задачи: от создания до успеха/провала.

### Диаграмма 4: Компоненты системы

Детальная структура трёх процессов и их файлов.

### Диаграмма 5: Конфигурация Celery

Mind map всех критичных параметров для Windows.

### Диаграмма 6: Порядок запуска

Sequence diagram показывает правильную последовательность запуска всех компонентов.

### Диаграмма 7: Обработка ошибок

Flowchart логики повторных попыток с max_retries=3.

### Диаграмма 8: Структура файлов

Дерево файлов проекта с указанием назначения каждого файла.

### Диаграмма 9: Redis структура

Внутреннее устройство Redis: очереди задач и хранилище результатов.

### Диаграмма 10: Сравнение

Наглядное сравнение синхронного и асинхронного выполнения задач.

---

## 🎯 Ключевые моменты из диаграмм

1. **Три независимых процесса**: Redis, FastAPI, Celery Worker
2. **Асинхронность**: FastAPI не ждёт выполнения задачи
3. **Надёжность**: task_acks_late=True + max_retries=3
4. **Windows совместимость**: worker_pool="solo" обязателен
5. **Последовательность запуска**: Redis → FastAPI → Celery

---

**Все диаграммы совместимы с Mermaid и отображаются в GitHub, GitLab, VS Code**
