import hashlib
import time
import random
import string

def generate_api_key():
    # Get the current time in milliseconds
    current_time = str(time.time()).encode('utf-8')
    
    # Generate a random string
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=16)).encode('utf-8')
    
    # Combine the time and random string
    combined = current_time + random_string
    
    # Create a SHA-256 hash of the combined string
    api_key = hashlib.sha256(combined).hexdigest()
    
    return api_key

if __name__ == "__main__":
    num_keys = 10  # Number of API keys to generate
    for _ in range(num_keys):
        print(generate_api_key())
