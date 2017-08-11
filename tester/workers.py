import json
import os
import time
import base64
from Queue import Queue
from StringIO import StringIO
from threading import Thread

import cv2
import logging
import requests
from PIL import Image

import config

logger = logging.getLogger(__name__)

class ResizeWorker(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            image_buffer, frame_counter = self.queue.get()
            self.resize_image(image_buffer, frame_counter)
            self.queue.task_done()

    def resize_image(self, image_buffer, output_path):
        encoded = base64.b64encode(image_buffer)

        payload = {
            'image': encoded,
            'width': config.RESIZED_WIDTH,
            'height': config.RESIZED_WIDTH
        }
        r = requests.post(config.RESIZE_URL, data=payload)

        result_url = r.headers.get('Location')

        pending = True
        while pending:
            r = requests.get(result_url)

            response = json.loads(r.text)

            if response['state'] != 'PENDING' and response['state'] != 'PROGRESS':
                pending = False

                if response['state'] == 'SUCCESS':
                    decoded = base64.b64decode(response['result'])
                    image_binary = StringIO(decoded)
                    with Image.open(image_binary) as image:
                        if not os.path.exists(os.path.dirname(output_path)):
                            os.makedirs(os.path.dirname(output_path))
                        image.save(output_path, image.format)

            else:
                time.sleep(config.RETRY_INTERVAL_IN_SECONDS)


class VideoWorker(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            instance_counter = self.queue.get()
            self.resize_video(instance_counter)
            self.queue.task_done()

    def resize_video(self, instance_counter):
        start_time = time.time()

        frame_counter = 1
        queue = Queue()
        cap = cv2.VideoCapture(config.VIDEO_FILE_PATH)

        for _ in range(config.NUM_OF_RESIZE_WORKERS):
            worker = ResizeWorker(queue)
            worker.daemon = True
            worker.start()

        reading_succeeded, frame = cap.read()
        while reading_succeeded:
            r, buffer = cv2.imencode('.jpg', frame)
            output_path = os.path.join(config.OUTPUT_PATH,
                                       'vid-instance{}'.format(instance_counter),
                                       'Frame{}.jpg'.format(frame_counter))
            queue.put((buffer, output_path))
            frame_counter += 1
            reading_succeeded, frame = cap.read()

        queue.join()
        time_took = time.time() - start_time
        logger.info('Took {} seconds for instance {}'.format(time_took, instance_counter))
        logger.info('Frame rate average: {}'.format(frame_counter / time_took))
