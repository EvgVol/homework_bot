# ------------------------------------------------------------------
class GetAPIException(Exception):
    """Исключения получения запроса API."""

    pass


# ------------------------------------------------------------------
class CheckResponseException(Exception):
    """Исключения получения неверного формата ответа API."""

    pass


# ------------------------------------------------------------------
class ParseStatusException(Exception):
    """Исключения получения статуса домашней работы."""

    pass


# ------------------------------------------------------------------
class CheckTokentsException(Exception):
    """Исключения доступности необходимых переменных окружения."""

    pass


# ------------------------------------------------------------------
class SendMessageException(Exception):
    """Исключения отправки сообщения в Telegram."""

    pass


class EmptyValuesFromAPI(Exception):
    """Исключение пустой ответ от API."""

    pass


class NoCorrectCodeRequest(Exception):
    """Исключение не верный код ответа."""

    pass
