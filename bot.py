import sqlite3
import threading
import time
from datetime import datetime
from telebot import TeleBot
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

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
            conn.execute("""
            CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            points INTEGER DEFAULT 0
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
            conn.execute("INSERT INTO users (user_id, points) VALUES (?, 1) ON CONFLICT(user_id) DO UPDATE SET points = points + 1", (user_id,))
            conn.commit()

    def show_tasks(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT name, theme, priority, deadline, status FROM tasks WHERE user_id = ?", (user_id,))
            return cur.fetchall()

    def get_user_points(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
            result = cur.fetchone()
            return result[0] if result else 0

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


@bot.message_handler(commands=['show_high_priority'])
def show_high_priority_tasks(message):
    user_id = message.from_user.id
    tasks = task_manager.show_high_priority_tasks(user_id)
    if tasks:
        response = "\n".join([task[0] for task in tasks])
        bot.send_message(message.chat.id, "🔴 Высокоприоритетные задачи:\n" + response)
    else:
        bot.send_message(message.chat.id, "Нет высокоприоритетных задач")
@bot.message_handler(commands=['mark_done'])
def mark_done_command(message):
    bot.send_message(message.chat.id, "Введите имя задачи, которую хотите отметить как выполненную:")
    bot.register_next_step_handler(message, mark_task_done)

def mark_task_done(message):
    user_id = message.from_user.id
    task_name = message.text
    task_manager.mark_task_done(task_name, user_id)
    bot.send_message(message.chat.id, "Задача отмечена как выполненная")
    
@bot.message_handler(commands=['show'])
def show_tasks(message):
    user_id = message.from_user.id
    tasks = task_manager.show_tasks(user_id)
    if not tasks:
        bot.send_message(message.chat.id, "📭 У вас нет задач.")
        return
    
    for name, theme, priority, deadline, status in tasks:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Выполнено", callback_data=f"done_{name}"))
        markup.add(InlineKeyboardButton("❌ Удалить", callback_data=f"delete_{name}"))
        response = f"📌 *{name}*\n📂 _{theme}_\n⚠️ *{priority}*\n⏳ {deadline}\n📍 {status}"
        bot.send_message(message.chat.id, response, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("done_"))
def mark_task_done_callback(call):
    task_name = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    task_manager.mark_task_done(task_name, user_id)
    bot.send_message(call.message.chat.id, f"✅ Задача *{task_name}* выполнена! +1 🎉", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
def delete_task_callback(call):
    task_name = call.data.split("_", 1)[1]
    user_id = call.from_user.id
    task_manager.delete_task(task_name, user_id)
    bot.send_message(call.message.chat.id, f"❌ Задача *{task_name}* удалена!", parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def show_statistics(message):
    user_id = message.from_user.id
    points = task_manager.get_user_points(user_id)
    bot.send_message(message.chat.id, f"🏆 Ваши баллы: *{points}*\n🚀 Чем больше задач выполнено – тем выше уровень!", parse_mode="Markdown")

@bot.message_handler(commands=['reminders'])
def send_reminders():
    while True:
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("SELECT user_id, name FROM tasks WHERE status = 'pending' AND deadline <= ?", (now,))
        tasks = cur.fetchall()
        for user_id, name in tasks:
            bot.send_message(user_id, f"⏰ Напоминание: Пора выполнить задачу *{name}*!", parse_mode="Markdown")
        time.sleep(60)

t = threading.Thread(target=send_reminders)
t.daemon = True
t.start()

bot.infinity_polling()
