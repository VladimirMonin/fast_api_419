# 📚 Занятие №1: Jinja2 + HTMX (Часть 4)

## Коммит 6: Out-of-Band (OOB) Swaps — обновление нескольких элементов

---

## 🎯 Проблема: счётчик не обновляется при поиске

После реализации живого поиска мы обнаружили UX-проблему:

```
Пользователь видит на странице:
┌────────────────────────────────────┐
│ Найдено товаров: 20                │  ← Старое значение!
│                                    │
│ [Поиск: "Плюм"]                    │
│                                    │
│ ┌────────────┐                     │
│ │  Плюмбус   │                     │  ← Только 1 товар
│ └────────────┘                     │
└────────────────────────────────────┘
```

Когда пользователь фильтрует товары, HTMX обновляет только `#product-grid` (список товаров), но **счётчик остаётся прежним** — показывает 20, хотя найден только 1 товар.

### Почему так происходит?

Посмотрим на наш HTMX-запрос:

```html
<input 
    hx-get="/"
    hx-target="#product-grid"
    hx-select="#product-grid"
    hx-swap="outerHTML"
>
```

**`hx-target="#product-grid"`** — заменяем только элемент с `id="product-grid"`.

Счётчик (`<p>Найдено товаров: {{ products|length }}</p>`) находится **вне** этого элемента, поэтому не обновляется.

---

## 💡 Решение: Out-of-Band Swaps

**Out-of-Band (OOB) Swaps** — это возможность HTMX обновлять **несколько элементов** в разных частях страницы **одним запросом**.

Идея простая:

1. Сервер возвращает HTML с **основным** элементом (который попадёт в target)
2. Плюс **дополнительные** элементы с атрибутом `hx-swap-oob="true"`
3. HTMX автоматически находит эти элементы по ID и заменяет их

---

## 🛠️ Реализация

### Шаг 1: Создаём partial для счётчика

Выносим счётчик товаров в отдельный файл с **важными атрибутами**:

#### Файл: `templates/partials/product_count.html`

```html
<p id="product-count" class="text-muted mb-0 mt-2" hx-swap-oob="true">
    Найдено товаров: <strong>{{ products|length }}</strong>
</p>
```

### Разбор атрибутов

**`id="product-count"`** — уникальный ID элемента. HTMX будет искать элемент с таким же ID на странице.

**`hx-swap-oob="true"`** — это магический атрибут! Он говорит HTMX:
> "Привет! Я не часть основного ответа. Найди меня на странице по ID и замени меня целиком!"

**OOB** расшифровывается как **Out-of-Band**, то есть "вне полосы", "за пределами основного канала". Это элемент, который обновляется **дополнительно**, не в target.

---

### Шаг 2: Используем partial в index.html

Обновляем главную страницу:

#### Файл: `templates/index.html` (изменённая часть)

```html
<!-- Поиск товаров с HTMX -->
<div class="row mb-4">
    <div class="col-md-6 col-lg-4">
        <input 
            type="text" 
            class="form-control" 
            placeholder="🔍 Поиск товаров..."
            name="search"
            hx-get="/"
            hx-trigger="keyup changed delay:500ms"
            hx-target="#product-grid"
            hx-select="#product-grid"
            hx-swap="outerHTML"
        >
        <small class="text-muted">Начните вводить название товара</small>
    </div>
    <div class="col-md-6 col-lg-8">
        {% include "partials/product_count.html" %}
    </div>
</div>
```

### Что изменилось

#### Было

```html
<p class="text-muted mb-0 mt-2">
    Найдено товаров: <strong>{{ products|length }}</strong>
</p>
```

#### Стало

```html
{% include "partials/product_count.html" %}
```

Теперь счётчик подключается через `include`, что означает:

1. Jinja2 вставляет содержимое `product_count.html` сюда
2. У счётчика есть `id="product-count"`
3. У счётчика есть `hx-swap-oob="true"`

---

## 🎯 Как это работает

Давайте пошагово разберём, что происходит при поиске:

