import socket

from telebot import TeleBot
from config import token

from Scanner import *

import multiprocessing
import time

def telegram_bot(token):
    bot = TeleBot(token)
    scan = Scanner()

    @bot.message_handler(commands=["start"])
    def start_message(message):
        bot.send_message(message.chat.id, "Привет, это "\
                                          "студенческий проект Lidar IoT интернет вещей академии самсунг"\
                                          "Дмитрия Белова"\
                                          "нажмите /help для получения информации")

    @bot.message_handler(content_types=["text"])
    def send_text(message):

        if message.text.lower() == "/help":  # COMMAND HELP
            try:
                help = "команды:\n\n" \
                        "/help - данная команда\n\n" \
                        "/check - проверить соединение\n\n" \
                        "/scan - начать сканирование\n\n" \
                        "/get - получить последний скан\n\n" \
                        "/get_raw - получить последние материалы"
                bot.send_message(message.chat.id, help)
            except Exception as ex:
                bot.send_message(message.chat.id, "error")

        elif message.text.lower() == "/check":
            try:
                bot.send_message(message.chat.id, "Соединение...")
                scan.check()
                bot.send_message(message.chat.id, "Модуль найден")
            except socket.timeout:
                bot.send_message(message.chat.id, "Связь с модулем отсутствует")
            except Exception as ex:
                bot.send_message(message.chat.id, ex)

        elif message.text.lower() == "/get_raw":
            try:
                bot.send_message(message.chat.id, "Материалы последнего скана")
                bot.send_document(chat_id=message.chat.id, document=open('data_raw.txt', 'rb'))
            except Exception as ex:
                bot.send_message(message.chat.id, ex)

        elif message.text.lower() == "/get":
            try:
                bot.send_message(message.chat.id, "Последний скан")
                bot.send_document(chat_id=message.chat.id, document=open('data.obj', 'rb'))
            except Exception as ex:
                bot.send_message(message.chat.id, ex)

        elif message.text.lower() == "/scan":
            try:
                next_step = bot.send_message(message.chat.id, "Начать сканирование? ( /Yes --- /No )")
                bot.register_next_step_handler(next_step, check_scan)
            except Exception as ex:
                bot.send_message(message.chat.id, ex)

    def check_scan(message):
        try:
            if message.text.lower() == "/yes":

                scan.scan()
                bot.send_message(message.chat.id, "Сканирование...")
                bot.send_document(chat_id=message.chat.id, document=open('data.obj', 'rb'))

            if message.text.lower() == "/no":
                bot.clear_step_handler_by_chat_id(message.chat.id)
                return
        except Exception as ex:
            bot.send_message(message.chat.id, ex)
        finally:
            bot.clear_step_handler_by_chat_id(message.chat.id)

    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    # bot.polling()

if __name__ == '__main__':
    telegram_bot(token)