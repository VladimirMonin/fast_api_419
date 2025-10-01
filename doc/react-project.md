# Пакет исходного кода проекта: react-project

## `index.html`

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>react-router-419</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>

```

## `package.json`

```json
{
  "name": "react-router-419",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.1.1",
    "react-dom": "^19.1.1",
    "react-router-dom": "^7.9.2"
  },
  "devDependencies": {
    "@eslint/js": "^9.36.0",
    "@types/react": "^19.1.13",
    "@types/react-dom": "^19.1.9",
    "@vitejs/plugin-react": "^5.0.3",
    "eslint": "^9.36.0",
    "eslint-plugin-react-hooks": "^5.2.0",
    "eslint-plugin-react-refresh": "^0.4.20",
    "globals": "^16.4.0",
    "typescript": "~5.8.3",
    "typescript-eslint": "^8.44.0",
    "vite": "^7.1.7"
  }
}

```

## `src/App.css`

```css
/* src/index.css */

body {
  font-family: sans-serif;
  margin: 0;
  background-color: #f0f2f5;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.products-list {
  display: flex;
  flex-wrap: wrap;
  gap: 20px; /* Расстояние между карточками */
  list-style: none;
  padding: 0;
}

li.product-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  background-color: #fff;
  width: calc(25% - 15px); /* 4 карточки в ряд с учетом gap */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
  display: block;
}

.product-card a {
  text-decoration: none;
  color: #333;
}

.product-card button {
  margin-top: 10px;
  padding: 10px 15px;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.product-card button:hover {
  background-color: #218838;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transform: translateY(-2px);
  transition: all 0.2s ease;
}

.detail {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Стили для формы поиска */
.search-container {
  margin-bottom: 30px;
  display: flex;
  justify-content: center;
}

.search-input {
  width: 100%;
  max-width: 500px;
  padding: 12px 16px;
  font-size: 16px;
  border: 2px solid #ddd;
  border-radius: 8px;
  background-color: #fff;
  outline: none;
  transition: border-color 0.3s ease;
}

.search-input:focus {
  border-color: #28a745;
  box-shadow: 0 0 0 3px rgba(40, 167, 69, 0.1);
}

/* Стили для кнопок в карточке товара */
.product-buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 15px;
}

.details-button,
.add-to-cart-button {
  padding: 10px 15px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.details-button {
  background-color: #6c757d;
  color: white;
}

.details-button a {
  color: white;
  text-decoration: none;
}

.details-button:hover {
  background-color: #5a6268;
  transform: translateY(-2px);
}

.add-to-cart-button {
  background-color: #28a745;
  color: white;
}

.add-to-cart-button:hover {
  background-color: #218838;
  transform: translateY(-2px);
}

/* Стили для иконки корзины в навигации */
.cart-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 5px;
}

.cart-counter {
  background-color: #dc3545;
  color: white;
  border-radius: 50%;
  padding: 2px 6px;
  font-size: 12px;
  font-weight: bold;
  min-width: 18px;
  text-align: center;
}

/* Стили для страницы корзины */
.empty-cart {
  text-align: center;
  padding: 60px 20px;
}

.empty-cart p {
  font-size: 18px;
  margin-bottom: 30px;
  color: #666;
}

.continue-shopping-link {
  display: inline-block;
  padding: 12px 24px;
  background-color: #28a745;
  color: white;
  text-decoration: none;
  border-radius: 5px;
  transition: background-color 0.2s ease;
}

.continue-shopping-link:hover {
  background-color: #218838;
}

.cart-items {
  margin-bottom: 30px;
}

.cart-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 15px;
  background-color: white;
}

.item-info h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
}

.item-info .item-description {
  color: #666;
  margin: 5px 0;
}

.item-info .item-price {
  color: #28a745;
  font-weight: bold;
  margin: 5px 0 0 0;
}

.item-controls {
  display: flex;
  align-items: center;
  gap: 20px;
}

.quantity-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.quantity-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #ddd;
  background-color: white;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.2s ease;
}

.quantity-btn:hover:not(:disabled) {
  background-color: #f8f9fa;
  border-color: #28a745;
}

.quantity-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.quantity {
  font-weight: bold;
  min-width: 40px;
  text-align: center;
}

.item-total {
  font-size: 18px;
  min-width: 120px;
  text-align: right;
}

.remove-btn {
  padding: 8px 16px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.remove-btn:hover {
  background-color: #c82333;
}

.cart-summary {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.total-section {
  text-align: center;
  margin-bottom: 20px;
}

.total-section h3 {
  margin: 0 0 20px 0;
  font-size: 24px;
  color: #28a745;
}

.cart-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-bottom: 20px;
}

.clear-cart-btn,
.checkout-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.2s ease;
}

.clear-cart-btn {
  background-color: #6c757d;
  color: white;
}

.clear-cart-btn:hover {
  background-color: #5a6268;
}

.checkout-btn {
  background-color: #28a745;
  color: white;
}

.checkout-btn:hover {
  background-color: #218838;
}

```

## `src/components/MainLayout.css`

```css
/* src/components/MainLayout.css */
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  background-color: #2c3e50;
  padding: 1rem 0;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.app-header nav {
  display: flex;
  gap: 2rem;
}

.app-header nav a {
  color: white;
  text-decoration: none;
  font-size: 1.1rem;
  font-weight: bold;
}

/* Стили для активного пункта меню */

.app-header nav a.active {
  border-bottom: 2px solid #ebcd69;
  color: #ebcd69;
}
/* Hover */
.app-header nav a:hover {
  color: #ebcd69;
  transition: color 0.5s;
}

.app-content {
  /* Заставляет основной контент занимать все доступное пространство */
  flex-grow: 1;
}

.app-footer {
  background-color: #34495e;
  color: #ecf0f1;
  padding: 1.5rem 0;
  text-align: center;
  /* Прижимает подвал к низу страницы, если контента мало */
  margin-top: auto;
}

```

## `src/components/ProductNotFoundPage.css`

```css
/*  */
.container-product-not-found {
  text-align: center;
  margin-top: 50px;
}

.container-product-not-found button {
  margin-top: 20px;
  padding: 10px 20px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.container-product-not-found button a {
  color: white;
  text-decoration: none;
}

.container-product-not-found button:hover {
  background-color: #2980b9;
}

.container-product-not-found h1 {
  font-size: 3rem;
  color: #e74c3c;
}
```

## `src/hooks/useAuth.ts`

```ts
// src/hooks/useAuth.ts
import { useState } from 'react';

// Имитируем состояние аутентификации
export const useAuth = () => {
  // По умолчанию пользователь не авторизован
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const login = () => {
    // В реальном приложении здесь был бы запрос к API
    setIsLoggedIn(true);
  };

  const logout = () => {
    setIsLoggedIn(false);
  };

  return { isLoggedIn, login, logout };
};

```

