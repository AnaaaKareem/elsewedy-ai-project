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
connection = pika.BlockingConnection(pika.ConnectionParameters(config.RABBITMQ_HOST))
channel = connection.channel()
# Declare the queue to ensure it exists
channel.queue_declare(queue='market_updates')

# Initialize Sentinel to access market data fetching logic
sentinel = UnifiedSentinel(config.KEYS, db_config=config.DB_CONFIG)

print("📡 Market Ticker Producer Started...")

while True:
    # Iterate through all materials to check for price updates
    for mat_name in sentinel.materials:
        # Fetch latest price and trend
        price, trend = sentinel.fetch_price(mat_name)
        
        if price > 0:
            # Construct payload
            data = {'material': mat_name, 'price': price, 'trend': trend, 'time': time.time()}
            
            # Publish to RabbitMQ exchange (default exchange used here)
            channel.basic_publish(exchange='', routing_key='market_updates', body=json.dumps(data))
            print(f"📤 Published: {mat_name} @ ${price}")
        else:
            print(f"⚠️ Skipping {mat_name} due to fetch failure.")
    
    # Wait for 60 seconds before next polling cycle
    time.sleep(60)