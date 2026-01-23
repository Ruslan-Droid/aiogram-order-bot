
# Aiogram 3 Bot Template

This is a template for telegram bots written in python using the `aiogram` framework

## About the template

### Used technology
* Python 3.14;
* aiogram 3.x (Asynchronous Telegram Bot framework);
* aiogram_dialog (GUI framework for telegram bot);
* dynaconf (Configuration Management for Python);
* taskiq (Async Distributed Task Manager);
* fluentogram (Internationalization tool in the Fluent paradigm);
* Docker and Docker Compose (containerization);
* PostgreSQL (database);
* NATS (taskiq broker);
* Redis (cache, taskiq result backend);
* Alembic (database migrations).

### Structure

```
📦 aiogram_bot_template/
│   ⚙️ .env.example
│   🚫 .gitignore
│   ⚙️ .python-version
│   ⚙️ alembic.ini
│   🐳 docker-compose.example
│   🐍 main.py
│   📦 pyproject.toml
│   📖 README.md
│   📦 uv.lock
│           
├── 📂 alembic
│   │   🐍 env.py
│   │   📝 script.py.mako
│   │   
│   ├── 📂 versions
│           
├── 📂 app
│   ├── 📂 bot
│   │   │   🐍 bot.py
│   │   │   🐍 __init__.py
│   │   │   
│   │   ├── 📂 dialogs
│   │   │   ├── 📂 flows
│   │   │   │   │   🐍 __init__.py
│   │   │   │   │   
│   │   │   │   ├── 📂 settings
│   │   │   │   │   │   🐍 dialogs.py
│   │   │   │   │   │   🐍 getters.py
│   │   │   │   │   │   🐍 handlers.py
│   │   │   │   │   │   🐍 keyboards.py
│   │   │   │   │   │   🐍 states.py
│   │   │   │   │           
│   │   │   │   ├── 📂 start
│   │   │   │   │   │   🐍 dialogs.py
│   │   │   │   │   │   🐍 getters.py
│   │   │   │   │   │   🐍 handlers.py
│   │   │   │   │   │   🐍 states.py
│   │   │   │           
│   │   │   └── 📂 widgets
│   │   │       │   🐍 i18n.py
│   │   │               
│   │   ├── 📂 enums
│   │   │   │   🐍 group_data.py
│   │   │           
│   │   ├── 📂 filters
│   │   │   │   🐍 chat_type_filters.py
│   │   │   │   🐍 dialog_filters.py
│   │   │           
│   │   ├── 📂 handlers
│   │   │   │   🐍 commands.py
│   │   │   │   🐍 errors.py
│   │   │   │   🐍 groups.py
│   │   │   │   🐍 user_statuses.py
│   │   │   │   🐍 __init__.py
│   │   │           
│   │   ├── 📂 i18n
│   │   │   │   🐍 translator_hub.py
│   │   │           
│   │   ├── 📂 keyboards
│   │   │   │   🐍 inline_keyboards.py
│   │   │   │   🐍 menu_button.py
│   │   │   │   
│   │   │   └── 📂 __pycache__
│   │   │           🐍 inline_keyboards.cpython-314.pyc
│   │   │           🐍 menu_button.cpython-314.pyc
│   │   │           
│   │   ├── 📂 middlewares
│   │   │   │   🐍 database.py
│   │   │   │   🐍 get_group.py
│   │   │   │   🐍 get_user.py
│   │   │   │   🐍 i18n.py
│   │   │   │   🐍 shadow_ban.py
│   │   │   │   
│   │   │   └── 📂 __pycache__
│   │   │           🐍 database.cpython-314.pyc
│   │   │           🐍 get_group.cpython-314.pyc
│   │   │           🐍 get_user.cpython-314.pyc
│   │   │           🐍 i18n.cpython-314.pyc
│   │   │           🐍 shadow_ban.cpython-314.pyc
│   │   │           
│   │   ├── 📂 states
│   │   │       🐍 states.py
│   │   │       
│   │   ├── 📂 utils
│   │   │   │   🐍 group_utils.py
│   │           
│   ├── 📂 infrastructure
│   │   ├── 📂 cache
│   │   │   │   🐍 connect_to_redis.py
│   │   │   │   🐍 __init__.py
│   │   │           
│   │   └── 📂 database
│   │       │   🐍 db.py
│   │       │   
│   │       ├── 📂 enums
│   │       │   │   🐍 user_roles.py
│   │       │           
│   │       ├── 📂 models
│   │       │   │   🐍 base_model.py
│   │       │   │   🐍 group.py
│   │       │   │   🐍 user.py
│   │       │   │   🐍 __Init__.py
│   │       │           
│   │       ├── 📂 query
│   │       │   │   🐍 group_queries.py
│   │       │   │   🐍 user_queries.py
│   │               
│   └── 📂 services
│       └── 📂 scheduler
│           │   🐍 taskiq_broker.py
│           │   🐍 tasks.py
│                   
├── 📂 config
│   │   🐍 config.py
│   │   ⚙️ settings.toml
│           
├── 📂 locales
│   ├── 📂 en
│   │   └── 📂 LC_MESSAGES
│   │           📝 txt.ftl
│   │           
│   └── 📂 ru
│       └── 📂 LC_MESSAGES
│               📝 txt.ftl
│               
└── 📂 nats_broker
    └── 📂 config
            ⚙️ server.conf
```

## Installation

1. Clone the repository to your local machine via HTTPS:

```bash
https://github.com/Ruslan-Droid/aiogram_bot_template.git
```
or via SSH:
```bash
git clone git@github.com:Ruslan-Droid/aiogram_bot_template.git
```

2. Create a `docker-compose.yml` file in the root of the project and copy the code from the `docker-compose.example` file into it.

3. Create a `.env` file in the root of the project and copy the code from the `.env.example` file into it. Replace the required secrets (BOT_TOKEN, ADMINS_CHAT, etc).

4. Run `docker-compose.yml` with `docker compose up` command. You need docker and docker-compose installed on your local machine.

5. Create a virtual environment in the project root and activate it.

6. Install the required libraries in the virtual environment. With `uv`:
```bash
uv sync
```
7. Create first migration 
```bash
alembic revision --autogenerate -m "initial migration"
```

8. Apply database migrations using the command:
```bash
alembic upgrade head
```

9. If you want to use the Taskiq broker for background tasks as well as the Taskiq scheduler, add your tasks to the `tasks.py` module and start the worker first:
```bash
taskiq worker app.services.scheduler.taskiq_broker:broker -fsd
```
and then the scheduler:
```bash
taskiq scheduler app.services.scheduler.taskiq_broker:scheduler
```

10. Run `main.py` to check the functionality of the template.

11. You can fill the template with the functionality you need.

## Developer tools

For convenient interaction with nats-server you need to install nats cli tool. For macOS you can do this through the homebrew package manager. Run the commands:
```bash
brew tap nats-io/nats-tools
brew install nats-io/nats-tools/nats
```
For linux:
```bash
curl -sf https://binaries.nats.dev/nats-io/natscli/nats@latest | sh
sudo mv nats /usr/local/bin/
```
After this you can check the NATS version with the command:
```bash
nats --version
```

## TODO

1. Add mailing service
2. Set up a CICD pipeline using Docker and GitHub Actions
