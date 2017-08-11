import base64

from flask import Flask, request, jsonify, url_for
from celery import Celery
from cStringIO import StringIO
from PIL import Image
from resizeimage import resizeimage

import config


app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = config.REDIS_URL
app.config['CELERY_RESULT_BACKEND'] = config.REDIS_URL
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


@celery.task(name='app.resize_image')
def resize_image(image_base64, width, height):
    decoded = base64.b64decode(image_base64)
    image_binary = StringIO(decoded)

    with Image.open(image_binary) as image:
        image.resize
        resized = resizeimage.resize_cover(image, [width, height])
        buffer = StringIO()
        resized.save(buffer, image.format)

    return base64.b64encode(buffer.getvalue())


@app.route('/resize', methods=['POST'])
def resize():
    image_base64 = request.form[config.IMAGE]
    width = int(request.form[config.WIDTH])
    height = int(request.form[config.HEIGHT])

    task = resize_image.delay(image_base64, width, height)
    return jsonify({}), 202, {'Location': url_for('task_status', task_id=task.id)}


@app.route('/status/<task_id>')
def task_status(task_id):
    task = resize_image.AsyncResult(task_id)

    if task.state == 'PENDING':
        response = {
            'state': task.state,
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'result': task.result
        }
    else:
        response = {
            'state': task.state,
            'exception': str(task.info)
        }

    return jsonify(response)

if __name__ == '__main__':
    app.run(threaded=True)
