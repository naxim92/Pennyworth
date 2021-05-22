import requests
import threading
from playsound import playsound


class TelegramBadConfigException(Exception):
    pass


class TelegramNotifyer():

    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

        if self.token is None \
                or self.chat_id is None \
                or self.token == '' \
                or self.chat_id == '':
            raise TelegramBadConfigException

    def send_text(self, message):
        telegram_url_1 = 'https://api.telegram.org/bot'
        telegram_url_2 = '/sendMessage?chat_id='
        telegram_url_3 = '&parse_mode=Markdown&text='

        send_text = ''.join((telegram_url_1,
                             self.token,
                             telegram_url_2,
                             self.chat_id,
                             telegram_url_3,
                             message))
        response = requests.get(send_text)
        return response.json()


class SoundNotifyer():

    def __init__(self, sound_file_path):
        self.sound = sound_file_path

    def play_sound(self):
        threading.Thread(
            target=(lambda:
                    playsound(self.sound, block=False))
        ).start()
