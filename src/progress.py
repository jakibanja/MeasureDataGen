
import threading
import json
import time

class ProgressTracker:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ProgressTracker, cls).__new__(cls)
                cls._instance.progress = {}
                cls._instance.listeners = []
        return cls._instance

    def update(self, status, member_count=None, record_count=None, details=None):
        update_data = {
            'status': status,
            'timestamp': time.time()
        }
        if member_count is not None: update_data['member_count'] = member_count
        if record_count is not None: update_data['record_count'] = record_count
        if details is not None: update_data['details'] = details
        
        self.progress = update_data
        
        # Notify listeners
        for listener in self.listeners:
            listener(update_data)

    def add_listener(self, callback):
        self.listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self.listeners:
            self.listeners.remove(callback)

progress_tracker = ProgressTracker()
