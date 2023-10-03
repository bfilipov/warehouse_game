FROM python:3.10-bullseye

COPY requirements.txt populate_db.py game.py .env .flaskenv entrypoint.sh ./game/

ADD app ./game/app
ADD migrations ./game/migrations

WORKDIR game

RUN pip install -r requirements.txt

# Set user and group
ARG user=game
ARG group=game
ARG uid=1000
ARG gid=1000
RUN groupadd -g ${gid} ${group}
RUN useradd -u ${uid} -g ${group} -s /bin/sh -m ${user} # <--- the '-m' create a user home directory

RUN chown game -R /game/

# Switch to user
#USER ${uid}:${gid}

RUN mkdir -p /home/game/logs

EXPOSE 5001

ENTRYPOINT ["./entrypoint.sh"]

#CMD ["gunicorn", "game:app", "-b", "0.0.0.0:5001", "-w", "4", "--access-logfile", "/home/game/logs/warehouse-access.log", "--error-logfile", "/home/game/logs/warehouse-error.log"]

#CMD ["gunicorn", "-b", "0.0.0.0:5001", "-w", "4", "game:app", "--access-logfile", "/home/game/logs/warehouse-access.log", "--error-logfile", "/home/game/logs/warehouse-error.log"]
