from datetime import datetime, timedelta


def get_tomorrow_date():
    tomorrow = datetime.today() + timedelta(1)
    return tomorrow.strftime("%Y-%m-%d")


def get_today_date():
    tomorrow = datetime.today()
    return tomorrow.strftime("%Y-%m-%d")


def get_formatted_time(date: datetime):
    formatted_text = datetime.strptime(str(date)[:19], "%Y-%m-%d %H:%M:%S")

    return formatted_text + timedelta(hours=3)


def unix_to_utc(time: str) -> str:
    return datetime.fromtimestamp(time).strftime("%Y-%m-%d")
