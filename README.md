# 🌟 Task Manager Bot

Task Manager Bot — это умный Telegram-бот для управления задачами! 📝 Он поможет тебе планировать дела, отслеживать прогресс и достигать целей. 🚀

## 🔥 Основные возможности
✅ **Добавление задач** с темой, приоритетом и дедлайном  
❌ **Удаление задач** одним кликом  
📅 **Просмотр списка всех задач**  
🚨 **Фильтр по высокоприоритетным задачам**  
📊 **Статистика выполнения**  

---

## 🛠 Установка и запуск
### 📌 Требования
- 🐍 **Python 3.8+**
- 📦 **Библиотеки**: `pyTelegramBotAPI`, `sqlite3`

### ⚡ Установка зависимостей
```bash
pip install pyTelegramBotAPI
```

### 🚀 Запуск бота
1. **Создайте файл `config.py`** и добавьте туда ваш Telegram API Token:
```python
TOKEN = "ВАШ_ТОКЕН"
```
2. **Запустите бота:**
```bash
python bot.py
```

---

## 📜 Команды бота
- 🎉 `/start` — Начало работы с ботом  
- ➕ `/add_task` — Добавить задачу  
- 🗑 `/delete_task` — Удалить задачу  
- ✅ `/mark_done` — Отметить задачу как выполненную  
- 📋 `/show` — Показать все задачи  
- 🔥 `/show_high_priority` — Показать важные задачи  
- 📊 `/stats` — Показать статистику выполнения  

---

## 🗄 Структура базы данных
📂 База данных (`database.db`) хранит задачи в следующем формате:
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    theme TEXT,
    priority TEXT CHECK(priority IN ('низкий', 'средний', 'высокий')) DEFAULT 'средний',
    deadline TEXT,
    status TEXT DEFAULT 'pending',
    user_id INTEGER NOT NULL
);
```

---

💡 **Развивай продуктивность вместе с Task Manager Bot!** 🔥
