FROM python:3.11-slim

WORKDIR /src
COPY requirements.txt /src
RUN pip install -r requirements.txt

COPY ./src /src
COPY .env /src
EXPOSE 8000
CMD ["fastapi", "run"]