```
1. Пользователь вводит "Плюм" в поле поиска
    ↓
2. HTMX ждёт 500ms (debounce)
    ↓
3. HTMX отправляет: GET /?search=Плюм
    ↓
4. FastAPI вызывает index(request, session, search="Плюм")
    ↓
5. products_get_with_filters(session, search="Плюм") → [Плюмбус]
    ↓
6. FastAPI рендерит templates/index.html с products=[Плюмбус]
    ↓
7. Jinja2 генерирует HTML:
   ┌──────────────────────────────────────────────┐
   │ <div id="product-grid">                      │  ← Основной контент
   │   <div class="col">                          │
   │     <div class="card">Плюмбус</div>          │
   │   </div>                                     │
   │ </div>                                       │
   │                                              │
   │ <p id="product-count" hx-swap-oob="true">    │  ← OOB элемент!
   │   Найдено товаров: <strong>1</strong>       │
   │ </p>                                         │
   └──────────────────────────────────────────────┘
    ↓
8. HTMX получает HTML
    ↓
9. HTMX видит hx-select="#product-grid" → вырезает #product-grid
    ↓
10. HTMX НО ТАКЖЕ видит элемент с hx-swap-oob="true"!
    ↓
11. HTMX делает ДВА действия:
    
    А) Основная замена (как обычно):
       target="#product-grid" → заменяет список товаров
    
    Б) OOB замена (дополнительно):
       Ищет на странице элемент с id="product-count"
       → заменяет его целиком
    ↓
12. Пользователь видит обновлённый список И обновлённый счётчик!
```

---

## 📊 Визуальная схема OOB

### ДО запроса (страница с 20 товарами)

```
┌──────────────────────────────────────────┐
│ <p id="product-count">                   │
│   Найдено товаров: 20                    │  ← Старый счётчик
│ </p>                                     │
├──────────────────────────────────────────┤
│ [Поиск: ________]                        │
├──────────────────────────────────────────┤
│ <div id="product-grid">                  │
│   <div>Товар 1</div>                     │
│   <div>Товар 2</div>                     │
│   ... (20 товаров)                       │  ← Старый список
│ </div>                                   │
└──────────────────────────────────────────┘
```

### Пользователь вводит "Плюм"

```
HTMX отправляет: GET /?search=Плюм
         ↓
FastAPI возвращает HTML:
┌──────────────────────────────────────────┐
│ <div id="product-grid">                  │
│   <div>Плюмбус</div>                     │  ← Новый список (1 товар)
│ </div>                                   │
│                                          │
│ <p id="product-count" hx-swap-oob="true">│
│   Найдено товаров: 1                     │  ← Новый счётчик
│ </p>                                     │
└──────────────────────────────────────────┘
```

### HTMX обрабатывает ответ

```
Шаг 1: Основная замена (hx-target)
┌──────────────────────────────────────────┐
│ <p id="product-count">                   │
│   Найдено товаров: 20                    │  ← Пока не тронут
│ </p>                                     │
├──────────────────────────────────────────┤
│ [Поиск: Плюм____]                        │
├──────────────────────────────────────────┤
│ <div id="product-grid">                  │
│   <div>Плюмбус</div>                     │  ✅ Заменён!
│ </div>                                   │
└──────────────────────────────────────────┘

Шаг 2: OOB замена (hx-swap-oob)
┌──────────────────────────────────────────┐
│ <p id="product-count">                   │
│   Найдено товаров: 1                     │  ✅ Тоже заменён!
│ </p>                                     │
├──────────────────────────────────────────┤
│ [Поиск: Плюм____]                        │
├──────────────────────────────────────────┤
│ <div id="product-grid">                  │
│   <div>Плюмбус</div>                     │
│ </div>                                   │
└──────────────────────────────────────────┘
```

### ПОСЛЕ замены

