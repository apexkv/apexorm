# apexorm/connection/__init__.py


class DB:
    def get_connection_string(self) -> str:
        raise NotImplementedError


class SQLiteDB(DB):
    def __init__(self, name: str="databse.db"):
        self.name = name if name.endswith(".db") else f"{name}.db"

    def get_connection_string(self) -> str:
        return f"sqlite:///{self.name}"


class MysqlDB(DB):
    def __init__(self, host: str, user: str, password: str, database: str):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def get_connection_string(self) -> str:
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}/{self.database}"


class PostgresDB(DB):
    def __init__(self, host: str, user: str, password: str, database: str):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def get_connection_string(self) -> str:
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}/{self.database}"
    

class AsyncSQLiteDB(SQLiteDB):
    def get_connection_string(self) -> str:
        return f"sqlite+aiosqlite:///{self.name}"


class AsyncMysqlDB(MysqlDB):
    def get_connection_string(self) -> str:
        return f"mysql+aiomysql://{self.user}:{self.password}@{self.host}/{self.database}"


class AsyncPostgresDB(PostgresDB):
    def get_connection_string(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}/{self.database}"
