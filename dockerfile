FROM python:3

ENV BOT_TOKEN="tg_bot_token"
ENV USER_ID="tg_user_id"

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY tg_bot.py .

CMD [ "python", "./tg_bot.py" ]
