""" Основные функции для генерации JSON-ответов """
import utils
from config import BASE_DIR
import logging


def make_main_content(date:str) -> dict:
    """ Функция формирует словарь с данными по картам, транзакциям
    за диапазон от начала месяца до указанной даты включительно, а также
    по текущим курсам валют и стоимости акций, указанными в user_settings"""

    make_main_content_logger = logging.getLogger("make_main_content")
    make_main_content_logger.info("Начинаем сбор данных для формирования главной страницы.")
    result = {"greeting" : utils.greeting_by_time(date)}

    data = utils.read_xlsx_file(BASE_DIR / "data" / "operations.xlsx")
    make_main_content_logger.info("Открыт xlsx-файл с транзакциями.")

    filtered_by_date = utils.filter_by_date(data, date)
    make_main_content_logger.info("Взяты данные только для заданного диапазона дат.")

    cutted_data = utils.cut_card_number(filtered_by_date)
    make_main_content_logger.info("Номер карты преобразован в короткий - последние 4 цифры номера карты.")

    grouped = utils.make_grouped(cutted_data)
    make_main_content_logger.info("Данные сруппированы по номеру карты.")

    make_main_content_logger.info("Готовим информацию о картах и транзакциях.")
    top_transactions = []
    cards_list = []
    for name, group in grouped:
        if name == "": # Это транзакции. Сортируем транзакции по убыванию суммы платежа.
            group.sort_values(by='Сумма платежа', axis=0, ascending=False, inplace=True)
            make_main_content_logger.info("Транзакции по счетам отсортированы по убыванию суммы платежа")
            if group['Сумма платежа'].count() >= 5:
                for i in range(5):
                    transaction_info = {"date": group.iloc[i, 1],
                                        "amount": float(group.iloc[i, 6]),
                                        "category": group.iloc[i, 9],
                                        "description": group.iloc[i, 11]
                                        }
                    top_transactions.append(transaction_info)
            else:
                i = 0
                while i < group['Сумма платежа'].count():
                    transaction_info = {"date": group.iloc[i, 1],
                                        "amount": float(group.iloc[i, 6]),
                                        "category": group.iloc[i, 9],
                                        "description": group.iloc[i, 11]
                                        }
                    top_transactions.append(transaction_info)
                    i += 1
            make_main_content_logger.info("Получили информацию о топ-5 транзакциях по счетам по сумме платежа.")
        else: # Это карта. Собираем информацию по каждой карте.
            total_spent = 0
            for i in range(group["Сумма платежа"].count()):
                if group.iloc[i,6] < 0:
                    total_spent += group.iloc[i,6]
            cashback = float(round(-total_spent / 100, 2))
            total_spent = float(round(-total_spent, 2))

            card_info = {
                "last_digits": name,
                "total_spent": total_spent,
                "cashback": cashback
            }
            cards_list.append(card_info)
            make_main_content_logger.info(f"Получена информация по карте {name}.")

    result["cards"] = cards_list
    result["top_transactions"] = top_transactions

    # Открываем JSON-файл с пользовательскими настройками.
    user_settings = utils.read_user_settings_file(BASE_DIR / "user_settings.json")
    make_main_content_logger.info("Открыт файл user_settings.")

    # Ищем курсы валют на сегодня
    currency_rate = []
    for currency in user_settings["user_currencies"]:
        current_currency = {
            "currency": currency,
            "rate": utils.find_exchange_rate(currency)
        }
        currency_rate.append(current_currency)

    result["currency_rates"] = currency_rate
    make_main_content_logger.info("Для каждой интересующей пользователя валюте получили курс на сегодняшний день.")

    # Ищем стоимость акций на сегодня
    stock_prices = []
    for stock in user_settings['user_stocks']:
        current_stock = {
            "stock": stock,
            "price": utils.find_stock_price(stock)
        }
        stock_prices.append(current_stock)

    result["stock_prices"] = stock_prices
    make_main_content_logger.info("Для каждой акции получили стоимость на открытие биржи сегодня.")

    return result


print(make_main_content("2018-07-30 13:40:31"))
