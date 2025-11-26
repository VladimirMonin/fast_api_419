# 📚 Занятие №1: Jinja2 + HTMX (Часть 3)

## Коммиты 4-5: Исправление багов и обновление карточек

---

## 🐛 Коммит 4: Исправление дублирования товаров в поиске

После запуска поиска мы обнаружили баг: некоторые товары дублируются в результатах. Давайте разберёмся, почему это происходит и как это исправить.

---

## 🔍 Диагностика проблемы

Проблема возникла в файле `core/database.py`, в функции `products_get_with_filters`.

### Файл: `core/database.py`

Исходный код функции (с багом):

```python
async def products_get_with_filters(
    session: AsyncSession,
    search: Optional[str] = None,
    sort: Optional[str] = None,
    has_image: bool = False,
) -> list[Product]:
    """Получение продуктов с фильтрацией и сортировкой."""
    
    # Базовый запрос с загрузкой связей
    stmt = select(ProductORM).options(
        selectinload(ProductORM.category), 
        selectinload(ProductORM.tags)
    )

    # Применяем поиск, если указан
    if search:
        stmt = (
            stmt.outerjoin(ProductORM.category)
            .outerjoin(ProductORM.tags)
            .where(
                or_(
                    ProductORM.name.ilike(f"%{search}%"),
                    CategoryORM.name.ilike(f"%{search}%"),
                    TagORM.name.ilike(f"%{search}%"),
                )
            )
        )  # ← Здесь проблема! Нет .distinct()

    # Выполняем запрос
    products_result = await session.scalars(stmt)
    products = [Product.model_validate(prod) for prod in products_result]
    
    return products
```

### Почему товары дублируются?

Давайте посмотрим на структуру базы данных:

```
Таблица products (товары):
┌────┬────────────┐
│ id │ name       │
├────┼────────────┤
│ 1  │ Плюмбус    │
└────┴────────────┘

Таблица tags (теги):
┌────┬──────────┐
│ id │ name     │
├────┼──────────┤
│ 1  │ Бытовые  │
│ 2  │ Популярные│
└────┴──────────┘

Таблица product_tag_association (связь M2M):
┌────────────┬────────┐
│ product_id │ tag_id │
├────────────┼────────┤
│ 1          │ 1      │  ← Плюмбус связан с "Бытовые"
│ 1          │ 2      │  ← Плюмбус связан с "Популярные"
└────────────┴────────┘
```

У товара "Плюмбус" **два тега**. Это связь **многие-ко-многим** (M2M — Many-to-Many).

Когда мы делаем `outerjoin(ProductORM.tags)`, SQLAlchemy генерирует такой SQL:

```sql
SELECT products.id, products.name, tags.name
FROM products
LEFT OUTER JOIN product_tag_association ON products.id = product_tag_association.product_id
LEFT OUTER JOIN tags ON tags.id = product_tag_association.tag_id
WHERE products.name LIKE '%Плю%'
```

Результат этого запроса:

```
┌────────────┬────────┬──────────────┐
│ product.id │ product.name │ tag.name     │
├────────────┼────────┼──────────────┤
│ 1          │ Плюмбус      │ Бытовые      │  ← Первая строка
│ 1          │ Плюмбус      │ Популярные   │  ← Вторая строка
└────────────┴────────┴──────────────┘
```

Видишь проблему? **Плюмбус появился дважды** — по разу на каждый тег!

SQLAlchemy честно возвращает обе строки, и мы получаем два объекта Product с одинаковым ID.

---

## ✅ Решение проблемы

Нужно добавить `.distinct()` в запрос. Это скажет SQL: "Убери дубликаты строк".

### Исправленный код

```python
async def products_get_with_filters(
    session: AsyncSession,
    search: Optional[str] = None,
    sort: Optional[str] = None,
    has_image: bool = False,
) -> list[Product]:
    """Получение продуктов с фильтрацией и сортировкой."""
    
    # Базовый запрос с загрузкой связей
    stmt = select(ProductORM).options(
        selectinload(ProductORM.category), 
        selectinload(ProductORM.tags)
    )

    # Применяем поиск, если указан
    if search:
        stmt = (
            stmt.outerjoin(ProductORM.category)
            .outerjoin(ProductORM.tags)
            .where(
                or_(
                    ProductORM.name.ilike(f"%{search}%"),
                    CategoryORM.name.ilike(f"%{search}%"),
                    TagORM.name.ilike(f"%{search}%"),
                )
            )
            .distinct()  # ← Добавили эту строку!
        )

    # Выполняем запрос
    products_result = await session.scalars(stmt)
    products = [Product.model_validate(prod) for prod in products_result]
    
    return products
```

### Как работает distinct()

Теперь SQL-запрос будет:

