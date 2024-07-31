import json
import random
import uuid

from yookassa import Configuration, Payment

Configuration.account_id = 424513
Configuration.secret_key = 'live_c1rXcAjX_T39V4lFkGAx13sfu_63x3UBkYj1BrQ12JM'


async def payment(amount, name, phone):
    payment = await Payment.create({
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "@RuWaysBot"
        },
        "capture": True,
        "description": "Покупка доступа в боте",
        "receipt": {
            "customer": {
                "full_name": name,
                "email": "maybeline.aa@gmail.com",
                "phone": phone
            },
            "items": [
                {
                    "description": "Доступ в боте",
                    "quantity": "1.00",
                    "amount": {
                        "value": str(amount),
                        "currency": "RUB"
                    },
                    "vat_code": "3"  # Код ставки НДС, 1 - НДС 18%, 2 - НДС 10%, 3 - НДС 0%, 4 - без НДС и т.д.
                }
            ]
        }
    }, uuid.uuid4())

    print(payment)

    return payment


async def check_payment(identy):
    payment_id = identy
    payments = await Payment.find_one(payment_id)
    return payments.status
