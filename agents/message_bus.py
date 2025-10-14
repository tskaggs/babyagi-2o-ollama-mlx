# agents/message_bus.py
import threading
import time


class MessageBus:
    def __init__(self):
        self.messages = []
        self.lock = threading.Lock()

    def send(self, sender, recipient, content):
        with self.lock:
            self.messages.append({
                'sender': sender,
                'recipient': recipient,
                'content': content,
                'timestamp': time.time()
            })

    def receive(self, recipient, since=0):
        with self.lock:
            return [msg for msg in self.messages if (msg['recipient'] == recipient or msg['recipient'] == 'all') and msg['timestamp'] > since]
