>Протопит веб-сервиса очереди задач.
#
Реализованное API:
```bash
# добавить задание в очередь
POST /api/v0/tasks/add/  -> {"task_id": <task_id>}
# информация о задании
POST /api/v0/tasks/<task_id>/ -> {"status": "...", "start_time": "...", "create_time": "...", "time_to_execute": "..."}
```
#
install:
```bash
git clone https://github.com/vilus/proto_task_que.git
cd proto_task_que
# virtualenv .venv
# . .venv/bin/activate
pip install -r src/requirements.txt
# -- simple case: django built-in server + sqlite3
export DEBUG=true
cd src
python manage.py migrate
python manage.py runserver 0.0.0.0:8080
# -- or -- docker + postgres9.6 + gunicorn (+ docker compose)
docker-compose build
docker-compose up -d
```
#
examples of usage:
```bash
for i in `seq 1 10`;do curl -X POST 127.0.0.1:8080/api/v0/tasks/add/; echo ""; done
{"task_id": 91}
{"task_id": 92}
{"task_id": 93}
{"task_id": 94}
{"task_id": 95}
{"task_id": 96}
{"task_id": 97}
{"task_id": 98}
{"task_id": 99}
{"task_id": 100}

curl -X POST 127.0.0.1:8080/api/v0/tasks/96/; echo ""
{"status": "In Queue", "start_time": null, "create_time": "2017-11-15T17:04:36.666Z", "time_to_execute": "None"}

curl -X POST 127.0.0.1:8080/api/v0/tasks/96/; echo ""
{"status": "Run", "start_time": "2017-11-15T17:04:57.494Z", "create_time": "2017-11-15T17:04:36.666Z", "time_to_execute": "None"}

curl -X POST 127.0.0.1:8080/api/v0/tasks/96/; echo ""
{"status": "Completed", "start_time": "2017-11-15T17:05:07.766Z", "create_time": "2017-11-15T17:04:36.666Z", "time_to_execute": "0:00:10.272160"}
```
