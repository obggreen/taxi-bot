import json
import random
import uuid

from yookassa import Configuration, Payment

Configuration.account_id = 424513
Configuration.secret_key = 'live_c1rXcAjX_T39V4lFkGAx13sfu_63x3UBkYj1BrQ12JM'


async def payment(amount):
    payment = await Payment.create({
        "amount": {
            "value": amount,
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/dfsdafsdfsdfdsfsdf_bot"
        },
        "capture": True,
        "description": f"Покупка тестового тарифа"
    }, uuid.uuid4())

    print(payment)

    return payment


async def check_payment(identy):
    payment_id = identy
    payments = await Payment.find_one(payment_id)
    return payments.status
