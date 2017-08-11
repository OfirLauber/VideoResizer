Requirements:
- A Redis queue
- OpenCV

Running instructions:
- Configure the app by editing config.py, you'll need to specify the Redis queue url
- Run the Celery worker with:
celery worker -A resize_api.app.celery
- Run the Flask app (run app.py inside the resize_api package)
- Run the tester (run app.py inside the tester package)