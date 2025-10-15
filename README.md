# 🧩 ApexORM — The Django-Style ORM for Any Python Project

**ApexORM** is a modern, standalone, Django-style ORM for Python — completely independent from Django, yet fully inspired by its expressive Model and QuerySet syntax.  
Under the hood, it’s powered by **SQLAlchemy**, bringing high-performance database access, reliability, and compatibility with popular databases like **SQLite**, **PostgreSQL**, and **MySQL**.

If you love Django’s ORM but want to use it **outside Django**, ApexORM is built for you.

---

## 🚀 Features at a Glance

-   ⚙️ **Django-like Models** — Define models with fields, relationships, and lookups like `name__icontains`.
-   🧠 **SQLAlchemy-Powered Engine** — Robust, production-grade SQL handling and connection pooling.
-   🔗 **Relations Support** — ForeignKey, OneToOne, and ManyToMany relations.
-   🔍 **QuerySet API** — Filter, order, exclude, search, and prefetch just like Django.
-   💾 **Simple Migration Helper** — Auto-create tables for registered models.
-   🧩 **Framework-Agnostic** — Works seamlessly with Flask, FastAPI, or any Python project.
-   ⏳ **Async ORM Coming Soon** — Native async engine support (`asyncpg`, `aiosqlite`, etc.) is in development.

---

## 📦 Installation

ApexORM is available on **PyPI**:

```bash
pip install apexorm
```

Or install in editable/development mode:

```bash
python -m pip install -e .
```

---

## 🧰 Quick Start

Define your models using a familiar Django-style syntax:

```python
from apexorm import ApexORM
from apexorm.connection import SQLiteDB
from apexorm.models import Model
from apexorm.models import fields


# Initialize ORM with SQLite (Postgres/MySQL also supported)
orm = ApexORM(SQLiteDB("app.db"))

# Define models
class Author(Model):
    id = fields.IntegerField(primary_key=True)
    name = fields.CharField(max_length=120, unique=True)
    bio = fields.TextField(nullable=True)

class Book(Model):
    id = fields.IntegerField(primary_key=True)
    title = fields.CharField(max_length=200)
    author = fields.ForeignKey("author", related_name="books")

# Register and migrate models
orm.register_models([Author, Book])
orm.migrate()
```

Now you can interact with your database using a **Django-like QuerySet API**:

```python
# Create records
author = Author(name="Ada Lovelace").save()
Book(title="Analytical Engine", author=author).save()

# Query records
books = Book.objects.filter(title__icontains="engine").order_by("-id").all()
first_book = Book.objects.first()

# Update
author.name = "Lady Ada Lovelace"
author.save()

# Delete
Book.objects.filter(title__istartswith="Analytical").delete()

# Relations
for b in author.books.all():
    print(b.title)
```

---

## 🧩 Supported Databases

ApexORM supports all major relational databases supported by SQLAlchemy:

| Database            | Connection Driver | Example DSN                                    |
| ------------------- | ----------------- | ---------------------------------------------- |
| **SQLite**          | Built-in          | `sqlite:///app.db`                             |
| **PostgreSQL**      | `psycopg2`        | `postgresql+psycopg2://user:pass@localhost/db` |
| **MySQL / MariaDB** | `pymysql`         | `mysql+pymysql://user:pass@localhost/db`       |

---

## 🏗️ Project Structure Example

```
myproject/
├── models/
│   ├── __init__.py
│   ├── user.py
│   └── post.py
├── main.py
└── requirements.txt
```

**main.py**

```python
from apexorm import ApexORM
from apexorm.connection import SQLiteDB
from models.user import User
from models.post import Post

orm = ApexORM(SQLiteDB("myapp.db"))
orm.register_models([User, Post])
orm.migrate()

user = User(username="kavi").save()
Post(title="Hello ApexORM", author=user).save()
```

---

## 🧠 Why ApexORM?

Django’s ORM is powerful but **tied to Django’s full framework stack**.
ApexORM gives you the same expressive power, **without** requiring Django or its configuration overhead.

You get:

-   A **clean API** for model definition and querying
-   **SQLAlchemy reliability** for schema and transactions
-   The ability to use Django-style models in **FastAPI, Flask, or standalone Python apps**

Perfect for developers who love Django’s syntax but need the flexibility of a lightweight, standalone environment.

---

## 📈 Roadmap

-   ✅ **Stable synchronous ORM core** (SQLAlchemy-powered)
-   🔄 **Migration tracking system** (in development)
-   ⚡ **Asynchronous ORM** (`AsyncApexORM` with `aiosqlite`, `asyncpg`) — _coming soon_
-   🧱 **Schema diffing + migration generator** (planned)
-   🧪 **Comprehensive test suite + CI/CD integration**
-   🌐 **Integration with upcoming ApexKV Framework** — a full-stack Python + React ERP system

---

## 🔍 SEO Keywords (for discoverability)

> Django-style ORM for Python, Standalone ORM, Python ORM library, SQLAlchemy ORM wrapper, Django-like QuerySet API, ORM for FastAPI, ORM for Flask, Lightweight Python ORM, ApexORM SQLAlchemy, Modern ORM for Python, Django-like models without Django.

---

## 🤝 Contributing

Contributions are welcome!
If you’d like to fix a bug, add a feature (e.g., async or migrations), or improve documentation:

1. Fork the repository
2. Create a new branch
3. Submit a pull request

Please read `AGENTS.md` for repository standards and contribution guidelines.

---

## 🪶 License

ApexORM is released under the **MIT License**.
You are free to use, modify, and distribute it for personal or commercial purposes.

---

## 🌍 Project Links

-   **Website:** [https://apexkv.org](https://apexkv.org)
-   **Source Code:** [https://github.com/ApexKV/apexorm](https://github.com/ApexKV/apexorm)
-   **PyPI:** [https://pypi.org/project/apexorm](https://pypi.org/project/apexorm)

---

> **ApexORM** — the simplicity of Django’s ORM, the power of SQLAlchemy, and the freedom of pure Python.

```

```
