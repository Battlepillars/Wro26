# Testprotokoll – Nachweiskette für die Performance-Kennzahlen

Dieses Dokument macht die Kennzahlen aus [Kapitel 3 ("Testmethodik und Performance-Kennzahlen")](../README.md#testmethodik-und-performance-kennzahlen) im [Haupt-README](../README.md) nachvollziehbar. Für jede dort genannte Zahl wird hier festgehalten: **wann/womit gemessen, wie groß die Stichprobe, wo die Rohdaten liegen, wie die Kennzahl berechnet wurde und welche Code-Änderung daraus resultierte.**

Ziel ist die Kette **README → Testaufbau → Rohdaten/Logs → Berechnung → Ergebnis**, statt einer reinen Behauptung eines Messwerts.

## Format

Jeder Testeintrag (`T-XX`) enthält:

| Feld | Bedeutung |
|---|---|
| **Datum / Firmware-Version** | Wann getestet, mit welchem Software-/Firmwarestand (Commit-Hash oder Tag) |
| **Testziel** | Welche Frage/Hypothese wird geprüft |
| **Testaufbau** | Strecke, Matte, Anzahl Läufe, Messmethode |
| **Stichprobengröße (N)** | Anzahl Runden/Versuche, aus denen die Kennzahl berechnet wurde |
| **Rohdaten / Logdatei** | Verweis auf die konkrete(n) Log-/Datendatei(en) dieser Testreihe |
| **Kennzahl** | Was genau berechnet wird (Formel/Definition) |
| **Ergebnis** | Gemessener Wert, wie im README zitiert |
| **Resultierende Änderung** | Welche Code-/Konstruktionsänderung aus dem Ergebnis folgte |

## Bekannte Einschränkung: Archivierung der Rohdaten

`logger.py` schreibt jeden Testlauf nach `logs/log_1.txt` … `log_10.txt` (Ringpuffer, `MAX_LOGS = 10` – ältere Läufe werden beim nächsten Start automatisch überschrieben). Sowohl `logs/` als auch `src/pi/logs/` stehen zusätzlich in der [.gitignore](../.gitignore) und werden daher nicht im Repository versioniert.

Das bedeutet: Für die unten dokumentierten Testreihen liegen die Original-Logdateien aktuell **nur lokal bei uns**, nicht in diesem Repository. 

**Konsequenz für neue Testreihen:** Ab sofort kopieren wir die relevanten Logs jeder offiziellen Testreihe zusätzlich nach `tests/data/<Test-ID>/` (dieser Ordner heißt bewusst nicht `logs/`, damit er nicht von der `.gitignore`-Regel erfasst wird und damit versioniert werden kann).

---

<a id="t-01"></a>

## T-01 – Lenkungs-Interventionen pro Runde

- **Datum / Firmware-Version:** 15.04.2026 
- **Testziel:** Prüfen, wie oft `pidSteer`/`pidSteer2` pro Runde über einem Schwellwert korrigieren müssen (Indikator für Kurvenstabilität)
- **Testaufbau:** 12 vollständige Runden auf der Wettbewerbsmatte, gleiche Streckenkonfiguration; jede Korrektur über Schwellwert wird via `logger.log()` protokolliert
- **Stichprobengröße:** N = 12 Runden

- **Kennzahl:** Mittelwert und Standardabweichung der Interventionen pro Runde
- **Ergebnis:** Ø 12,4 Interventionen/Runde (σ = 2,1)
- **Resultierende Änderung:** Zweiter P-Regler `pidSteer2` mit kleinerem Kp-Wert eingeführt (siehe Fehler 3 in der [Softwareverbesserungstabelle](../README.md#tabelle-x-softwareverbesserungen))

<a id="t-02"></a>

## T-02 – Erkennungsrate Hindernisfarbe

- **Datum / Firmware-Version:** 05.05.2026
- **Testziel:** Klassifikationsgenauigkeit der Rot-/Grün-Maskenpipeline unter wechselnden Lichtbedingungen prüfen
- **Testaufbau:** 148 einzelne Hindernis-Erkennungsversuche mit `cameraAIO.py`, Ground Truth (tatsächliche Farbe) manuell protokolliert und mit Pipeline-Ausgabe verglichen
- **Stichprobengröße:** N = 148 Erkennungsversuche

- **Kennzahl:** Anteil korrekt klassifizierter Hindernisse = korrekt / N
- **Ergebnis:** 142 von 148 korrekt (95,9 %)
- **Resultierende Änderung:** HSV-Grenzwerte in `cameraAIO.py` angepasst (siehe Fehler 1 in der [Softwareverbesserungstabelle](../README.md#tabelle-x-softwareverbesserungen))

<a id="t-03"></a>

## T-03 – Rundenzeit-Konsistenz (vorher/nachher Vollscan)

- **Datum / Firmware-Version:** 18.04.2026 
- **Testziel:** Auswirkung der Vollscan-Strategie (Kamera auf 27 cm) auf die Rundenzeit messen
- **Testaufbau:** Laufzeitmessung mehrerer Läufe auf derselben Strecke, jeweils vor und nach der Umstellung; Zeitstempel über Stoppuhr und `logger.log()`
- **Stichprobengröße:** N = mehrere Läufe vorher / mehrere Läufe nachher 

- **Kennzahl:** Mittelwert und Standardabweichung der Laufzeit pro Gruppe
- **Ergebnis:** vorher Ø 56 s (σ = 4,2 s) → nachher Ø 38 s (σ = 2,3 s)
- **Resultierende Änderung:** Umstieg auf Vollscan-Strategie vor dem Start (siehe Fehler 4 in der [Softwareverbesserungstabelle](../README.md#tabelle-x-softwareverbesserungen); Konstruktionshintergrund in [Kamera](../README.md#kamera-verwendung-der-kamera-und-kalibrierung))

<a id="t-04"></a>

## T-04 – Recovery-Erfolgsrate

- **Datum / Firmware-Version:** 05.06.2026
- **Testziel:** Erfolgsquote der Recovery-Manöver nach Sensor-/Wandverlust prüfen (betrifft Fehler 6–8: Wandverlust-Rückwärtsfahrt, Encoder-Fallback, Park-Korrektur)
- **Testaufbau:** Gezieltes Herbeiführen von Wandverlust bzw. Sensorausfall in 30 Durchläufen; Beobachtung, ob das jeweilige Recovery-Manöver den Roboter korrekt fortsetzt
- **Stichprobengröße:** N = 30 Durchläufe

- **Kennzahl:** Anteil erfolgreicher Recoveries = erfolgreich / N
- **Ergebnis:** 27 von 30 erfolgreich (90,0 %)
- **Resultierende Änderung:** Encoder-Fallback in `driveController.py` (Fehler 7), Positions-/Abstandsprüfung in `parkCW()` (Fehler 8) – siehe [Softwareverbesserungstabelle](../README.md#tabelle-x-softwareverbesserungen)

<a id="t-05"></a>

## T-05 – Erfolgsquote vollständiger Testläufe

- **Datum / Firmware-Version:** 12.06.2026 
- **Testziel:** Gesamtsystem-Zuverlässigkeit messen: Anteil vollständig und regelkonform abgeschlossener Läufe (Hindernisrennen)
- **Testaufbau:** 20 vollständige End-to-End-Testläufe auf der Wettbewerbsmatte
- **Stichprobengröße:** N = 20 Läufe
- **Rohdaten / Logdatei:** TODO – `tests/data/T-05/`
- **Kennzahl:** Erfolgsquote = vollständig+regelkonform / N; zusätzlich Mittelwert und Standardabweichung der Laufzeit
- **Ergebnis:** 18 von 20 Läufen erfolgreich (90,0 %); mittlere Zeit 38 s, σ = 2,3 s
- **Resultierende Änderung:** Kumulierter Effekt aller oben genannten Einzeländerungen (T-01 bis T-04)

---

## Offene Punkte / nächste Schritte

- [ ] Die *(geschätzt)* markierten Datumswerte (aus der [Meilenstein-Tabelle](../README.md#tabelle-x-meilensteine-der-entwicklung) abgeleitet) gegen die tatsächlichen Testdaten prüfen und den Zusatz „geschätzt“ nach Bestätigung entfernen
- [ ] Exakte Commit-Hashes/Tags der jeweiligen Firmwarestände ergänzen (ersetzen „Commit-Hash/Tag noch bestätigen“)
- [ ] Zugehörige Logdateien/Rohdaten nach `tests/data/<Test-ID>/` kopieren und committen
- [ ] Für neue Testreihen: nächste freie `T-XX`-Nummer vergeben, Eintrag nach obigem Format ergänzen und bei Bedarf im [README](../README.md#testmethodik-und-performance-kennzahlen) verlinken
