# MagnetBank Monorepo

Consolidated repository for **MagnetBank**, a decentralized, non-custodial torrent metadata indexer powered by the Hive blockchain.

## 🚀 Overview

MagnetBank allows users to search, share, and dynamically generate magnet links directly from blockchain records. It utilizes a SQLite backend for high-performance local indexing while maintaining the Hive blockchain as the immutable source of truth.

### Key Components
- **[frontend/](./frontend)**: A modern, neon-themed Flask web application for searching and submitting magnet links.
- **[node/](./node)**: A high-performance Python worker that synchronizes Hive blockchain operations into the local SQLite database.
- **[utils/](./utils)**: Shared database models, helper functions, and data migration tools.

## 🛠️ Quick Start

### 1. Prerequisites
- **Python 3.14+**
- **uv** (Package & Environment Manager)
- **Hive Keychain** (For submitting new entries)

### 2. Environment Setup
Create a `.env` file at the **project root** (this directory) using the provided example:
```bash
cp .env.example .env
# Edit .env with your Hive account and preferred API node
```

### 3. Installation
Install all dependencies into a unified virtual environment:
```bash
uv sync
```

### 4. Running the Project
#### Start the Sync Node (Backend)
```bash
uv run python node/node.py
```
#### Start the Web Interface (Frontend)
```bash
export FLASK_APP=frontend/app.py
uv run flask run --port 8080
```

## 🏗️ Architecture

- **Blockchain**: [Hive](https://hive.io) (via the bespoke `hive-nectar` library).
- **Database**: [SQLite](https://sqlite.org) with [SQLAlchemy](https://sqlalchemy.org) ORM.
- **Development**: Managed entirely via `uv`.
- **Quality**: Enforced by `prek` (pre-commit hooks) with `ruff` and `black`.

## 📄 License
MagnetBank is open-source software licensed under the MIT License. See [LICENSE](./LICENSE) for details.
