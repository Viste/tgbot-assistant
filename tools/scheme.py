import decimal
from dataclasses import dataclass


@dataclass
class Merchant:
    login: str
    password1: str
    password2: str


@dataclass
class Order:
    number: int
    description: str
    cost: decimal
