"""Elections Scraper: výsledky voleb 2017 pro vybraný okres do CSV."""

import csv
import sys
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HOSTS = ("volby.cz", "www.volby.cz", "volby.gov.cz", "www.volby.gov.cz")
EXAMPLE = ('python main.py "https://www.volby.cz/pls/ps2017nss/ps32?'
           'xjazyk=CZ&xkraj=13&xnumnuts=7201" vysledky_kromeriz.csv')


def check_arguments(args: list[str]) -> tuple[str, str]:
    """Zkontroluje argumenty z příkazové řádky.

    Vrátí odkaz a název souboru. Když něco nesedí, vypíše proč
    a ukončí program.
    """
    if len(args) != 3:
        print("Program potřebuje 2 argumenty: odkaz na územní celek "
              "a název výstupního souboru.")
        print("Příklad:", EXAMPLE)
        sys.exit(1)

    url, file_name = args[1], args[2]
    address = urlparse(url)
    if (address.netloc not in HOSTS
            or not address.path.endswith("/ps2017nss/ps32")):
        print("První argument musí být odkaz na územní celek z volby.cz "
              "(stránka se seznamem obcí, ve výsledcích sloupec "
              "'Výběr obce').")
        print("Příklad:", EXAMPLE)
        sys.exit(1)

    if not file_name.endswith(".csv"):
        print("Druhý argument musí být název souboru s koncovkou .csv.")
        sys.exit(1)

    return url, file_name


def download_page(session: requests.Session, url: str) -> BeautifulSoup:
    """Stáhne stránku a vrátí ji jako BeautifulSoup objekt."""
    response = session.get(url, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"
    return BeautifulSoup(response.text, "html.parser")


def to_number(text: str) -> int:
    """Převede číslo z webu na int, mezi tisíci je mezera (nbsp)."""
    return int(text.replace("\xa0", "").replace(" ", ""))


def get_municipalities(
    soup: BeautifulSoup, url: str
) -> list[tuple[str, str, str]]:
    """Vrátí seznam obcí ve tvaru (kód, název, odkaz na výsledky)."""
    municipalities = []
    for cell in soup.find_all("td", class_="cislo"):
        link = cell.find("a")
        if not link:
            continue
        name = cell.find_next_sibling("td").get_text(strip=True)
        municipalities.append(
            (link.get_text(strip=True), name, urljoin(url, link["href"]))
        )
    return municipalities


def get_results(soup: BeautifulSoup) -> tuple[int, int, int, dict[str, int]]:
    """Vytáhne výsledky jedné obce.

    Vrátí počet voličů, vydaných obálek, platných hlasů a slovník
    hlasů pro jednotlivé strany.
    """
    registered = to_number(soup.find("td", headers="sa2").get_text())
    envelopes = to_number(soup.find("td", headers="sa3").get_text())
    valid = to_number(soup.find("td", headers="sa6").get_text())

    # strany jsou rozdělené do dvou tabulek (t1 a t2)
    names = soup.find_all("td", headers=["t1sb2", "t2sb2"])
    counts = soup.find_all("td", headers=["t1sb3", "t2sb3"])
    votes = {}
    for name, count in zip(names, counts):
        if count.get_text(strip=True) == "-":
            continue
        votes[name.get_text(strip=True)] = to_number(count.get_text())

    return registered, envelopes, valid, votes


def save_csv(
    file_name: str, rows: list[list[Any]], parties: list[str]
) -> None:
    """Uloží výsledky obcí do CSV souboru včetně hlavičky."""
    header = ["code", "location", "registered", "envelopes", "valid"]
    # utf-8-sig, aby Excel správně zobrazil diakritiku
    with open(file_name, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(header + parties)
        writer.writerows(rows)


def scrape_municipalities(
    session: requests.Session, municipalities: list[tuple[str, str, str]]
) -> tuple[list[tuple], list[str]]:
    """Stáhne výsledky všech obcí.

    Vrátí výsledky obcí a seznam stran v pořadí, v jakém se na webu objevily.
    """
    parties = []
    results = []
    for number, (code, name, link) in enumerate(municipalities, 1):
        print(f"\robec {number}/{len(municipalities)}", end="")
        registered, envelopes, valid, votes = get_results(
            download_page(session, link)
        )
        for party in votes:
            if party not in parties:
                parties.append(party)
        results.append((code, name, registered, envelopes, valid, votes))
    print()
    return results, parties


def build_rows(results: list[tuple], parties: list[str]) -> list[list[Any]]:
    """Převede výsledky obcí na řádky CSV, chybějící strana má 0 hlasů."""
    rows = []
    for code, name, registered, envelopes, valid, votes in results:
        party_votes = [votes.get(party, 0) for party in parties]
        rows.append([code, name, registered, envelopes, valid] + party_votes)
    return rows


def main() -> None:
    """Stáhne výsledky všech obcí z okresu a uloží je do CSV."""
    url, file_name = check_arguments(sys.argv)
    print("STAHUJI DATA Z VYBRANEHO URL:", url)

    session = requests.Session()
    try:
        municipalities = get_municipalities(download_page(session, url), url)
        if not municipalities:
            print("Na stránce nejsou žádné obce, zkontroluj odkaz.")
            sys.exit(1)
        results, parties = scrape_municipalities(session, municipalities)
    except requests.RequestException as error:
        print("\nNepodařilo se stáhnout data:", error)
        sys.exit(1)

    print("UKLADAM DO SOUBORU:", file_name)
    save_csv(file_name, build_rows(results, parties), parties)
    print("UKONCUJI election-scraper")


if __name__ == "__main__":
    main()
