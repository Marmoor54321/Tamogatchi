# model/observer.py

class Observer:
    def update(self, event_name, data=None):
        pass

class Observable:
    def __init__(self):
        self._observers = []

    def add_observer(self, observer: Observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def notify_observers(self, event_name, data=None):
        for observer in self._observers:
            observer.update(event_name, data)