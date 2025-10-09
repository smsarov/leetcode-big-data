from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def load_csv_to_db(csv_path: str, table_name: str):
    df = pd.read_csv(csv_path)
    df['is_accepted'] = df['is_accepted'].astype(bool)
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    print(f"Данные из {csv_path} загружены в таблицу {table_name}")

def fetch_data(table_name: str, username: str = None, columns: list[str] = None):
    with engine.connect() as conn:
        cols = ", ".join(columns) if columns else "*"
        if username:
            query = text(f"SELECT {cols} FROM {table_name} WHERE username = :username")
            result = conn.execute(query, {"username": username})
            print(f"Получены записи пользователя {username}")
        else:
            query = text(f"SELECT {cols} FROM {table_name}")
            result = conn.execute(query)
            print("Получены все записи из таблицы")

        rows = result.fetchall()
        print(f"Количество строк: {len(rows)}")
        return rows


