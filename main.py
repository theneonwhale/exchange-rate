import argparse
import logging
import aiohttp
import asyncio
from datetime import date, timedelta
import platform

logging.basicConfig(level=logging.INFO)


parser = argparse.ArgumentParser(description='App for checking currency exchange rate')
parser.add_argument('-c', '--currency', default="all", help="Currency name")
parser.add_argument('-d', '--days', default=1, help="Period in days")
args = vars(parser.parse_args())
user_currency = args.get('currency')
user_days = args.get('days')


async def request(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    r = await response.json()
                    return r
                logging.error(f"Error status {response.status} for {url}")
        except aiohttp.ClientConnectorError as e:
            logging.error(f"Connection error {url}: {e}")
        return None


def get_urls(days):
    days = int(days)
    if days > 10:
        days = 10
    urls = []
    for i in range(days):
        day = (date.today() - timedelta(i)).strftime("%d.%m.%Y")
        url = f'https://api.privatbank.ua/p24api/exchange_rates?json&date={day}'
        urls.append(url)
    return urls


def get_output(currency, data):
    result = []
    for i in data:
        res_date = i.get('date')
        if currency == 'all':
            res = {res_date: {}}
            for cur in i.get('exchangeRate'):
                current_cur = cur.get('currency')
                res[res_date].update({current_cur: {}})
                res[res_date][current_cur]['sale'] = cur.get('saleRateNB')
                res[res_date][current_cur]['purchase'] = cur.get('purchaseRateNB')
            result.append(res)
        else:
            currency_data = {}
            for idx, cur in enumerate(i.get('exchangeRate')):
                if cur.get('currency') == currency:
                    currency_data = cur
            res = {res_date: {currency: {}}}
            res[res_date][currency]['sale'] = currency_data.get('saleRateNB')
            res[res_date][currency]['purchase'] = currency_data.get('purchaseRateNB')
            result.append(res)
    return result


async def get_exchange(currency, days):
    urls = get_urls(days)
    res = []
    for url in urls:
        res.append(request(url))
    result = await asyncio.gather(*res)
    return get_output(currency, result)


async def main():
    result = await asyncio.gather(get_exchange(user_currency, user_days))
    logging.info(f'Exchange rate: {result}')
    return result


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
