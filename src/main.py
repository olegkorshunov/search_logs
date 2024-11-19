from contextlib import asynccontextmanager

from fastapi import FastAPI, Form
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import bindparam, text

from src.database import create_tables, drop_tables, engine, insert_data


class SearchResponse(BaseModel):
    log_more_than_100: bool = Field(
        ...,
        description="Флаг, указывающий что найдено записей больше 100 в таблице log",
    )
    message_more_than_100: bool = Field(
        ...,
        description="Флаг, указывающий что найдено записей больше 100 в таблице message",
    )
    logs: list = Field(
        ...,
        description="Список записей из таблицы log",
    )
    messages: list = Field(
        ...,
        description="Список записей из таблицы message",
    )

    model_config = ConfigDict(from_attributes=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    await insert_data()
    yield

    await drop_tables()


app = FastAPI(lifespan=lifespan)


@app.post("/search")
async def search(address: str = Form(..., description="Email address")) -> SearchResponse:
    async with engine.begin() as conn:
        log_stmt = text(
            """
            select created, str, int_id from log
            where address = :address
            order by created, int_id 
            limit 101;
            """
        ).bindparams(address=address)
        logs = await conn.execute(log_stmt)
        logs = logs.fetchall()
        int_ids = list(map(lambda x: x[2], logs))
        msg_stmt = text(
            """
            select created, str from message
            where int_id in :int_ids
            order by created, int_id 
            limit 101;
            """
        ).bindparams(bindparam(key="int_ids", value=int_ids, expanding=True))

        messages = await conn.execute(msg_stmt)
        messages = messages.fetchall()

        logs_list = [list(row)[:2] for row in logs]
        messages_list = [list(row) for row in messages]

    return SearchResponse(
        log_more_than_100=len(logs_list) > 100,
        message_more_than_100=len(messages_list) > 100,
        logs=logs_list[:100],
        messages=messages_list[:100],
    )
