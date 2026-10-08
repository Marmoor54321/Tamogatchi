# model/observer.py

class Observer:
    """Interfejs dla widoków (nasłuchiwaczy)."""
    def update(self, event_name, data=None):
        pass

class Observable:
    """Klasa, po której dziedziczy Model. Pozwala dodawać obserwatorów i ich powiadamiać."""
    def __init__(self):
        self._observers = []

    def add_observer(self, observer: Observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def notify_observers(self, event_name, data=None):
        for observer in self._observers:
            observer.update(event_name, data)