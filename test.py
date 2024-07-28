import requests


def make_call(api_id, phone, ip):
    url = "https://sms.ru/code/call"
    payload = {
        'api_id': api_id,
        'phone': phone,
        'ip': ip
    }

    try:
        response = requests.get(url, params=payload)
        response_data = response.json()


        if response_data['status'] == "OK":
            print(f"Call initiated successfully to {phone}.")
            print(response_data)
            return response_data
        else:
            print(f"Error: {response_data['status_text']}")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# Пример использования функции
api_id = "4046E8C9-7529-2172-A270-678FBF18731A"
phone = "79956716952"
ip = "188.232.208.221"
make_call(api_id, phone, ip)
