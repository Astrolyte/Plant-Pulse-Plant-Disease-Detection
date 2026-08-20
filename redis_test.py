import redis

print("1. Attempting to connect...")

try:
    # Adding a 3-second timeout forces Python to throw an error if it can't connect
    r = redis.Redis(
        host='localhost', 
        port=6379, 
        decode_responses=True,
        socket_timeout=3
    )

    # Test the connection directly
    r.ping() 
    print("2. Connected successfully!")

    r.set('foo', 'bar')
    print("3. Set key 'foo'")

    val = r.get('foo')
    print(f"4. Retrieved value: {val}")

    r.close()

except redis.exceptions.TimeoutError:
    print("ERROR: Connection timed out! Redis host/port is unreachable.")
except redis.exceptions.ConnectionError as e:
    print(f"ERROR: Could not connect to Redis: {e}")