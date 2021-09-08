FROM python:3.10.0rc2-slim-buster
WORKDIR /app
RUN git clone https://github.com/TamzinHadasa/zinbot.git .
RUN pip3 install -r requirements.txt
COPY config.py config.py
CMD ["python","main.py"]
