FROM python:3

ENV BOT_TOKEN="tg_bot_token"
ENV USER_ID="tg_user_id"
ENV http_proxy="http://host.docker.internal:9999"


WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY tg_bot.py .

CMD [ "python", "./tg_bot.py" ]
