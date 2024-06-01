import pika
import logging
from queue import Queue
from threading import Lock
from contextlib import contextmanager
from const import RABBITMQ_URL
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RabbitMQSession:
    def __init__(self, url, pool_size=10):
        result = urlparse(url)
        self.rabbitmq_params = pika.ConnectionParameters(
            host=result.hostname,
            port=result.port,
            virtual_host=result.path[1:],
            credentials=pika.PlainCredentials(result.username, result.password)
        )
        self.pool_size = pool_size
        self.pool = Queue(maxsize=pool_size)
        self.lock = Lock()

        for _ in range(pool_size):
            connection = pika.BlockingConnection(self.rabbitmq_params)
            self.pool.put(connection)

    @contextmanager
    def get_connection(self):
        connection = self.pool.get()
        try:
            yield connection
        finally:
            self.pool.put(connection)

    def publish_message(self, queue_name, message):
        with self.get_connection() as connection:
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)
            channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # 使消息持久化
                )
            )
            logger.info(f"Message sent to queue {queue_name}: {message}")

    def consume_messages(self, queue_name, callback):
        with self.get_connection() as connection:
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
            logger.info(f"Start consuming messages from queue {queue_name}")
            channel.start_consuming()

    def stop_consuming(self, connection):
        connection.close()

    def close_all_connections(self):
        with self.lock:
            while not self.pool.empty():
                connection = self.pool.get()
                connection.close()


def callback(ch, method, properties, body):
    try:
        logger.info(f"Received message: {body}")
        # 在这里处理消息
        # 模拟处理时间
        import time
        time.sleep(1)
    finally:
        # 在处理完消息后进行确认
        ch.basic_ack(delivery_tag=method.delivery_tag)


# rabbitmq_session = RabbitMQSession(url=RABBITMQ_URL)
#
# # 发布消息
# rabbitmq_session.publish_message('my_queue', 'Hello, RabbitMQ with connection pool!')
#
# # 消费消息
# try:
#     rabbitmq_session.consume_messages('my_queue', callback)
# except KeyboardInterrupt:
#     rabbitmq_session.close_all_connections()
#     logger.info("Stopped consuming messages and closed all connections")
