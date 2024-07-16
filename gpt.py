import base64

import requests
from openai import OpenAI

client = OpenAI(api_key="sk-proj-wRH3dEJoUgfT4YyL3xO5T3BlbkFJgmm135S0J6Ifi0RGyOUT")


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


image_path = "files/img_1.png"

base64_image = encode_image(image_path)

api_key = 'sk-proj-wRH3dEJoUgfT4YyL3xO5T3BlbkFJgmm135S0J6Ifi0RGyOUT'

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
    "не нужно, просто формат как я тебе показал, ты строго такой должен вернуть"
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
        "max_tokens": 1000
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    data = response.json()
    print(data)
    content = data['choices'][0]['message']['content']

    return content
