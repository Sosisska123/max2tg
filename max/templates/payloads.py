import json
import uuid
import re


def get_ping_json(seq: int) -> str:
    """**OPCODE 1**
    Ping

    Returns:
        str: JSON
    """

    return json.dumps(
        {
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": 1,
            "payload": {"interactive": False},
        }
    )


def get_useragent_header_json(useragent: str = None) -> str:
    """**OPCODE 6**
    This is the first sending package to the websocket server. Used for initial connection.

    The response is:
    ```
    {
        "ver": 11,
        "cmd": 1,
        "seq": 0,
        "opcode": 6,
        "payload": {
            "reg-country-code": ["AZ", "AM", "KZ", "KG", "MD", "TJ", "UZ"],
            "location": "RU",
        }
    }
    ```

    Args:
        useragent (str, optional): If you need a custom useragent. If None used default

    Returns:
        str: JSON


    """
    useragent = (
        useragent
        or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"
    )

    return json.dumps(
        {
            "ver": 11,
            "cmd": 0,
            "seq": 0,
            "opcode": 6,
            "payload": {
                "userAgent": {
                    "deviceType": "WEB",
                    "locale": "ru",
                    "deviceLocale": "ru",
                    "osVersion": "Windows",
                    "deviceName": "Edge",
                    "headerUserAgent": useragent,
                    "appVersion": "25.11.1",
                    "screen": "1080x1920 1.0x",
                    "timezone": "Europe/Moscow",
                },
                "deviceId": str(uuid.uuid4()),
            },
        }
    )


def get_token_json(token: str, seq: int = 1) -> str:
    """**OPCODE 19**
    The second package that send to the websocket server. Used for user auth and receive its chat list and more

    Args:
        token (str): You can get the token at the end of authentication `(OPCODE 18)`
        You can get it after sending your phone number `(OPCODE 17)`
        and sending a received mini-token again to the server `(OPCODE 18)`


        It looks like this: `An_Sx6HQ9HDi...`
        seq (int, optional): Sequence number. Defaults to 1.

    Returns:
        str: JSON
    """
    return json.dumps(
        {
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": 19,
            "payload": {
                "interactive": True,
                "token": token,
                "chatsCount": 40,
                "chatsSync": 0,
                "contactsSync": 0,
                "presenceSync": 0,
                "draftsSync": 0,
            },
        }
    )


def get_subscribe_json(state: bool, chat_id: int, seq: int) -> str:
    """**OPCODE 75**
    Somewhy when a user changes the chat this package is sent
    honestly idk why and what does it affect
    btw its used as ping and send every 1 minute

    Args:
        state (bool): When a user changes the chat it will unsubscribe the previous one and subscribe the new one
        False on previous, True on new
        chat_id (int): The chat id        seq (int): Each sub/unsub action has the different sequence number


    Returns:
        str: JSON
    """

    return json.dumps(
        {
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": 75,
            "payload": {"chatId": chat_id, "subscribe": state},
        }
    )


def get_read_last_message_json(
    chat_id: int, message_id: str, timestamp: int, seq: int
) -> str:
    """**OPCODE 50**
    Read the last message in chat

    example
    ```
    {
        "ver": 11,
        "cmd": 0,
        "seq": seq,
        "opcode": 50,
        "payload": {
            "type": "READ_MESSAGE",
            "chatId": -68956055956057,
            "messageId": "115486269922292864",
            "mark": 1762180632359,
        },
    }
    ```


    Args:
        chat_id (int): Chat ID of the message you want to read
        message_id (str): Message ID of the message you want to read
        timestamp (int): UNIX timestamp
        seq (int): Sequence number

    Returns:
        str: JSON
    """

    return json.dumps(
        {
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": 50,
            "payload": {
                "type": "READ_MESSAGE",
                "chatId": chat_id,
                "messageId": message_id,
                "mark": timestamp,
            },
        }
    )