```
┌──────────────────────────────────────────┐
│ <p id="product-count">                   │
│   Найдено товаров: 1                     │  ← Обновлено! 🎉
│ </p>                                     │
├──────────────────────────────────────────┤
│ [Поиск: Плюм____]                        │
├──────────────────────────────────────────┤
│ <div id="product-grid">                  │
│   <div>Плюмбус</div>                     │  ← Обновлено! 🎉
│ </div>                                   │
└──────────────────────────────────────────┘
```

---

## 🔑 Ключевые моменты OOB

### 1. Атрибут hx-swap-oob

```html
<div id="notifications" hx-swap-oob="true">
    У вас 5 новых уведомлений
</div>
```

**`hx-swap-oob="true"`** — это как метка: "Я OOB-элемент, найди меня на странице и замени!"

Можно также указать стратегию замены:

- `hx-swap-oob="innerHTML"` — заменить только содержимое
- `hx-swap-oob="outerHTML"` — заменить весь элемент (по умолчанию при `true`)
- `hx-swap-oob="beforebegin"` — вставить перед элементом
- `hx-swap-oob="afterend"` — вставить после элемента

### 2. Важность ID

OOB работает **только с элементами, у которых есть ID**. HTMX ищет на странице элемент с таким же ID.

```html
<!-- В ответе сервера: -->
<span id="cart-count" hx-swap-oob="true">3</span>

<!-- На странице должен быть: -->
<span id="cart-count">0</span>

<!-- HTMX найдёт по ID и заменит -->
```

### 3. Множественные OOB элементы

Можно обновлять **сколько угодно** элементов одним запросом:

```html
<!-- Ответ сервера: -->
<div id="product-grid">
    <!-- товары -->
</div>

<span id="product-count" hx-swap-oob="true">1</span>
<span id="cart-total" hx-swap-oob="true">$150</span>
<div id="notifications" hx-swap-oob="true">
    <p>Новое сообщение!</p>
</div>
```

HTMX обновит:

1. `#product-grid` (основной target)
2. `#product-count` (OOB)
3. `#cart-total` (OOB)
4. `#notifications` (OOB)

**Четыре элемента одним запросом!** 🚀

---

## 🎓 Практические сценарии использования OOB

### Сценарий 1: Добавление товара в корзину

```html
<!-- Кнопка на карточке товара: -->
<button 
    hx-post="/cart/add/{{ product.id }}"
    hx-target="#cart-items"
>
    🛒 В корзину
</button>

<!-- Сервер возвращает: -->
<div id="cart-items">
    <!-- обновлённый список товаров в корзине -->
</div>

<span id="cart-count" hx-swap-oob="true">3</span>  ← Счётчик в шапке
<span id="cart-total" hx-swap-oob="true">$450</span>  ← Сумма
<div id="notification" hx-swap-oob="true">
    <div class="alert">Товар добавлен в корзину!</div>
</div>
```

**Один клик** → обновляются:

- список товаров в корзине
- счётчик товаров (в шапке сайта)
- общая сумма
- всплывающее уведомление

### Сценарий 2: Лайк поста в соцсети

```html
<button hx-post="/post/123/like" hx-target="#like-button-123">
    ❤️ Лайк
</button>

<!-- Сервер возвращает: -->
<button id="like-button-123">
    💙 Убрать лайк
</button>

<span id="like-count-123" hx-swap-oob="true">42</span>
<div id="user-stats" hx-swap-oob="true">
    Вы поставили 156 лайков
</div>
```

### Сценарий 3: Фильтрация + сортировка

```html
<select hx-get="/products" hx-target="#products">
    <option value="price_asc">По цене ↑</option>
    <option value="price_desc">По цене ↓</option>
</select>

<!-- Сервер возвращает: -->
<div id="products">
    <!-- отсортированные товары -->
</div>

<div id="sort-info" hx-swap-oob="true">
    Сортировка: по возрастанию цены
</div>
<span id="product-count" hx-swap-oob="true">15</span>
```

---

## ⚠️ Важные ограничения и особенности

### 1. OOB элементы должны быть в корне ответа

❌ **Неправильно:**

