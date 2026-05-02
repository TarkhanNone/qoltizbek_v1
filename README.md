# QolTizbek — Система управления нарядами

> Веб-приложение для цифрового документооборота производственных нарядов.  
> Название происходит от казахского «қол тізбек» — цепочка подписей.

## 📌 О проекте

QolTizbek автоматизирует процесс выдачи и контроля производственных нарядов:

- Руководитель создаёт наряд и сразу назначает состав бригады
- Руководитель подписывает наряд «Выдал»
- Старший наряда расписывается
- Каждый работник расписывается индивидуально
- Руководитель закрывает наряд после завершения работ
- Система фиксирует все действия в журнале аудита

---

## ⚙️ Стек технологий

| Компонент | Технология |
|-----------|-----------|
| Backend | Python 3.11, Django 6 |
| База данных | PostgreSQL |
| Frontend | Bootstrap 5, Bootstrap Icons, Chart.js |
| Деплой | Render, Gunicorn, WhiteNoise |
| Контроль версий | Git, GitLab |

---

## 🔄 Workflow наряда

```
Руководитель создаёт наряд + назначает состав
        ↓
Руководитель подписывает «Выдал»
        ↓
Старший наряда подписывает
        ↓
Каждый работник расписывается
        ↓
Статус: Завершён ✅
        ↓
Руководитель закрывает наряд
        ↓
Статус: Закрыт 🔒
```

Нарушить порядок программно невозможно.

---

## 👥 Роли

| Роль | Возможности |
|------|-------------|
| Руководитель | Создаёт наряд, выдаёт, закрывает |
| Старший наряда | Подписывает как старший |
| Работник | Расписывается индивидуально |

Реализовано через **Django Groups** — без хардкода ролей в коде.

---

## 🧩 Модели базы данных

| Модель | Описание |
|--------|---------|
| `User` | Кастомный пользователь (телефон, аватар, должность) |
| `WorkOrder` | Наряд на работу (статусы: draft → progress → done → closed) |
| `Brigade` | Бригада (один наряд = одна бригада, OneToOne) |
| `BrigadeMember` | Участник бригады с флагом `is_leader` |
| `Signature` | Подпись пользователя (issuer / leader / worker) |
| `AuditLog` | Журнал всех действий |

---

## 📋 Функциональность

### Наряды
- Список с поиском, фильтрацией по статусу и сортировкой по колонкам
- Пагинация (10 записей на странице)
- Создание с назначением состава бригады
- Редактирование (только автор или администратор)
- Мягкое удаление с подтверждением

### Аутентификация
- Регистрация с обязательным email, телефоном, аватаром, должностью
- Вход / Выход с редиректом на главную
- Профиль пользователя
- Редактирование профиля
- Смена пароля

### Права доступа
- Список и просмотр — доступны всем
- Создание — только авторизованным
- Редактирование — только автор или staff
- Удаление — только автор или staff

### Дополнительно
- Dashboard — счётчики, график (Chart.js), последние наряды
- Audit Log — история всех действий с датой и пользователем
- PDF-печать готового наряда

---

## 🧪 Тесты

```bash
pytest -v
```

10 тестов покрывают логику подписей:
- Порядок подписей
- Запрет повторной подписи
- Автоматическое обновление статуса
- Защита закрытого наряда

---

## 🚀 Запуск локально

### 1. Клонировать репозиторий

```bash
git clone https://gitlab.com/wwwdarkhan96/qoltizbek_v1.git
cd qoltizbek_v1
```

### 2. Создать виртуальное окружение

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Создать `.env` файл

```env
SECRET_KEY=твой-секретный-ключ
DEBUG=1
DB_NAME=qoltizbek_db
DB_USER=qoltizbek_user
DB_PASSWORD=твой-пароль
DB_HOST=localhost
DB_PORT=5432
```

### 5. Создать базу данных PostgreSQL

```sql
CREATE DATABASE qoltizbek_db;
CREATE USER qoltizbek_user WITH PASSWORD 'пароль';
GRANT ALL PRIVILEGES ON DATABASE qoltizbek_db TO qoltizbek_user;
GRANT ALL ON SCHEMA public TO qoltizbek_user;
```

### 6. Применить миграции

```bash
python manage.py migrate
```

### 7. Загрузить демо-данные

```bash
python manage.py seed_data
```

### 8. Запустить сервер

```bash
python manage.py runserver
```

Открой [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 📁 Структура проекта

```
qoltizbek_v1/
├── config/                  # Настройки Django
│   ├── settings.py
│   └── urls.py
├── accounts/                # Пользователи
│   ├── models.py            # Кастомный User
│   ├── views.py             # Регистрация, профиль, пароль
│   ├── forms.py             # Формы с валидацией
│   └── urls.py
├── workorders/              # Основная логика
│   ├── models.py            # WorkOrder, Brigade, Signature, AuditLog
│   ├── views.py             # CRUD + workflow + подписи
│   ├── forms.py             # Формы с валидацией
│   ├── urls.py
│   ├── tests.py             # 10 pytest тестов
│   └── management/
│       └── commands/
│           └── seed_data.py # Демо-данные
├── templates/               # HTML шаблоны
│   ├── base.html
│   ├── partials/            # navbar, pagination
│   ├── accounts/            # login, register, profile
│   └── workorders/          # list, detail, form, dashboard, print
├── .env                     # Переменные окружения (не в Git)
├── .gitignore
├── requirements.txt
└── pytest.ini
```

---

## 👨‍💻 Автор

**Жаксыбай Дархан**

- GitLab: [wwwdarkhan96](https://gitlab.com/wwwdarkhan96)
- GitHub: [TarkhanNone](https://github.com/TarkhanNone)