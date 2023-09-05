FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -U pip &&\
    pip install -r requirements.txt --no-cache-dir
COPY . .
RUN chmod +x run_app.sh
ENTRYPOINT ["/app/run_app.sh"]