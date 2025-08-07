# Настройка Google Sheets API

## Шаг 1: Создание проекта в Google Cloud Console

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите Google Sheets API:
   - Перейдите в "APIs & Services" > "Library"
   - Найдите "Google Sheets API" и включите его

## Шаг 2: Создание Service Account

1. Перейдите в "APIs & Services" > "Credentials"
2. Нажмите "Create Credentials" > "Service Account"
3. Заполните форму:
   - Name: `sfx-savdo-sheets`
   - Description: `Service account for SFX Savdo bot`
4. Нажмите "Create and Continue"
5. Пропустите шаги с ролями (нажмите "Done")

## Шаг 3: Создание ключа

1. В списке Service Accounts найдите созданный аккаунт
2. Нажмите на email аккаунта
3. Перейдите на вкладку "Keys"
4. Нажмите "Add Key" > "Create new key"
5. Выберите "JSON" и нажмите "Create"
6. Файл автоматически скачается

## Шаг 4: Настройка файла credentials.json

1. Переименуйте скачанный файл в `credentials.json`
2. Поместите его в корневую папку проекта
3. Убедитесь, что файл добавлен в `.gitignore`

## Шаг 5: Настройка доступа к Google Sheets

1. Откройте вашу Google таблицу: https://docs.google.com/spreadsheets/d/1w0ZJ7X44AC_GlnlzkytEhZW8-QKsFiaVQPUvn8YmN1E/edit
2. Нажмите "Share" (в правом верхнем углу)
3. Добавьте email вашего Service Account (из credentials.json, поле `client_email`)
4. Дайте права "Editor"

## Шаг 6: Установка зависимостей

```bash
pip install -r requirements.txt
```

## Шаг 7: Тестирование

Запустите тест подключения:

```bash
python google_sheets.py
```

Если всё настроено правильно, вы увидите сообщение "Подключение к Google Sheets успешно!"

## Структура данных в Google Sheets

Данные будут записываться в лист "Лист1" со следующими колонками:

| A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|
| Поставщик | Объект номи | Махсулот номи | Миқдори | Ўлчов бирлиги | Нархи | Сумма | Изох |

## Устранение неполадок

### Ошибка "Service Account не найден"
- Убедитесь, что файл `credentials.json` находится в корневой папке проекта
- Проверьте, что файл содержит правильные данные

### Ошибка "Доступ запрещен"
- Убедитесь, что Service Account добавлен в настройки доступа к таблице
- Проверьте, что у Service Account есть права "Editor"

### Ошибка "API не включен"
- Убедитесь, что Google Sheets API включен в Google Cloud Console
- Проверьте, что проект выбран правильно

## Безопасность

⚠️ **ВАЖНО**: Никогда не коммитьте файл `credentials.json` в Git!
- Файл уже добавлен в `.gitignore`
- Используйте переменные окружения для продакшена
- Регулярно ротируйте ключи доступа