```html
<div id="wrapper">
    <div id="products">...</div>
    <span id="count" hx-swap-oob="true">5</span>  ← Внутри wrapper!
</div>
```

✅ **Правильно:**

```html
<div id="products">...</div>
<span id="count" hx-swap-oob="true">5</span>  ← На уровне корня!
```

### 2. ID должен существовать на странице

Если на странице нет элемента с таким ID, HTMX **проигнорирует** OOB-элемент (не будет ошибки).

### 3. hx-select работает только для target

```html
<input 
    hx-get="/"
    hx-target="#products"
    hx-select="#products"  ← Вырезает из ответа #products
>
```

**`hx-select`** НЕ влияет на OOB элементы! Они всегда обрабатываются, даже если не попадают в select.

---

## 📈 Преимущества OOB перед альтернативами

### Альтернатива 1: Несколько запросов

**Без OOB:**

```javascript
// JavaScript код
fetch('/search?q=Плюм')
    .then(r => r.text())
    .then(html => {
        document.getElementById('products').innerHTML = html;
    });

fetch('/count?q=Плюм')
    .then(r => r.text())
    .then(count => {
        document.getElementById('count').innerText = count;
    });
```

❌ Два запроса на сервер
❌ Нужен JavaScript
❌ Возможны race conditions

**С OOB:**

```html
<input hx-get="/search" hx-target="#products">
```

✅ Один запрос
✅ Без JavaScript
✅ Атомарное обновление

### Альтернатива 2: Обновление всей страницы

**Без OOB:**

```html
<input hx-get="/" hx-target="body" hx-swap="innerHTML">
```

❌ Перерисовка всего DOM
❌ Потеря состояния (фокус, скролл)
❌ Медленно

**С OOB:**

✅ Точечное обновление
✅ Сохранение состояния
✅ Быстро

---

## 🎯 Итоговая архитектура с OOB

```
index.html
├─ Поиск (input)
│  └─ hx-get="/"
│     hx-target="#product-grid"
│     hx-select="#product-grid"
│
├─ Счётчик
│  └─ {% include "partials/product_count.html" %}
│     └─ id="product-count"
│        hx-swap-oob="true"
│
└─ Список товаров
   └─ id="product-grid"

При запросе GET /?search=Плюм:
    ↓
FastAPI рендерит index.html
    ↓
Jinja2 вставляет:
    - #product-grid (новый список)
    - partials/product_count.html (новый счётчик с OOB)
    ↓
HTMX получает ответ:
    1. #product-grid → заменяет (основной target)
    2. #product-count с hx-swap-oob → тоже заменяет (OOB)
    ↓
Обновлены ОБА элемента одним запросом! 🎉
```

---

## ✅ Что мы получили после коммита 6

- ✅ Счётчик товаров обновляется синхронно со списком
- ✅ Использован механизм Out-of-Band Swaps
- ✅ Создан переиспользуемый partial `product_count.html`
- ✅ Один HTTP-запрос обновляет два элемента
- ✅ Отличный UX — пользователь видит актуальные данные везде

---

## 🎓 Ключевые выводы

1. **OOB Swaps** — это мощный инструмент для обновления нескольких элементов одним запросом
2. **`hx-swap-oob="true"`** — магический атрибут, который делает элемент "внеполосным"
3. **ID обязателен** — HTMX ищет OOB-элементы по ID
4. **Partials + OOB** — отличная комбинация для переиспользуемых обновляемых компонентов
5. **Без JavaScript** — всё работает на чистом HTML + атрибутах HTMX

Теперь наш каталог товаров работает как полноценное SPA-приложение, но написан на чистом Python + HTML! 🚀

---

## 🔗 Полезные ссылки

- [HTMX Out of Band Swaps Documentation](https://htmx.org/attributes/hx-swap-oob/)
- [HTMX Examples: Active Search with OOB](https://htmx.org/examples/active-search/)
- [Bootstrap Grid System](https://getbootstrap.com/docs/5.3/layout/grid/)
