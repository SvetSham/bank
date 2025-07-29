"""Вспомогательные функции, необходимые для работы функции страницы «Главная»"""
import datetime
import logging
# import sys
import os
import pandas as pd
from config import BASE_DIR
import json
import requests
from dotenv import load_dotenv


logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    filename=BASE_DIR / "logs" / "utils.log",
                    filemode='w',
                    encoding='utf-8')


def greeting_by_time(moment: str) -> str:
    """Функция получает на вход дату в формате YYYY-MM-DD HH:MM:SS и возвращает соответствующее приветствие."""
    greeting_by_time_logger = logging.getLogger('prepare_date')
    date_obj = datetime.datetime.strptime(moment, "%Y-%m-%d %H:%M:%S")
    greeting_by_time_logger.info(f'Получена дата {date_obj.strftime("%d-%m-%Y %H:%M:%S")}')
    greeting = ''
    if 3 <= date_obj.hour <= 8:
        greeting = "Доброе утро"
        greeting_by_time_logger.info(f'Создано приветствие {greeting}')
    elif 9 <= date_obj.hour <= 14:
        greeting = "Добрый день"
        greeting_by_time_logger.info(f'Создано приветствие {greeting}')
    elif 15 <= date_obj.hour <= 20:
        greeting = "Добрый вечер"
        greeting_by_time_logger.info(f'Создано приветствие {greeting}')
    else:
        greeting = "Доброй ночи"
        greeting_by_time_logger.info(f'Создано приветствие {greeting}')
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
    read_xlsx_file_logger = logging.getLogger("read_xlsx_file")

    excel_data = pd.read_excel(path_to_file)

    read_xlsx_file_logger.info(f'Открыт файл {path_to_file}.')

    return excel_data


def str_to_date(date_str:str) -> datetime.datetime:
    """Функция преобразует входящую строку формата '%d.%m.%Y %H:%M:%S'
     в объект datetime"""
    str_to_date_logger = logging.getLogger("str_to_date")

    date_result = datetime.datetime.strptime(date_str, '%d.%m.%Y %H:%M:%S')

    str_to_date_logger.info(f'Преобразована из строки дата {date_result}.')

    return date_result


def filter_by_date(excel_data:pd.core.frame.DataFrame, moment:str)->pd.core.frame.DataFrame:
    """Функция принимает на вход датафрейм с транзакциями и дату в формате YYYY-MM-DD HH:MM:SS.
    На выходе выдает датафрейм с транзакциями, прошедшими от начала месяца до введённой даты. """
    filter_by_date_logger = logging.getLogger('filter_by_date')

    date_start, date_stop = calculate_time_range(moment)
    filter_by_date_logger.info(f"Создан диапазон дат.")

    excel_data['Дата операции'] = excel_data['Дата операции'].apply(str_to_date)
    filter_by_date_logger.info("Все даты преобразованы из строки в объект datetime.")

    filtered_data=excel_data.loc[(excel_data['Дата операции'] >=date_start)
                                 & (excel_data['Дата операции'] <= date_stop)]
    filter_by_date_logger.info("Отфильтрованы данные по транзакциям для данного диапазона дат.")

    return filtered_data


def get_last_four_numbers_of_card(card_full_number:str) -> str:
    """Функция принимает номер карты в виде строки и,
    если это правда строка, то возвращает последние 4 цифры
    номера карты в виде строки. Иначе возвращает пустую строку. """
    get_last_four_numbers_of_card_logger = logging.getLogger("get_last_four_numbers_of_card")
    if isinstance(card_full_number, str):
        card_short_number = card_full_number[-4:]
        get_last_four_numbers_of_card_logger.info(f"Номер карты представлен в виде последних четырех цифр {card_short_number}.")
        return card_short_number
    else:
        get_last_four_numbers_of_card_logger.info("Транзакция проходила по счёту, а не по карте.")
        return ''


def cut_card_number(cutted_data:pd.core.frame.DataFrame) -> pd.core.frame.DataFrame:
    """Функция принимает датафрейм и возвращает датафрейм с номерами карт в виде последних четырёх цифр."""
    cut_card_number_logger = logging.getLogger("cut_card_number")

    cutted_data.loc[:,'Номер карты'] = cutted_data['Номер карты'].apply(get_last_four_numbers_of_card)
    cut_card_number_logger.info("Все номера карт приведены к последним четырем цифрам.")

    return cutted_data


def make_grouped(grouped_data:pd.core.frame.DataFrame) -> pd.core.frame.DataFrame:
    """ Функция группирует данные по номерам карт"""
    make_grouped_logger = logging.getLogger('make_grouped')
    grouped_data = grouped_data.groupby("Номер карты")
    make_grouped_logger.info("Транзакции сгруппированы по номерам карт.")
    return grouped_data


def read_user_settings_file(path_to_file:str) -> dict:
    """ Функция читает JSON-файл с пользовательскими настройками и возвращает словарь"""
    read_user_settings_file_logger = logging.getLogger("read_user_settings_file")
    with open(path_to_file) as file:
        user_settings = json.load(file)
    read_user_settings_file_logger.info(f"Открыт файл {path_to_file}.")
    return user_settings

def find_exchange_rate(currency:str) -> str:
    """ Функция ищет, сколько рублей сегодня стоит валюта, указанная в user_settings"""
    find_exchange_rate_logger = logging.getLogger("find_exchange_rate")
    load_dotenv()
    API_KEY_CUR = os.getenv("API_KEY_CUR")
    find_exchange_rate_logger.info("Получен API_KEY для поиска курса валют.")
    base = currency
    symbols = 'RUB'
    url = "https://api.apilayer.com/exchangerates_data/latest"

    payload = {"base":base, "symbols":symbols}
    headers = {"apikey": API_KEY_CUR}

    find_exchange_rate_logger.info(f"Отправлен запрос по адресу {url}, узнать, сколько рублей стоит {base}.")
    response = requests.get(url, headers=headers, params=payload)

    status_code = response.status_code
    find_exchange_rate_logger.info(f'Получен код статуса {status_code}.')
    result = response.text

    rate = round(response.json()["rates"][symbols], 2)
    find_exchange_rate_logger.info(f'Получен курс: 1 {base} = {rate} RUB.')

    return rate


def find_stock_price(stock:str) -> float:
    """ Функция ищет, сколько рублей сегодня на время открытия биржи стоят акции, указанные в user_settings"""
    find_stock_price_logger = logging.getLogger("find_stock_price")
    load_dotenv()
    API_KEY_STOCK = os.getenv("API_KEY_STOCK")
    find_stock_price_logger.info("Получен API_KEY для поиска стоимости акций.")

    function = "GLOBAL_QUOTE"
    symbol = stock
    url = f'https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={API_KEY_STOCK}'
    find_stock_price_logger.info(f"Отправлен запрос по адресу {url}, узнать, сколько рублей стоит акция {symbol}.")
    response = requests.get(url)
    status_code = response.status_code
    find_stock_price_logger.info(f'Получен код статуса {status_code}.')
    result = response.text

    stock_price = round(float(response.json()["Global Quote"]["02. open"]), 2)
    find_stock_price_logger.info(f'Получена стоимость акции {symbol} = {stock_price} RUB.')
    return stock_price

