import decimal
from dataclasses import dataclass


@dataclass
class AppConfig:
    token: str = ""
    api_key: str = ""
    channel: str = ""
    rb_pass1: str = ""
    rb_pass2: str = ""
    rb_login: str = ""
    # admins: List[int] = field(default_factory=list)


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
