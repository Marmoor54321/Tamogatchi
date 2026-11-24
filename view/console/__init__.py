# view/console/__init__.py
"""Małe widoki konsolowe (curses), z których składa się ConsoleView.

  canvas.py          - rysowanie na ekranie: kolory, ramki, bezpieczne addstr
  layout.py          - rozmieszczenie paneli na ekranie
  keys.py            - klawisze -> abstrakcyjne komendy dla kontrolera
  panel.py           - klasa bazowa panelu w ramce
  stats_panel.py     - kasa, rekord i paski statystyk
  pet_panel.py       - rysunek zwierzaka (skórka + nastrój, podgląd)
  message_panel.py   - ostatni komunikat
  menu_panel.py      - menu przekazane przez kontroler
  messages.py        - zdarzenie z modelu -> treść komunikatu
  minigame_screen.py - ekran minigry Dino
"""
