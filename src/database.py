import re
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.config import settings

engine = create_async_engine(
    settings.postgres_dsn_async,
    echo=True,
)


async def create_tables():
    async with engine.begin() as conn:
        await conn.execute(text("drop table if exists message;"))
        await conn.execute(text("drop table if exists log;"))
        await conn.execute(
            text(
                """
                CREATE TABLE message ( 
                    created           TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL, 
                    id                VARCHAR NOT NULL, 
                    int_id            CHAR(16) NOT NULL, 
                    str               VARCHAR NOT NULL, 
                    status            BOOL, 
                    CONSTRAINT message_id_pk PRIMARY KEY(id) 
                ); 
                """
            )
        )
        await conn.execute(text("CREATE INDEX message_created_idx ON message (created);"))
        await conn.execute(text("CREATE INDEX message_int_id_idx ON message (int_id);"))
        await conn.execute(
            text(
                """    
                CREATE TABLE log ( 
                    created       TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL, 
                    int_id        CHAR(16) NOT NULL, 
                    str           VARCHAR, 
                    address       VARCHAR 
                ); 
                """
            )
        )
        await conn.execute(text("CREATE INDEX log_address_idx ON log USING hash (address);"))


async def drop_tables():
    async with engine.begin() as conn:
        await conn.execute(text("drop table if exists message;"))
        await conn.execute(text("drop table if exists log;"))


def is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def process_row(row: str) -> dict:
    result = {
        "created": datetime.strptime(" ".join(row[:2]), "%Y-%m-%d %H:%M:%S"),
        "int_id": row[2],
        "str": " ".join(row[3:]),
        "address": None,
    }
    if len(row) > 4 and is_valid_email(row[4]):
        result["address"] = row[4]

    if row[3] in "<=" and "id=" in row[-1]:
        result["id"] = row[-1].replace("id=", "")
        return result, "message"

    return result, "log"


async def insert_data():
    with open(settings.maillog_path, "r") as data:
        data = map(lambda x: x.strip().split(), data.readlines())
        messages = []
        logs = []
        for item in data:
            data, table = process_row(item)
            if table == "message":
                messages.append(data)
            else:
                logs.append(data)
    async with engine.begin() as conn:
        stmt_messages = text(
            """
            INSERT INTO message (created, id, int_id, str)
            VALUES (:created, :id, :int_id, :str);
            """
        )
        await conn.execute(stmt_messages, messages)
        stmt_logs = text(
            """
            INSERT INTO log (created, int_id, str, address)
            VALUES (:created, :int_id, :str, :address);
            """
        )
        await conn.execute(stmt_logs, logs)
        await conn.commit()
