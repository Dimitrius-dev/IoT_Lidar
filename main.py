import socket

from telebot import TeleBot
from config import token

from Scanner import *

import multiprocessing
import time

def telegram_bot(token):
    bot = TeleBot(token)

    @bot.message_handler(commands=["start"])
    def start_message(message):
        bot.send_message(message.chat.id, "Привет, это "\
                                          "студенческий проект для игры пиксель арт"\
                                          "нажмите /help для получения информации")

    @bot.message_handler(content_types=["text"])
    def send_text(message):

        if message.text.lower() == "/help":  # COMMAND HELP
            try:
                help = "команды:\n\n" \
                        "/help - данная команда\n\n" \
                        "/check - проверить соединение\n\n" \
                        "/scan - начать сканирование"
                bot.send_message(message.chat.id, help)
            except Exception as ex:
                bot.send_message(message.chat.id, "error")

        elif message.text.lower() == "/check":
            try:
                bot.send_message(message.chat.id, "Соединение...")
                scan = Scanner()
                scan.check()
                bot.send_message(message.chat.id, "Модуль найден")
            except socket.timeout:
                bot.send_message(message.chat.id, "Связь с модулем отсутствует")
            except Exception as ex:
                bot.send_message(message.chat.id, ex)

        elif message.text.lower() == "/scan":
            try:
                next_step = bot.send_message(message.chat.id, "Начать сканирование? ( /Yes --- /No )")
                bot.register_next_step_handler(next_step, check_scan)
                # bot.send_document(chat_id=message.chat.id, document=open('data.obj', 'rb'))
            except Exception as ex:
                bot.send_message(message.chat.id, ex)

    def check_scan(message):
        try:
            if message.text.lower() == "/yes":
                scan = Scanner()
                scan.scan()
                bot.send_document(chat_id=message.chat.id, document=open('data.obj', 'rb'))

            if message.text.lower() == "/no":
                bot.clear_step_handler_by_chat_id(message.chat.id)
                return
        except Exception as ex:
            bot.send_message(message.chat.id, ex)
        finally:
            bot.clear_step_handler_by_chat_id(message.chat.id)

    # bot.infinity_polling(timeout=10, long_polling_timeout=5)
    bot.polling()

if __name__ == '__main__':
    telegram_bot(token)