def get_messages_json(
    chat_id: int, timestamp: int, seq: int, messages_count: int = 30
) -> str:
    """**OPCODE 49**
    Get last 30 messages from a certain chat. idk do you send subscription first or not

    After successful auth you'll receive smth like this:
    ```
    {
       "ver": 11,
       "cmd": 1,
       "seq": 10,
       "opcode": 49,
       "payload": {
           "messages": [
               {
                   "sender": 91540825,
                   "id": "115485904704401377",
                   "time": 1762175059576,
                   "text": "",
                   "type": "USER",
                   "cid": 1762175077637,
                   "attaches": [
                       {
                           "_type": "CONTROL",
                           "event": "new",
                           "title": "название",
                           "userIds": [],
                       }
                   ],
               },
               {
                   "sender": 91540825,
                   "reactionInfo": {},
                   "id": "115485943389094002",
                   "time": 1762175649858,
                   "text": "текст",
                   "type": "USER",
                   "cid": 1762175667916,
                   "attaches": [],
               },
           ]
       },
    }
    ```

    Args:
        chat_id (int): Chat ID
        timestamp (int): UNIX Timestamp
        seq (int): Sequence code

    Returns:
        str: JSON
    """

    return json.dumps(
        {
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": 49,
            "payload": {
                "chatId": chat_id,
                "from": timestamp,
                "forward": 0,
                "backward": messages_count,
                "getMessages": True,
            },
        }
    )


# [==================== AUTH ====================]


def get_start_auth_json(phone: str, seq: int) -> str:
    """**OPCODE 17**
    Used for start authentication

    example:
    ```
    {
        "ver": 11,
        "cmd": 0,
        "seq": 8,
        "opcode": 17,
        "payload": {
            "phone": "+71111111111",
            "type": "START_AUTH",
            "language": "ru",
        },
    }
    ```

    After successful auth you'll receive smth like this:
    ```
    {
        "ver": 11,
        "cmd": 1,
        "seq": 11,
        "opcode": 17,
        "payload": {
            "requestMaxDuration": 60000,
            "requestCountLeft": 10,
            "altActionDuration": 60000,
            "codeLength": 6,
            "token": "An_Sx6HQ9HDi...",
        },
    }
    ```

    Args:
        phone (str): Your (or somebody's) phone number. STRICTLY in format +7xxxxxxxxxx
        seq (int): Sequence number

    Returns:
        str: JSON
    """

    if not re.match(r"^\+7\d{10}$", phone):
        raise ValueError(f"Phone number must be in format +7xxxxxxxxxx, got: {phone}")

    return json.dumps(
        {
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": 17,
            "payload": {
                "phone": phone,
                "type": "START_AUTH",
                "language": "ru",
            },
        }
    )


def get_check_code_json(token: str, code: str, seq: int) -> str:
    """**OPCODE 18**
        Used for check code

        After successful auth you'll receive smth like this:
    ```
    {
        "ver": 11,
        "cmd": 1,
        "seq": 16,
        "opcode": 18,
        "payload": {
            "tokenAttrs": {
                "LOGIN": {
                    "token": "An_Sx6HQ9HDi..."
                }
            },
        "profile": {
            "profileOptions": [],
            "contact": {
                "accountStatus": 0,
                "names": [
                    {
                        "name": "имя",
                        "firstName": "имя",
                        "lastName": "",
                        "type": "ONEME",
                    }
                ],
                "phone": 7xxxxxxxxxx,
                "options": ["TT", "ONEME"],
                "updateTime": 1762174777652,
                "id": 91540825,
                },
            },
        },
    }
    ```

        Args:
            token (str): Token that you received in the previous package (OPCODE 17)
            code (str): SMS code that phone number holder received
            seq (int): Sequence code

        Returns:
            str: JSON
    """

    return json.dumps(
        {
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": 18,
            "payload": {
                "token": token,
                "verifyCode": code,
                "authTokenType": "CHECK_CODE",
            },
        }
    )


def get_received_message_response_json(seq: int, chat_id: int, message_id: str) -> str:
    """**OPCODE 128**
    Used for received message response. somehow MAX web version send this data to server
    Interesting fact: This is the only sending data with cmd=1 and received data with cmd=0

    Args:
        seq (int): Sequence number
        chat_id (int): Chat ID
        message_id (str): Message ID

    Returns:
        str: JSON
    """

    return json.dumps(
        {
            "ver": 11,
            "cmd": 1,
            "seq": seq,
            "opcode": 128,
            "payload": {"chatId": chat_id, "messageId": message_id},
        }
    )
