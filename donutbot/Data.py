import sqlite3
import datetime
from enum import StrEnum
from pathlib import Path
import pandas as pd

from Config import config

class Operation(StrEnum):
    ADD = "add"
    DELETE = "delete"

def _get_query(query_name):
    with open('donutbot/queries/{}.sql'.format(query_name), 'r', encoding='utf-8') as file:
        query_string = file.read()
    return query_string

class Data:
    connection: sqlite3.Connection

    insert_query = """
        INSERT INTO Records (username, number, time, operation)
        VALUES(?, ?, ?, ?)
    """

    create_query = """
        CREATE TABLE Records (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            number INTEGER NOT NUll,
            time TIMESTAMP NOT NULL,
            operation TEXT NOT NULL);
    """

    def __init__(self):
        first_run = not Path(config.settings["files"]["database"]).exists()

        self.connection = sqlite3.connect(config.settings["files"]["database"])

        if first_run:
            cursor = self.connection.cursor()
            cursor.execute(self.create_query)
            self.connection.commit()

    def add(self, username: str, number: int):
        self.insert_record(username, number, Operation.ADD)

    def remove(self, username: str, number: int):
        self.insert_record(username, number, Operation.DELETE)

    def insert_record(self, username: str, number: int, operation: Operation):
        cursor = self.connection.cursor()
        cursor.execute(self.insert_query, (username, number, datetime.datetime.now().strftime('%F %T.%f')[:-3], operation))
        self.connection.commit()

    def clear(self):
        cursor = self.connection.cursor()
        cursor.execute("TRUNCATE TABLE Records")
        self.connection.commit()


    def summarize(self) -> dict[str, int]:
        result: dict[str, int] = {}

        cursor = self.connection.cursor()
        cursor.execute("SELECT username, number, operation FROM Records")

        for username, number, operation in cursor:
            if username in result:
                if operation == Operation.ADD:
                    result[username] += int(number)
                else:
                    result[username] -= int(number)
            else:
                result[username] = (int(number) * 1 if operation == Operation.ADD else -1)

        return result
    
    def summarize_rates(self) -> dict[str, float]:
        return self.get_rates_dataframe()[['username','donuts_per_day']].set_index('username').to_dict()['donuts_per_day']

    def get_dataframe(self) -> pd.DataFrame:
        return pd.read_sql_query("SELECT * from Records ORDER BY time ASC", self.connection)
    
    def get_cleaned_dataframe(self) -> pd.DataFrame:
        if self.needs_refresh('cleaned_records'):
            self.clean_records()
        return pd.read_sql_query("SELECT * from cleaned_records ORDER BY time ASC", self.connection)
    
    def get_rates_dataframe(self) -> pd.DataFrame:
        if self.needs_refresh('cleaned_records'):
            self.clean_records()
        if self.needs_refresh('donut_rates'):
            self.estimate_rates()
        return pd.read_sql_query("SELECT * from donut_rates", self.connection)
    
    def clean_records(self):
        print('Cleaning records...')
        df_clean = pd.read_sql_query(_get_query('cleaned_records'), self.connection)
        df_clean.to_sql('cleaned_records', self.connection, if_exists='replace', index=False)
    
    def estimate_rates(self):
        print('Estimating rates...')
        df_rates = pd.read_sql_query(_get_query('donut_rates'), self.connection)
        df_rates.to_sql('donut_rates', self.connection, if_exists='replace', index=False)
    
    def needs_refresh(self, table_name: str) -> bool:
        try:
            staleness_query = '''
                select 
                    (select max(refresh_time) from {}) < (select datetime(max(time), 'utc') from Records)
                        OR 
                    (select julianday(max(refresh_time)) from {}) < (julianday('now') - 1)
            '''.format(table_name, table_name)
        except:
            return True
        return bool(pd.read_sql_query(staleness_query, self.connection).iloc[0,0])
