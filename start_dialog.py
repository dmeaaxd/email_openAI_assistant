import os
import time

import imaplib
import email
from email.mime.text import MIMEText
import smtplib

import dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from entity import Base, Client
from openAI_module.generate_mess import *
from utils.funcs import *

from process_dialog import connect_smtp

dotenv.load_dotenv()

username = os.getenv("EMAIL_LOGIN")
password = os.getenv("EMAIL_PASSWORD")

engine = create_engine(os.getenv("DB_URL"))

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

sheet_url = os.getenv("SHEET_URL")
spreadsheet = client.open_by_url(sheet_url)
settings_sheet = spreadsheet.worksheet("Настройки")

main_prompt = """Ты нейро-сотрудник компании Avatarex и твоя задача вести переписку через email с потенциальными клиентами, которым ты должен продать идею найма нейро-сотрудников.

Ты пишешь письмо руководителю отдела продаж компании, обращаешься к нему по имени, хвалишь успехи его компании и его личные достижения и подводишь к мысли записаться на экскурсию в Avatarex чтобы он узнал, как нейро-сотрудники помогут его компании существенно увеличить метрики в отделе продаж - конверсии, удовлетворённость клиентов, средний чек.

Твое имя - Владимир Иванов. 

Пиши только сообщение и ничего более!
"""

while True:
    try:
        print("Проверка на запуск...")
        checkbox_status = settings_sheet.cell(1, 7).value

        if checkbox_status == 'TRUE':
            print("Запуск...")

            smtp = connect_smtp()

            email = settings_sheet.cell(2, 1).value
            name = settings_sheet.cell(2, 2).value
            company = settings_sheet.cell(2, 3).value
            sphere = settings_sheet.cell(2, 4).value
            special_prompt = settings_sheet.cell(2, 5).value

            # new_client = Client(email=email, name=name, company=company, sphere=sphere, special_prompt=special_prompt)
            # session.add(new_client)
            # session.commit()

            # Check if client already exists in the database
            existing_client = session.query(Client).filter_by(email=email).first()

            if existing_client:
                print(f"Клиент с email {email} уже существует. Используем существующего клиента.")
                new_client = existing_client
            else:
                print(f"Клиент с email {email} не найден. Создание нового клиента.")
                new_client = Client(email=email, name=name, company=company, sphere=sphere, special_prompt=special_prompt)
                session.add(new_client)
                session.commit()

            greeting_message = generate_greeting(f'{main_prompt}\n\nИмя клиента - {new_client.name}, Название компании клиента - {new_client.company}, сфера деятельности - {new_client.sphere}.\n{new_client.special_prompt}')

            message = MIMEText(greeting_message)
            message['Subject'] = "Наймите нейро-сотрудников для вашего отдела продаж!"
            message['From'] = username
            message['To'] = new_client.email
            print(f"Отправка сообщения на {new_client.email}...")
            smtp.sendmail(username, new_client.email, message.as_string())

            print("Запись сообщения в БД")
            create_message_for_user(session, new_client.id, 'assistant', greeting_message)
            print("Сообщение записано в БД")

            print(f"Сообщение отправлено на {new_client.email}.")

            settings_sheet.update_cell(2, 1, "")
            settings_sheet.update_cell(2, 2, "")
            settings_sheet.update_cell(2, 3, "")
            settings_sheet.update_cell(2, 4, "")
            settings_sheet.update_cell(2, 5, "")
            settings_sheet.update_cell(1, 7, "FALSE")

            smtp.quit()
            session.close()

        time.sleep(5)

    except Exception as e:
        print(f"ПУНЭЭЭЙ. Еще раз! {e}")
        session.rollback()
        session.close()
        session = Session()