```sql
SELECT DISTINCT products.id, products.name, tags.name
FROM products
LEFT OUTER JOIN product_tag_association ON products.id = product_tag_association.product_id
LEFT OUTER JOIN tags ON tags.id = product_tag_association.tag_id
WHERE products.name LIKE '%Плю%'
```

**`DISTINCT`** говорит базе данных: "Убери повторяющиеся строки по всем столбцам".

Результат:

```
┌────────────┬──────────────┐
│ product.id │ product.name │
├────────────┼──────────────┤
│ 1          │ Плюмбус      │  ← Только одна строка!
└────────────┴──────────────┘
```

Теперь "Плюмбус" появится в списке товаров только один раз, даже если у него 10 тегов.

---

## 📊 Схема работы distinct()

```
БЕЗ distinct():
┌─────────────────────────────────────┐
│ JOIN products + tags                │
├─────────────────────────────────────┤
│ Плюмбус + Бытовые                   │
│ Плюмбус + Популярные                │
└─────────────────────────────────────┘
        ↓
SQLAlchemy.scalars()
        ↓
[Product(id=1, name="Плюмбус"),
 Product(id=1, name="Плюмбус")]  ← Дубликаты!


С distinct():
┌─────────────────────────────────────┐
│ JOIN products + tags                │
├─────────────────────────────────────┤
│ Плюмбус + Бытовые                   │
│ Плюмбус + Популярные                │
└─────────────────────────────────────┘
        ↓
DISTINCT (уникальные по products.id)
        ↓
┌─────────────────────────────────────┐
│ Плюмбус                             │  ← Одна строка
└─────────────────────────────────────┘
        ↓
SQLAlchemy.scalars()
        ↓
[Product(id=1, name="Плюмбус")]  ← Один товар!
```

---

## 🎯 Коммит 5: Обновление отдельной карточки товара

Теперь добавляем новую фичу: кнопку обновления в каждой карточке товара. При нажатии карточка обновится с актуальными данными из БД, **не перезагружая всю страницу**.

---

## 🆕 Создание нового эндпоинта

Нам нужен отдельный эндпоинт, который возвращает **только одну карточку товара** (а не всю страницу).

### Файл: `routes/pages.py` (дополнение)

```python
from fastapi import APIRouter, Request, Depends, HTTPException
from core.database import get_db_session, products_get_with_filters, product_get_by_id

@router.get("/product/{product_id}", include_in_schema=False)
async def get_product_card(
    request: Request,
    product_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Получение обновленной карточки товара по ID
    
    Используется для HTMX-обновления отдельной карточки 
    без перезагрузки страницы.
    """
    try:
        product = await product_get_by_id(session, product_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    return templates.TemplateResponse(
        "partials/product_card.html",
        {
            "request": request,
            "product": product,
        }
    )
```

### Разбор

#### 1. Path-параметр

```python
@router.get("/product/{product_id}")
async def get_product_card(product_id: int, ...):
```

**`{product_id}`** — это path-параметр. Часть URL становится переменной.

Примеры:

- `/product/1` → `product_id = 1`
- `/product/42` → `product_id = 42`
- `/product/abc` → Ошибка 422 (ожидается int, получено str)

#### 2. Получение товара

```python
product = await product_get_by_id(session, product_id)
```

**`product_get_by_id`** — это функция из CRUD, которая ищет товар по ID в базе данных.

Если товара нет → выбрасывается исключение.

#### 3. Обработка ошибок

```python
try:
    product = await product_get_by_id(session, product_id)
except Exception:
    raise HTTPException(status_code=404, detail="Товар не найден")
```

Если функция `product_get_by_id` выбрасывает исключение (товар не найден), мы превращаем его в **HTTP 404**.

FastAPI автоматически вернёт ответ:

```json
{
  "detail": "Товар не найден"
}
```

#### 4. Возврат partial

```python
return templates.TemplateResponse(
    "partials/product_card.html",
    {
        "request": request,
        "product": product,
    }
)
```

Обрати внимание: возвращаем **не всю страницу** (`index.html`), а только **фрагмент** (`partials/product_card.html`).

HTMX получит только HTML одной карточки, без шапки, футера и остального.

---

## 🎨 Добавление кнопки обновления в карточку

Теперь обновляем файл `templates/partials/product_card.html`.

### Файл: `templates/partials/product_card.html` (обновлённый)

