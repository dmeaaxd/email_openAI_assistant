import imaplib
import email
from email.mime.text import MIMEText
import smtplib
import time
import os
import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from entity import Base, Client, Message
from openAI_module.generate_mess import *
from utils.funcs import *

dotenv.load_dotenv()

# Настройка SQLAlchemy
engine = create_engine(os.getenv("DB_URL"))
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Настройка Email агента
username = os.getenv("EMAIL_LOGIN")
password = os.getenv("EMAIL_PASSWORD")

def connect_imap():
    print("Подключение к IMAP серверу...")
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(username, password)
    print("Подключение к IMAP серверу выполнено.")
    return imap

def connect_smtp():
    print("Подключение к SMTP серверу...")
    smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    smtp.login(username, password)
    print("Подключение к SMTP серверу выполнено.")
    return smtp

def email_exists(session: Session, email: str) -> bool:
    print(f"Проверка существования email: {email}")
    exists = session.query(Client).filter_by(email=email).first() is not None
    print(f"Email {'найден' if exists else 'не найден'} в базе данных.")
    return exists


def check_inbox(imap, smtp):
    try:
        print("Проверка входящих сообщений...")
        try:
            imap.select("INBOX")
        except Exception as e:
            print(f"Ошибка поиска ящиков в клиенте почты: {e}")

        try:
            status, messages = imap.search(None, '(UNSEEN)')
        except Exception as e:
            print(f"Ошибка присвоения переменным почтовых значений: {e}")

        print(f"Статус поиска сообщений: {status}, Найденные сообщения: {messages}")

        if status == "OK":
            for num in messages[0].split():
                status, data = imap.fetch(num, '(RFC822)')
                # print(f"Статус получения сообщения: {status}, Данные: {data}")

                if status == "OK":
                    for response_part in data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            client_email = email.utils.parseaddr(msg['From'])[1]
                            subject = msg['Subject']
                            print(f"Новое письмо от {client_email} с темой: {subject}")

                            if email_exists(session, client_email):
                                try:
                                    client = session.query(Client).filter_by(email=client_email).one()

                                    # Извлечение текста входящего сообщения
                                    if msg.is_multipart():
                                        message_text = ""
                                        for part in msg.walk():
                                            if part.get_content_type() == "text/plain":
                                                message_text = part.get_payload(decode=True).decode()
                                                break
                                    else:
                                        message_text = msg.get_payload(decode=True).decode()

                                    message_text = filter_message(message_text, username)

                                    print(f"Текст входящего сообщения: {message_text}")
                                    create_message_for_user(session, client.id, 'user', message_text)
                                    send_reply(smtp, client_email, msg, client.id)
                                    print(f"Ответ отправлен на почту в {client_email}")
                                except Exception as e:
                                    print(f"Ошибка отправки сообщения: {e}")

                            imap.store(num, '+FLAGS', '\\Seen')

    except imaplib.IMAP4.abort as e:
        print(f"Ошибка IMAP: {e}. Переподключение...")
        return False
    except Exception as e:
        print(f"Ошибка: {e}")

    return True

def send_reply(smtp, to_address, original_msg, client_id):
    print(f"Генерация ответа для {to_address}...")
    openai_answer = generate_answer(collect_mess_into_dict(session, client_id))
    print(f"Ответ сгенерирован: {openai_answer}")

    reply = MIMEText(openai_answer)
    reply['Subject'] = f"Re: {original_msg['Subject']}"
    reply['From'] = username
    reply['To'] = to_address

    print(f"Отправка ответа на {to_address}...")
    smtp.sendmail(username, to_address, reply.as_string())
    print("Запись ответа в БД")
    create_message_for_user(session, client_id, 'assistant', openai_answer)
    print("Ответ записан в БД")
    print(f"Ответ отправлен на {to_address}.")


def main():
    while True:
        imap = connect_imap()
        smtp = connect_smtp()
        try:
            while True:
                if not check_inbox(imap, smtp):
                    break
                time.sleep(10)
        except KeyboardInterrupt:
            print("Программа прервана. Закрытие соединения.")
            break
        finally:
            imap.logout()
            smtp.quit()
            session.close()

if __name__ == "__main__":
    main()
