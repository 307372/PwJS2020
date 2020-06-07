# Projekt w języku skryptowym
## Temat: Narzędzie do automatyzacji wybranych czynności wykonywanych przy pomocy myszki i klawiatury
##### Przykładowe zastosowania:
* Gdy chcemy wykonać czynność, w momencie kiedy nie ma nas przy komputerze, np. pobieramy duży plik i zostawiamy komputer włączony na noc lub przed wyjściem do pracy, ale chcemy go wyłączyć po zakończeniu pobierania, to można użyć do tego makra aktywowanego z opóźnieniem.
* Można stworzyć makro, które naciska lewy przycisk myszy najszybciej jak to możliwe, co może być przydatne w grach, np. w shooterach korzystając z broni półautomatycznej przy jego użyciu można jej używać jak automatycznej.
* Przy obróbce filmów, jeśli robimy coś często i wymaga to dużo klikania, możemy ustawić sobie do tego odpowiednie makro, np. gdy na początku każdego filmu nad którym pracujemy chcemy wkleić intro, to potrzebne kliknięcia / skróty klawiszowe możemy sobie zapisać w formie makro i później wykonywać to jednym skrótem klawiszowym.
##### Planowane funkcje:
* Pewne:
  * Makra do myszy i klawiatury pisane z klawiatury
  * Autoclicker do przycisków na myszy i klawiaturze
  * Działanie programu w systemie windows
* Prawdopodobne:
  * Opcja "Nagrywania" makr zamiast pisania ich
  * Prosty password manager ( makra do klawiatury przechowywane w jakiś względnie bezpieczny sposób )

##### Technologie:
* UI: [Pyside2](https://pypi.org/project/PySide2/)
* Obsługa klawiatury: [keyboard](https://pypi.org/project/keyboard/)
* Obsługa myszy: [mouse](https://pypi.org/project/mouse/)
* Pewność, że program jest uruchomiony tylko raz: [pywin32](https://pypi.org/project/pywin32/)