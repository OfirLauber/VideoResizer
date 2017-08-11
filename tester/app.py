import time
from Queue import Queue

import logging

import config
from workers import VideoWorker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    n = 2
    m = 10
    queue = Queue()

    for _ in range(config.NUM_OF_VIDEO_WORKERS):
        worker = VideoWorker(queue)
        worker.daemon = True
        worker.start()

    for i in range(n):
        queue.put(i + 1)
        time.sleep(m)

    queue.join()
