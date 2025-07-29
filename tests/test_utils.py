import datetime
import json
import os
from unittest.mock import mock_open, patch

import pandas as pd
import pytest
from dotenv import load_dotenv

from config import BASE_DIR
from src.utils import greeting_by_time, calculate_time_range, read_xlsx_file, str_to_date, filter_by_date
from src.utils import get_last_four_numbers_of_card, cut_card_number, make_grouped, read_user_settings_file
from src.utils import find_exchange_rate, find_stock_price


@pytest.fixture
def date_range() -> tuple:
    date_start = datetime.datetime(2025, 7, 1, 0, 0, 0)
    date_stop = datetime.datetime(2025, 7, 28, 23, 59, 59)
    return date_start, date_stop


@pytest.fixture
def df_example():
    df = pd.DataFrame({"Yes": [50, 21], "No": [131, 2]})
    return df


@pytest.fixture
def date_object():
    date_obj = datetime.datetime(2025, 7, 28, 8, 19, 15)
    return date_obj


@pytest.fixture
def initial_data():
    df = pd.DataFrame(
        {"Дата операции": ["24.01.2025 01:12:34", "28.07.2025 23:42:56", "15.07.2025 16:28:19", "10.08.1976 15:20:31"]}
    )
    return df


@pytest.fixture
def filtered_data():
    df = pd.DataFrame(
        {"Дата операции": [datetime.datetime(2025, 7, 28, 23, 42, 56), datetime.datetime(2025, 7, 15, 16, 28, 19)]}
    )
    return df


@pytest.fixture
def card_numbers_long():
    df = pd.DataFrame({"Номер карты": ["*1234", "*7890"]})
    return df


@pytest.fixture
def card_numbers_short():
    df = pd.DataFrame({"Номер карты": ["1234", "7890"]})
    return df


@pytest.fixture
def not_grouped_data():
    df = pd.DataFrame(
        {
            "Дата операции": [
                "24.01.2025 01:12:34",
                "28.07.2025 23:42:56",
                "15.07.2025 16:28:19",
                "10.08.1976 15:20:31",
            ],
            "Номер карты": ["1234", "7890", "7890", "1234"],
        }
    )
    return df


@pytest.fixture
def grouped_info():
    return {
        "1234": [
            {"Дата операции": "24.01.2025 01:12:34", "Номер карты": "1234"},
            {"Дата операции": "10.08.1976 15:20:31", "Номер карты": "1234"},
        ],
        "7890": [
            {"Дата операции": "28.07.2025 23:42:56", "Номер карты": "7890"},
            {"Дата операции": "15.07.2025 16:28:19", "Номер карты": "7890"},
        ],
    }


@pytest.fixture
def path_to_json_file():
    return BASE_DIR / "user_settings.json"


@pytest.fixture
def json_file_content():
    return '{"user_currencies": ["USD", "EUR"],"user_stocks": ["AAPL", "AMZN"]}'


def test_greeting_by_time():
    assert greeting_by_time("2018-07-30 07:40:31") == "Доброе утро"
    assert greeting_by_time("2018-07-30 13:40:31") == "Добрый день"
    assert greeting_by_time("2018-07-30 20:40:31") == "Добрый вечер"
    assert greeting_by_time("2018-07-30 22:40:31") == "Доброй ночи"


def test_calculate_time_range(date_range):
    assert calculate_time_range("2025-07-28 07:19:20") == date_range


@patch("pandas.read_excel")
def test_read_xlsx_file(mock_xlsx, df_example):
    mock_xlsx.return_value = df_example
    path_to_file = BASE_DIR / "data" / "operations.xlsx"
    result = read_xlsx_file(path_to_file)
    assert result.equals(df_example)
    mock_xlsx.assert_called_once_with(path_to_file)


def test_str_to_date(date_object):
    assert str_to_date("28.07.2025 08:19:15") == date_object


def test_filter_by_date(initial_data, filtered_data):
    result = filter_by_date(initial_data, "2025-07-28 09:41:46").reset_index(drop=True)
    filtered_data = filtered_data.reset_index(drop=True)
    assert result.equals(filtered_data)


def test_get_last_four_numbers_of_card():
    assert get_last_four_numbers_of_card(1234) == ""
    assert get_last_four_numbers_of_card("1234567890") == "7890"


def test_cut_card_number(card_numbers_long, card_numbers_short):
    assert cut_card_number(card_numbers_long).equals(card_numbers_short)


def test_make_grouped(not_grouped_data, grouped_info):
    grouped = make_grouped(not_grouped_data)
    dict_of_groups = grouped.apply(lambda x: x.to_dict(orient="records")).to_dict()
    assert dict_of_groups == grouped_info


def test_read_user_settings_file(json_file_content, path_to_json_file):
    with patch("builtins.open", mock_open(read_data=json_file_content)) as mock_file:
        result = read_user_settings_file(path_to_json_file)
        assert result == json.loads(json_file_content)
        mock_file.assert_called_once_with(path_to_json_file)


@patch("requests.get")
def test_find_exchange_rate(mock_get):
    mock_get.return_value.json.return_value = {
        "success": True,
        "timestamp": 1753717085,
        "base": "EUR",
        "date": "2025-07-28",
        "rates": {"RUB": 94.256183},
    }
    load_dotenv()
    API_KEY_CUR = os.getenv("API_KEY_CUR")
    payload = {"base": "EUR", "symbols": "RUB"}
    headers = {"apikey": API_KEY_CUR}
    url = "https://api.apilayer.com/exchangerates_data/latest"
    assert find_exchange_rate("EUR") == 94.26
    mock_get.assert_called_once_with(url, headers=headers, params=payload)


@patch("requests.get")
def test_find_stock_price(mock_get):
    mock_get.return_value.json.return_value = {
        "Global Quote": {
            "01. symbol": "AMZN",
            "02. open": "233.3500",
            "03. high": "234.2900",
            "04. low": "232.2500",
            "05. price": "232.7900",
            "06. volume": "26300138",
            "07. latest trading day": "2025-07-28",
            "08. previous close": "231.4400",
            "09. change": "1.3500",
            "10. change percent": "0.5833%",
        }
    }
    load_dotenv()
    API_KEY_STOCK = os.getenv("API_KEY_STOCK")
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AMZN&apikey={API_KEY_STOCK}"
    assert find_stock_price("AMZN") == 233.35
    mock_get.assert_called_once_with(url)
