FROM python:3.12

WORKDIR /search_logs

COPY requirements.txt .

RUN pip install -r requirements.txt && pip list

COPY . .

# CMD ["sh"]

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
