import openai
import os
import dotenv

dotenv.load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_answer(messages_list):
    response = openai.chat.completions.create(
        model='gpt-4o',
        messages=messages_list
    )
    return response.choices[0].message.content


def generate_greeting(client_info):
    response = openai.chat.completions.create(
        model='gpt-4o',
        messages=[
            {'role': 'system', 'content': client_info},
        ]
    )
    return response.choices[0].message.content
