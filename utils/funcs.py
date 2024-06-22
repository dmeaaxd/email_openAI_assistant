from entity import Message


def create_message_for_user(session, client_id, sender, message_text):
    new_message = Message(client_id=client_id, sender=sender, mess_text=message_text)
    session.add(new_message)
    session.commit()


def collect_mess_into_dict(session, client_id):
    messages = session.query(Message).filter(Message.client_id == client_id).order_by(Message.datetime.asc()).all()

    messages_list = [
        {"role": "assistant" if message.sender == "assistant" else "user", "content": message.mess_text}
        for message in messages
    ]
    return messages_list


def filter_message(message_text, email):
    lines = message_text.split('\n')

    email_index = -1
    for i, line in enumerate(lines):
        if email in line:
            email_index = i
            break

    if email_index != -1:
        filtered_lines = lines[:email_index]
        return '\n'.join(filtered_lines)
    else:
        return message_text
