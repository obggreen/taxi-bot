import base64

import requests
from aiogram.client.session import aiohttp
from openai import OpenAI

# client = OpenAI(api_key="sk-proj-oj9ebJMjRtPLhoLHPIxlT3BlbkFJsHJfr7ZEhVsf4t3AXUAm")


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


image_path = "files/img_1.png"

base64_image = encode_image(image_path)

api_key = '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'

check_auto_number = (
    'Твоя задача найти на автомобиле регистрационный знак, если его хорошо видно и ты четко'
    ' можешь определить все буквы и цифры и регион на нем, в ответ ты должен вернуть только'
    ' регистрационный знак без лишней информации, если ты не видишь хотя бы одну букву, когда'
    'формат который мне нужен это строго А555АА, так же забудь о прошлых фотках, либо '
    'сомневаешься в ответе, отправь просто значение 0'
)

check_sts_user = (
    "Ты профессионал по разбору информации с фотографии СТС. "
    "Ты должен собрать информацию, а именно: "
    "марка, модель, цвет, гос номер, год выпуска автомобиля, серия, номер. "
    "Если все данные есть, прислать в формате JSON, а именно в таком: "
    "{\n"
    "  \"марка\": \"\",\n"
    "  \"модель\": \"\",\n"
    "  \"цвет\": \"\",\n"
    "  \"гос_номер\": \"\",\n"
    "  \"год_выпуска\": ,\n"
    "  \"Серия\": ,\n"
    "  \"Номер\": \n"
    "},\n"
    "Если какого-то из данных нет, прислать значение 0."
    "повторяю, ожидаю в ответ только json без лишних слов/букв/пояснений, так же помечять в скобки и указывать json "
    "не нужно, просто формат как я тебе показал, ты строго такой должен вернуть. Возвращай обязательно в формате json,"
    "что бы я мог использовать сразу в коде твой ответ, без лишних слов и вставок"
)

check_rights_user = (
    'Ты профессионал по разбору ФИО с водительского удостоверения, тебе нужно обнаружить ФИО на фотографии и прислать '
    'мне в ответ только ФИО, если ты его не смог найти, пришли мне число 0'
)


async def get_response_gpt(base: str, content: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": content
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 4096
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload) as response:
            data = await response.json()
            print(data)

            content = data['choices'][0]['message']['content']
            print(content)

    return content
