import sys
import json
import requests
import urllib3

# Suppress only the single InsecureRequestWarning from urllib3 needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Update with your Node.js server URL and API key
proxy_url = "https://10.0.0.79:443/api/chat"  # Ensure you use https and the correct port
api_key = "52a23153a13ce62139fd50b1190e748d2c849600ddc64e8db218380441bafbf9"  # Replace with your actual API key

model = "llama3"  # Update with your desired model name

def chat(message, output_file):
    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": [{"role": "user", "content": message}]
    }

    params = {
        "api_key": api_key
    }

    try:
        r = requests.post(
            proxy_url,
            json=data,
            headers=headers,
            params=params,
            verify=False,  # Disable SSL verification
            timeout=30,  # Adjust timeout as necessary
            stream=True
        )
        r.raise_for_status()

        response = ""
        for line in r.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                try:
                    json_line = json.loads(decoded_line)
                    if isinstance(json_line, dict) and "message" in json_line and "content" in json_line["message"]:
                        response += json_line["message"]["content"]
                except json.JSONDecodeError as e:
                    print("Error decoding JSON:", e)  # Debug statement

        response = response.strip()

        with open(output_file, 'w') as f:
            json.dump({"prompt": message, "response": response}, f, indent=4)

        # Print the prompt and response
        print(f"User: {message}")
        print("Assistant:", response)

    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python bot.py <message>")
        return

    message = ' '.join(sys.argv[1:])
    output_file = "output.json"

    chat(message, output_file)
    print(f"Conversation saved to {output_file}")

if __name__ == "__main__":
    main()
