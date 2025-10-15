# apexorm/__init__.py
import importlib
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from apexorm.connection import DB
from apexorm.models import Model, Manager, Base
from apexorm.models.relations import finalize_backrefs
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

__version__ = "0.1.0"

class ApexORM:
    session: sessionmaker
    def __init__(self, db: DB, models_paths: list[str]|None = None):
        self.db = db.get_connection_string()
        self.models_paths = models_paths
        self.engine = create_engine(self.db)
        self.models:list[Model] = []

        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        if not self.check_connection():
            raise ConnectionError("Failed to connect to the database.")

    def migrate(self):
        # finalize relationships before creating tables
        finalize_backrefs(Base)
        for model in self.models:
            model.metadata.create_all(self.engine)

    def register_models(self, models: list[Model]):
        for model in models:
            if issubclass(model, Model):
                model.__generate_table_name__(model.__name__)
                self.models.append(model)
                model._session = self.session
                model.objects = Manager(model)
            else:
                raise TypeError(f"{model} is not a subclass of Model")

    def register_model_paths(self, paths: list[str]):
        for path in paths:
            try:
                module = importlib.import_module(path)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, Model) and attr is not Model:
                        self.register_models([attr])
            except ModuleNotFoundError as e:
                print(f"Module {path} not found: {e}")
            except Exception as e:
                print(f"Error importing module {path}: {e}")

    def check_connection(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False


class AsyncApexORM:
    async def __init__(self, db:DB, models_paths:list[str]|None = None):
        self.db = db.get_connection_string()
        self.engine = create_async_engine(self.db, echo=False)
        self.models = []
        self.Session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.session = None
        self.models_paths = models_paths

        if not await self.check_connection():
            raise ConnectionError("Failed to connect to the database.")

    async def migrate(self):
        """Create all tables"""
        finalize_backrefs(Base)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def register_models(self, models):
        for model in models:
            if issubclass(model, Model):
                model.__generate_table_name__(model.__name__)
                self.models.append(model)
                model._session = self.session
                model.objects = Manager(model)
            else:
                raise TypeError(f"{model} is not a subclass of Model")
            
    def register_model_paths(self, paths: list[str]):
        for path in paths:
            try:
                module = importlib.import_module(path)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, Model) and attr is not Model:
                        self.register_models([attr])
            except ModuleNotFoundError as e:
                print(f"Module {path} not found: {e}")
            except Exception as e:
                print(f"Error importing module {path}: {e}")

    async def check_connection(self):
        """Initialize session and test connection"""
        self.session = self.Session()
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print("Async DB connection error:", e)
            return False

    async def close(self):
        if self.session:
            await self.session.close()
        await self.engine.dispose()