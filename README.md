<img src="icon.png" align="right" />

# Описание проекта homework_bot
Проект homework_bot предназначен для проверки статуса домашней работы на сервере Яндекса.Практикум. Бот опрашивает API сервис Яндекс.Практикум с периодичностью раз в 10 минут и проверяет статус отправленной на ревью домашней работы. В случае изменения статуса работы, бот пришлет соответствующее уведомление в Telegram. О своей работе все действия передаются в лог, о важных проблемах отправляет уведомление в Telegram.


# Используемые технологии
- Python 3.7.9
- Bot API
- Polling
- Dotenv
- Logging
- Exception

# Подготовка к запуску и запуск проекта api_yamdb

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```

```
source venv/Scripts/activate 
```

```
python -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Запустить проект:

```
python homework.py
```


# Разработчики

[Волочек Евгений](https://github.com/EvgVol): весь проект.

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)