```html
<div class="col" id="product-{{ product.id }}">
    <div class="card h-100 shadow-sm">
        {% if product.image_url %}
        <img src="{{ product.image_url }}" class="card-img-top" alt="{{ product.name }}" style="height: 200px; object-fit: cover;">
        {% else %}
        <div class="card-img-top bg-secondary d-flex align-items-center justify-content-center" style="height: 200px;">
            <span class="text-white fs-1">📦</span>
        </div>
        {% endif %}
        
        <div class="card-body d-flex flex-column">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <h5 class="card-title mb-0">{{ product.name }}</h5>
                <button 
                    class="btn btn-sm btn-outline-secondary border-0 p-1"
                    hx-get="/product/{{ product.id }}"
                    hx-target="#product-{{ product.id }}"
                    hx-swap="outerHTML"
                    title="Обновить карточку товара"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-arrow-clockwise" viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2z"/>
                        <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466"/>
                    </svg>
                </button>
            </div>
            <p class="card-text text-muted small flex-grow-1">
                {{ product.description[:100] }}{% if product.description|length > 100 %}...{% endif %}
            </p>
            
            <div class="mt-auto">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="badge bg-primary">{{ product.price_credits }} ₽</span>
                    {% if product.price_shmeckles %}
                    <span class="badge bg-success">{{ product.price_shmeckles }} Sh</span>
                    {% endif %}
                </div>
                
                <button class="btn btn-sm btn-outline-primary w-100">
                    🛒 В корзину
                </button>
            </div>
        </div>
    </div>
</div>
```

### Что изменилось

#### 1. Уникальный ID для карточки

```html
<div class="col" id="product-{{ product.id }}">
```

Теперь каждая карточка имеет уникальный `id`. Например:

- Плюмбус → `id="product-1"`
- Портальная пушка → `id="product-2"`

Это нужно, чтобы HTMX мог точно найти и заменить нужную карточку.

#### 2. Кнопка обновления

```html
<button 
    class="btn btn-sm btn-outline-secondary border-0 p-1"
    hx-get="/product/{{ product.id }}"
    hx-target="#product-{{ product.id }}"
    hx-swap="outerHTML"
    title="Обновить карточку товара"
>
    <svg>...</svg>  <!-- Иконка стрелки по кругу -->
</button>
```

**`hx-get="/product/{{ product.id }}"`** — при клике отправить GET-запрос на `/product/1` (для Плюмбуса).

**`hx-target="#product-{{ product.id }}"`** — заменить элемент с `id="product-1"`.

**`hx-swap="outerHTML"`** — заменить весь элемент целиком (включая внешний `<div>`).

#### 3. SVG-иконка

```html
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-arrow-clockwise" viewBox="0 0 16 16">
    <path fill-rule="evenodd" d="..."/>
    <path d="..."/>
</svg>
```

Это иконка **"стрелка по часовой стрелке"** из Bootstrap Icons. Означает "обновить", "перезагрузить".

Мы используем SVG вместо emoji или текста, потому что:

- SVG масштабируется без потери качества
- Можно менять цвет через CSS (`fill="currentColor"`)
- Выглядит профессионально

---

## 🎯 Полная схема работы обновления карточки

```
1. Пользователь кликает на кнопку ↻ в карточке Плюмбуса (id=1)
    ↓
2. HTMX видит hx-get="/product/1"
    ↓
3. HTMX отправляет: GET /product/1
    ↓
4. FastAPI вызывает get_product_card(request, product_id=1, session)
    ↓
5. Функция product_get_by_id(session, 1) → SELECT * FROM products WHERE id = 1
    ↓
6. База данных возвращает актуальные данные Плюмбуса
    ↓
7. FastAPI рендерит templates/partials/product_card.html с product=Плюмбус
    ↓
8. FastAPI возвращает HTML только одной карточки:
    <div class="col" id="product-1">
        <div class="card">...</div>
    </div>
    ↓
9. HTMX получает HTML карточки
    ↓
10. HTMX находит элемент #product-1 на странице
    ↓
11. HTMX заменяет старую карточку на новую (hx-swap="outerHTML")
    ↓
12. Пользователь видит обновлённую карточку Плюмбуса
```

---

## 💡 Зачем это нужно?

Представь ситуацию:

1. Админ меняет цену Плюмбуса в админ-панели: `100 ₽` → `150 ₽`
2. Пользователь смотрит каталог, видит старую цену `100 ₽`
3. Пользователь нажимает кнопку обновления ↻
4. Карточка обновляется → видит новую цену `150 ₽`
5. **Вся страница не перезагружалась!** Позиция скролла не сбросилась, поле поиска не очистилось.

Это намного удобнее, чем перезагружать всю страницу (F5).

---

## 🎨 Визуальная схема структуры карточки

```
┌────────────────────────────────────────┐
│ <div id="product-1">                   │ ← Обёртка с уникальным ID
│  ┌──────────────────────────────────┐  │
│  │ <div class="card">               │  │
│  │  ┌────────────────────────────┐  │  │
│  │  │ 📦 или <img>               │  │  │ ← Картинка товара
│  │  └────────────────────────────┘  │  │
│  │  ┌────────────────────────────┐  │  │
│  │  │ Плюмбус             [↻]    │  │  │ ← Название + кнопка обновления
│  │  ├────────────────────────────┤  │  │
│  │  │ Описание товара...         │  │  │ ← Описание (обрезано до 100 символов)
│  │  ├────────────────────────────┤  │  │
│  │  │ [100 ₽] [50 Sh]            │  │  │ ← Цены
│  │  ├────────────────────────────┤  │  │
│  │  │ [🛒 В корзину]             │  │  │ ← Кнопка добавления в корзину
│  │  └────────────────────────────┘  │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
```

