FROM selenium/standalone-firefox:129.0-20260404

WORKDIR /src
COPY requirements.txt /src
RUN pip install -r requirements.txt

COPY ./src /src
EXPOSE 8000
CMD ["fastapi", "run"]
