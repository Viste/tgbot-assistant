import aiohttp
import decimal
import hashlib
from urllib import parse
from urllib.parse import urlparse


def calculate_signature(*args) -> str:
    """Create signature MD5."""
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()


def parse_response(request: str) -> dict:
    params = {}

    for item in urlparse(request).query.split('&'):
        key, value = item.split('=')
        params[key] = value
    return params


def check_signature_result(order_number: int, received_sum: decimal.Decimal, received_signature: str, password: str) -> bool:
    signature = calculate_signature(received_sum, order_number, password)
    if signature.lower() == received_signature.lower():
        return True
    return False


def generate_payment_link(merchant_login: str, merchant_password_1: str, cost: decimal.Decimal, number: int, description: str, is_test=0,
                          robokassa_payment_url='https://auth.robokassa.ru/Merchant/Index.aspx') -> str:
    """URL for redirection of the customer to the service."""
    signature = calculate_signature(merchant_login, cost, number, merchant_password_1)

    data = {'MerchantLogin': merchant_login, 'OutSum': cost, 'InvId': number, 'Description': description, 'SignatureValue': signature, 'IsTest': is_test}
    return f'{robokassa_payment_url}?{parse.urlencode(data)}'


async def verify_payment_async(verification_url: str) -> str:
    """Asynchronously verify payment status."""
    async with aiohttp.ClientSession() as session:
        async with session.get(verification_url) as response:
            if response.status == 200:
                text = await response.text()
                # Assuming the response text is the verification result
                return text
            else:
                return "Verification failed"
