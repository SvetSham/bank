"""Вспомогательные функции, необходимые для работы функции страницы «Главная»"""
import datetime
import logging
import sys
import os
import pandas as pd
from config import BASE_DIR
import json
import requests
from dotenv import load_dotenv

# Добавляем путь до корня проекта
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    filename=BASE_DIR / "logs" / "utils.log",
                    filemode='w',
                    encoding='utf-8')


def greeting_by_time(moment: str) -> str:
    """Функция получает на вход дату в формате YYYY-MM-DD HH:MM:SS и возвращает соответствующее приветствие."""
    prepare_date_logger=logging.getLogger('prepare_date')
    date_obj = datetime.datetime.strptime(moment, "%Y-%m-%d %H:%M:%S")
    prepare_date_logger.info(f'Получена дата {date_obj.strftime("%d-%m-%Y %H:%M:%S")}')
    greeting = ''
    if 3 <= date_obj.hour <= 8:
        greeting = "Доброе утро"
        prepare_date_logger.info(f'Создано приветствие {greeting}')
    elif 9 <= date_obj.hour <= 14:
        greeting = "Добрый день"
        prepare_date_logger.info(f'Создано приветствие {greeting}')
    elif 15 <= date_obj.hour <= 20:
        greeting = "Добрый вечер"
        prepare_date_logger.info(f'Создано приветствие {greeting}')
    else:
        greeting = "Доброй ночи"
        prepare_date_logger.info(f'Создано приветствие {greeting}')
    return greeting


def calculate_time_range(moment: str) -> tuple:
    """Функция получает на вход дату в формате YYYY-MM-DD HH:MM:SS и возвращает
    дату начала и дату конца диапазона для поиска в формате DD.MM.YYYY HH:MM:SS"""
    calculate_time_range_logger=logging.getLogger("calculate_time_range")

    date_stop = datetime.datetime.strptime(moment, "%Y-%m-%d %H:%M:%S")
    calculate_time_range_logger.info(f"Получена дата {date_stop.strftime('%d-%m-%Y %H:%M:%S')}")

    date_stop = date_stop.replace(hour=23, minute=59, second=59)
    calculate_time_range_logger.info(f"Создана конечная дата диапазона {date_stop.strftime('%d-%m-%Y %H:%M:%S')}")

    date_start = date_stop.replace(day=1, hour=0, minute=0, second=0)
    calculate_time_range_logger.info(f"Создана начальная дата диапазона {date_start.strftime('%d-%m-%Y %H:%M:%S')}")

    return date_start, date_stop


def read_xlsx_file(path_to_file:str) -> pd.core.frame.DataFrame:
    """Функция читает xlsx-файл и возвращает DataFrame"""
    excel_data=pd.read_excel(path_to_file)
    return excel_data


def str_to_date(date_str:str) -> datetime.datetime:
    """Функция преобразует входящую строку в объект datetime"""
    return datetime.datetime.strptime(date_str, '%d.%m.%Y %H:%M:%S')


def filter_by_date(excel_data:pd.core.frame.DataFrame, moment:str)->pd.core.frame.DataFrame:
    """Функция принимает на вход датафрейм с транзакциями и дату. На выходе выдает
    датафрейм с транзакциями, прошедшими от начала месяца до введённой даты. """
    date_start, date_stop=calculate_time_range(moment)
    excel_data['Дата операции'] = excel_data['Дата операции'].apply(str_to_date)
    filtered_data=excel_data.loc[(excel_data['Дата операции'] >=date_start)
                                 & (excel_data['Дата операции'] <= date_stop)]
    return filtered_data


def get_last_four_numbers_of_card(card_full_number:str) -> str:
    """Функция принимает номер карты в виде строки и,
    если это правда строка, то возвращает последние 4 цифры
    номера карты в виде строки. Иначе возвращает пустую строку. """
    if isinstance(card_full_number, str):
        return card_full_number[-4:]
    else:
        return ''


def cut_card_number(cutted_data:pd.core.frame.DataFrame) -> pd.core.frame.DataFrame:
    """Функция принимает датафрейм и возвращает датафрейм с номерами карт в виде последних четырёх цифр."""
    cutted_data.loc[:,'Номер карты'] = cutted_data['Номер карты'].apply(get_last_four_numbers_of_card)
    return cutted_data


def make_grouped(grouped_data:pd.core.frame.DataFrame) -> pd.core.frame.DataFrame:
    """ Функция группирует данные по номерам карт"""
    grouped_data = grouped_data.groupby("Номер карты")
    return grouped_data


def read_user_settings_file(path_to_file:str) -> dict:
    """ Функция читает JSON-файл с пользовательскими настройками и возвращает словарь"""
    with open(path_to_file) as file:
        user_settings = json.load(file)
    return user_settings

def find_exchange_rate(currency:str) -> str:
    load_dotenv()
    API_KEY_CUR = os.getenv("API_KEY_CUR")
    base = currency
    symbols = 'RUB'
    url = "https://api.apilayer.com/exchangerates_data/latest"

    payload = {"base":base, "symbols":symbols}
    headers = {"apikey": API_KEY_CUR}

    response = requests.request("GET", url, headers=headers, params=payload)
    status_code = response.status_code
    result = response.text
    rate = round(response.json()["rates"][symbols], 2)
    return rate


def find_stock_price(stock:str) -> float:
    load_dotenv()
    API_KEY_STOCK = os.getenv("API_KEY_STOCK")
    function = "GLOBAL_QUOTE"
    symbol = stock
    headers = {"apikey": API_KEY_STOCK}
    payload = {"function": function, "symbol": symbol}
    url = f'https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={API_KEY_STOCK}'
    response = requests.get(url)
    status_code = response.status_code
    result = response.text
    stock_price = round(float(response.json()["Global Quote"]["02. open"]), 2)
    return stock_price

