# Elections Scraper

Třetí projekt na Engeto Online Python Akademii.

## Popis projektu

Skript stahuje výsledky parlamentních voleb v roce 2017 pro vybraný územní
celek (okres). Výsledky jsou na webu
[volby.cz](https://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ).

Pro každou obec v okrese uloží do CSV souboru:

- kód obce
- název obce
- počet voličů v seznamu
- počet vydaných obálek
- počet platných hlasů
- počet hlasů pro každou kandidující stranu

## Instalace knihoven

Potřebné knihovny jsou v souboru `requirements.txt`. Nejlepší je nainstalovat
je do nového virtuálního prostředí:

```
python -m venv venv
source venv/bin/activate        # na Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Spuštění projektu

Skript se spouští se dvěma argumenty:

```
python main.py <odkaz-na-uzemni-celek> <vystupni-soubor.csv>
```

Odkaz získáš tak, že na stránce s výsledky klikneš u vybraného okresu na `X`
ve sloupci „Výběr obce“ a zkopíruješ adresu stránky. Pokud chybí některý
z argumentů nebo odkaz nevede na seznam obcí, program na to upozorní
a skončí.

## Ukázka projektu

Výsledky hlasování pro okres Kroměříž:

1. argument: `https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=13&xnumnuts=7201`
2. argument: `vysledky_kromeriz.csv`

Spuštění programu:

```
python main.py "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=13&xnumnuts=7201" vysledky_kromeriz.csv
```

Průběh stahování:

```
STAHUJI DATA Z VYBRANEHO URL: https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=13&xnumnuts=7201
obec 79/79
UKLADAM DO SOUBORU: vysledky_kromeriz.csv
UKONCUJI election-scraper
```

Částečný výstup:

```
code,location,registered,envelopes,valid,Občanská demokratická strana,Řád národa - Vlastenecká unie,...
588300,Bařice-Velké Těšany,374,269,268,15,0,...
588326,Bezměrov,426,270,264,20,0,...
542318,Blazice,172,120,120,10,0,...
```

Celý výstup je v souboru `vysledky_kromeriz.csv`.
