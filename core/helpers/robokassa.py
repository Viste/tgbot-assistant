import aiohttp
import logging
from urllib import parse

from tools.scheme import Merchant, Order
from core.helpers.tools import robokassa_payment_url, is_test
from core.helpers.tools import calculate_signature, parse_xml_response


logger = logging.getLogger(__name__)


async def check_payment(url) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            xml_data = await response.text()
            logging.info("RESPONSE %s", xml_data)
            parsed_response = parse_xml_response(xml_data)
            return parsed_response


class Robokassa:
    def __init__(self, merchant: Merchant):
        self.merchant = merchant

    async def generate_payment_link(self, order: Order) -> str:
        signature = calculate_signature(self.merchant.login, order.cost, order.number, self.merchant.password1)
        data = {
            'MerchantLogin': self.merchant.login,
            'OutSum': order.cost,
            'InvId': order.number,
            'Description': order.description,
            'SignatureValue': str(signature),
            'IsTest': is_test}
        return f'{robokassa_payment_url}?{parse.urlencode(data)}'
