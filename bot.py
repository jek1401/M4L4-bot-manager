import sqlite3
import threading
import time
from datetime import datetime
from telebot import TeleBot
import telebot

class TaskManager:
    def __init__(self, database):
        self.database = database
        self.create_table()

    def create_table(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            theme TEXT,
            priority TEXT CHECK(priority IN ('низкий', 'средний', 'высокий')) DEFAULT 'средний',
            deadline TEXT,
            status TEXT DEFAULT 'pending',
            user_id INTEGER NOT NULL
            )""")
            conn.commit()

    def add_task(self, user_id, name, theme, priority, deadline):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute("INSERT INTO tasks (name, theme, priority, deadline, user_id) VALUES (?, ?, ?, ?, ?)", (name, theme, priority, deadline, user_id))
            conn.commit()

    def delete_task(self, task_name, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute("DELETE FROM tasks WHERE name = ? AND user_id = ?", (task_name, user_id))
            conn.commit()

    def mark_task_done(self, task_name, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute("UPDATE tasks SET status = 'done' WHERE name = ? AND user_id = ?", (task_name, user_id))
            conn.commit()

    def show_tasks(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT name, theme, priority, deadline, status FROM tasks WHERE user_id = ?", (user_id,))
            return cur.fetchall()
    
    def show_high_priority_tasks(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM tasks WHERE user_id = ? AND priority = 'высокий'", (user_id,))
            return cur.fetchall()

    def get_statistics(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'done'", (user_id,))
            completed = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'pending'", (user_id,))
            pending = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,))
            total = cur.fetchone()[0]
            return completed, pending, total

bot = TeleBot("TOKEN")
task_manager = TaskManager("database.db")

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, """Привет! Я бот-менеджер задач
Помогу тебе сохранить твои задачи!

/add_task - добавить новую задачу
/delete_task - удалить задачу
/mark_done - отметить задачу как выполненную
/show - показать все задачи
/show_high_priority - показать только важные задачи
/stats - статистика выполнения""")

@bot.message_handler(commands=['add_task'])
def add_task_command(message):
    bot.send_message(message.chat.id, "Введите название задачи:")
    bot.register_next_step_handler(message, get_task_name)

def get_task_name(message):
    user_id = message.from_user.id
    task_name = message.text
    bot.send_message(message.chat.id, "Введите тематику задачи:")
    bot.register_next_step_handler(message, lambda msg: get_task_theme(msg, user_id, task_name))

def get_task_theme(message, user_id, task_name):
    theme = message.text
    bot.send_message(message.chat.id, "Выберите приоритет (низкий, средний, высокий):")
    bot.register_next_step_handler(message, lambda msg: get_task_priority(msg, user_id, task_name, theme))

def get_task_priority(message, user_id, task_name, theme):
    priority = message.text.lower()
    if priority not in ['низкий', 'средний', 'высокий']:
        bot.send_message(message.chat.id, "Некорректный приоритет. Используйте: низкий, средний или высокий.")
        return
    bot.send_message(message.chat.id, "Введите дату и время дедлайна (ГГГГ-ММ-ДД ЧЧ:ММ):")
    bot.register_next_step_handler(message, lambda msg: save_task(msg, user_id, task_name, theme, priority))

def save_task(message, user_id, task_name, theme, priority):
    deadline = message.text
    task_manager.add_task(user_id, task_name, theme, priority, deadline)
    bot.send_message(message.chat.id, "Задача добавлена")

@bot.message_handler(commands=['delete_task'])
def delete_task_command(message):
    bot.send_message(message.chat.id, "Введите имя задачи, которую хотите удалить:")
    bot.register_next_step_handler(message, delete_task)

def delete_task(message):
    user_id = message.from_user.id
    task_name = message.text
    task_manager.delete_task(task_name, user_id)
    bot.send_message(message.chat.id, "Задача удалена")

@bot.message_handler(commands=['show'])
def show_tasks(message):
    user_id = message.from_user.id
    tasks = task_manager.show_tasks(user_id)
    if tasks:
        response = "\n".join([f"{name} (Тема: {theme}, Приоритет: {priority}, Дедлайн: {deadline}, Статус: {status})" for name, theme, priority, deadline, status in tasks])
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "Задач нет")

@bot.message_handler(commands=['show_high_priority'])
def show_high_priority_tasks(message):
    user_id = message.from_user.id
    tasks = task_manager.show_high_priority_tasks(user_id)
    if tasks:
        response = "\n".join([task[0] for task in tasks])
        bot.send_message(message.chat.id, "🔴 Высокоприоритетные задачи:\n" + response)
    else:
        bot.send_message(message.chat.id, "Нет высокоприоритетных задач")

@bot.message_handler(commands=['stats'])
def show_statistics(message):
    user_id = message.from_user.id
    completed, pending, total = task_manager.get_statistics(user_id)
    if total > 0:
        completion_rate = (completed / total) * 100
    else:
        completion_rate = 0
    bot.send_message(message.chat.id, f"📊 Ваша статистика:\n✅ Выполнено: {completed}\n⏳ В процессе: {pending}\n📌 Всего задач: {total}\n🏆 Успешность: {completion_rate:.2f}%")

bot.infinity_polling()