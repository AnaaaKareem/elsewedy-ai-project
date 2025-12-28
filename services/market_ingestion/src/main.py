import sys
import os

# Add 'shared' directory to path to allow importing common modules
# Works for both Docker (where /app/shared is mounted) and Local (via relative path)
current_dir = os.path.dirname(os.path.abspath(__file__))
shared_dir = os.path.abspath(os.path.join(current_dir, '../../../shared'))
if os.path.exists(shared_dir) and shared_dir not in sys.path:
    sys.path.append(shared_dir)

import pika, json, time
from data_sources.unified_sentinel import UnifiedSentinel
from infrastructure.config import config

"""
RabbitMQ Producer Service.

This service acts as a 'Market Ticker', continuously fetching real-time market data
for all tracked materials and publishing update events to the 'market_updates' queue.
Downstream workers consume these events to trigger AI inference and optimization.
"""

# Setup RabbitMQ Connection
# Uses host from centralized config (typically 'localhost' or container name)
connection = pika.BlockingConnection(pika.ConnectionParameters(
    host=config.RABBITMQ_HOST,
    credentials=pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASS)
))
channel = connection.channel()
# Declare the queue to ensure it exists (Durable = survives broker restart)
channel.queue_declare(queue='market_updates', durable=True)

# Initialize Sentinel to access market data fetching logic
# Ingestion service doesn't need DB or heavy analytics, preventing import errors from missing libs
sentinel = UnifiedSentinel(config.KEYS, db_config=None)

print("📡 Market Ticker Producer Started...")

while True:
    # Iterate through all materials to check for price updates
    for mat_name in sentinel.materials:
        # Fetch latest price and trend
        price, trend = sentinel.fetch_price(mat_name)
        
        if price > 0:
            # Construct payload
            data = {'material': mat_name, 'price': price, 'trend': trend, 'time': time.time()}
            
            # Publish Persistent Message
            channel.basic_publish(
                exchange='',
                routing_key='market_updates',
                body=json.dumps(data),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                ))
            print(f"📤 Published: {mat_name} @ ${price}")
        else:
            print(f"⚠️ Skipping {mat_name} due to fetch failure.")
    
    # Wait for 60 seconds before next polling cycle
    time.sleep(60)