При клике на `[↻]`:

1. Запрос → `/product/1`
2. Ответ → новый HTML карточки
3. Замена → только этот `<div id="product-1">` целиком

Остальные карточки **не трогаются**!

---

## ✅ Что мы получили после коммитов 4-5

### Коммит 4 (Bugfix)

- ✅ Исправлено дублирование товаров в результатах поиска
- ✅ Добавлен `.distinct()` в SQL-запрос
- ✅ Теперь товары с несколькими тегами показываются один раз

### Коммит 5 (Feature)

- ✅ Создан эндпоинт `/product/{id}` для получения одной карточки
- ✅ Добавлена кнопка обновления (иконка ↻) в каждую карточку
- ✅ Каждая карточка имеет уникальный `id="product-{id}"`
- ✅ Обновление карточки происходит без перезагрузки страницы
- ✅ Используется HTMX для замены только нужной карточки

---

## 🎓 Ключевые концепции, которые мы изучили

### 1. **M2M связи и JOIN**

Когда у одного товара много тегов, `JOIN` создаёт несколько строк. Нужен `DISTINCT` для устранения дубликатов.

### 2. **Path-параметры в FastAPI**

`/product/{product_id}` → переменная в URL, автоматически парсится и валидируется.

### 3. **Partials и их переиспользование**

Один HTML-фрагмент можно использовать многократно (в списке товаров и отдельно для обновления).

### 4. **HTMX: точечные обновления**

Вместо перезагрузки всей страницы обновляем только нужный элемент.

### 5. **Уникальные ID в шаблонах**

`id="product-{{ product.id }}"` позволяет HTMX точно находить и заменять элементы.

---

## 🚀 Финальная архитектура

```
Пользователь взаимодействует со страницей
            ↓
┌───────────────────────────────────────────┐
│ templates/index.html                      │
│ ├─ Поле поиска (HTMX)                     │
│ │   → GET / с параметром search           │
│ │   → Обновляет #product-grid             │
│ ├─ Список товаров (#product-grid)         │
│ │   ├─ product_card.html (id=product-1)   │
│ │   │   └─ Кнопка ↻ → GET /product/1      │
│ │   │      → Обновляет #product-1         │
│ │   ├─ product_card.html (id=product-2)   │
│ │   └─ ...                                │
└───────────────────────────────────────────┘
            ↓
┌───────────────────────────────────────────┐
│ routes/pages.py                           │
│ ├─ GET / → index()                        │
│ │   ├─ Получает товары из БД              │
│ │   ├─ Фильтрует по search (если есть)    │
│ │   └─ Рендерит index.html                │
│ ├─ GET /product/{id} → get_product_card() │
│ │   ├─ Получает один товар из БД          │
│ │   └─ Рендерит product_card.html         │
└───────────────────────────────────────────┘
            ↓
┌───────────────────────────────────────────┐
│ core/database.py                          │
│ ├─ products_get_with_filters()            │
│ │   ├─ SELECT с JOIN и фильтрами          │
│ │   └─ .distinct() для устранения дублей  │
│ ├─ product_get_by_id()                    │
│ │   └─ SELECT WHERE id = ?                │
└───────────────────────────────────────────┘
            ↓
┌───────────────────────────────────────────┐
│ База данных SQLite                        │
│ ├─ products                               │
│ ├─ categories                             │
│ ├─ tags                                   │
│ └─ product_tag_association (M2M)          │
└───────────────────────────────────────────┘
```

---

## 📝 Важные выводы

1. **HTMX — это не магия**, это просто атрибуты HTML, которые говорят: "Когда происходит событие X, отправь запрос Y и обнови элемент Z".

2. **Jinja2 — это Python в HTML**. Циклы, условия, переменные — всё работает как в обычном Python, только в HTML-шаблонах.

3. **Partials — это функции для HTML**. Вынес общий код в отдельный файл — используешь везде. Изменил в одном месте — изменилось везде.

4. **FastAPI автоматически парсит параметры**: из URL (`/product/{id}`), из query (`?search=...`), из форм, из JSON. Ты просто указываешь типы в функции.

5. **Каждый коммит решает одну задачу**: настройка шаблонов → каталог → поиск → багфикс → обновление. Маленькие шаги, чёткая история изменений.

---

Поздравляю! Теперь у тебя есть полноценный каталог товаров с живым поиском и обновлением карточек, написанный на чистом Python + HTMX! 🎉🚀
