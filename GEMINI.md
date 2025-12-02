# Project Overview

This project is a Python-based Telegram bot that acts as a bridge to the "max.ru" chat service. It allows users to interact with their "max.ru" account through a Telegram interface. The bot is built using `aiogram` for the Telegram bot functionality and communicates with the "max.ru" service via a WebSocket connection.

The project is structured into several key components:

- **`bot`**: This directory contains all the code related to the Telegram bot, including handlers for user commands, callbacks, and UI components.
- **`max`**: This directory contains the client for the "max.ru" WebSocket service. It handles authentication, message parsing, and communication with the "max.ru" API.
- **`core`**: This directory contains shared components used by both the `bot` and `max` modules, such as message models and queue management.
- **`shared`**: This directory contains configuration files.

The application uses `SQLAlchemy` for database interaction, with two separate databases for the bot and the "max" client.

## Building and Running

### 1. Installation

Install the required Python dependencies using pip:

```bash
pip install -r requirements.txt
```

### 2. Configuration

The project requires configuration for both the Telegram bot and the "max.ru" service.

1.  Create a `.env` file in the `shared` directory by copying the example file:

    ```bash
    cp shared/.env.example shared/.env
    ```

2.  Edit `shared/.env` and add your Telegram bot token.

3.  Edit `shared/config.yaml` to configure the database URLs, admin users, and other settings.

### 3. Running the Application

To run the application, execute the main module:

```bash
python __main__.py
```

This will start the Telegram bot, connect to the "max.ru" WebSocket service, and initialize the database connections.

## Development Conventions

- **Configuration**: The application uses a combination of a YAML file (`shared/config.yaml`) and an environment file (`shared/.env`) for configuration. The `pydantic` library is used for settings management.
- **Database**: The project uses `SQLAlchemy` for database access. Database initialization and session management are handled by the `DBDependency` class.
- **Asynchronous Code**: The entire application is built on `asyncio` to handle concurrent operations, such as the Telegram bot and the WebSocket client.
- **Modular Structure**: The code is organized into modules with clear responsibilities, such as `bot` for the Telegram bot, `max` for the "max.ru" client, and `core` for shared components.
