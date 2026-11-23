"""Projekt 3: Elections Scraper: výsledky voleb 2017 pro vybraný okres do CSV."""

import csv
import sys
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

HOSTS = ("volby.cz", "www.volby.cz", "volby.gov.cz", "www.volby.gov.cz")
EXAMPLE = ('python main.py "https://www.volby.cz/pls/ps2017nss/ps32?'
           'xjazyk=CZ&xkraj=13&xnumnuts=7201" vysledky_kromeriz.csv')
Municipality = tuple[str, str, str]  # kód, název, odkaz na výsledky


def stop(message: str) -> None:
    """Vypíše chybu s příkladem správného spuštění a ukončí program."""
    print(message)
    print("Příklad:", EXAMPLE)
    sys.exit(1)


def check_arguments(args: list[str]) -> tuple[str, str]:
    """Zkontroluje argumenty z příkazové řádky.

    Vrátí odkaz a název souboru. Když něco nesedí, vypíše proč
    a ukončí program.
    """
    if len(args) != 3:
        stop("Program potřebuje 2 argumenty: odkaz na územní celek "
             "a název výstupního souboru.")
    url, file_name = args[1], args[2]
    if not is_district_url(url):
        stop("První argument musí být odkaz na územní celek z volby.cz "
             "(seznam obcí, ve výsledcích sloupec 'Výběr obce').")
    if not file_name.endswith(".csv"):
        stop("Druhý argument musí být název souboru s koncovkou .csv.")
    return url, file_name


def is_district_url(url: str) -> bool:
    """Ověří, že odkaz vede na seznam obcí územního celku z roku 2017."""
    address = urlparse(url)
    params = parse_qs(address.query)
    return (address.scheme == "https" and address.netloc in HOSTS
            and address.path.endswith("/ps2017nss/ps32")
            and "xkraj" in params and "xnumnuts" in params)


def download_page(session: requests.Session, url: str) -> BeautifulSoup:
    """Stáhne stránku, kódování z jejích bajtů rozpozná BeautifulSoup."""
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser")


def to_number(text: str) -> int:
    """Převede číslo z webu na int, mezi tisíci je mezera (nbsp).

    Pomlčka znamená, že strana v obci nekandidovala, a počítá se jako 0.
    """
    cleaned = text.replace("\xa0", "").replace(" ", "").strip()
    if cleaned == "-":
        return 0
    if not cleaned.isdigit():
        raise ValueError(f"Místo čísla je na stránce text '{text}'.")
    return int(cleaned)


def find_cell(soup: BeautifulSoup, header: str) -> Tag:
    """Najde buňku tabulky podle atributu headers, jinak vyvolá chybu."""
    cell = soup.find("td", headers=header)
    if cell is None:
        raise ValueError(f"Na stránce chybí buňka '{header}', "
                         "web asi změnil strukturu.")
    return cell


def get_municipalities(soup: BeautifulSoup, url: str) -> list[Municipality]:
    """Vrátí seznam obcí ve tvaru (kód, název, odkaz na výsledky)."""
    municipalities = []
    for cell in soup.find_all("td", class_="cislo"):
        link = cell.find("a")
        name_cell = cell.find_next_sibling("td")
        if link is None or name_cell is None or not link.get("href"):
            continue
        municipalities.append((link.get_text(strip=True),
                               name_cell.get_text(strip=True),
                               urljoin(url, link["href"])))
    return municipalities


def get_results(soup: BeautifulSoup) -> tuple[int, int, int, dict[str, int]]:
    """Vytáhne výsledky jedné obce.

    Vrátí počet voličů, vydaných obálek, platných hlasů a slovník
    hlasů pro jednotlivé strany.
    """
    registered = to_number(find_cell(soup, "sa2").get_text())
    envelopes = to_number(find_cell(soup, "sa3").get_text())
    valid = to_number(find_cell(soup, "sa6").get_text())

    # strany jsou rozdělené do dvou tabulek (t1 a t2)
    names = soup.find_all("td", headers=["t1sb2", "t2sb2"])
    counts = soup.find_all("td", headers=["t1sb3", "t2sb3"])
    if not names or len(names) != len(counts):
        raise ValueError("Počet stran a počet hlasů na stránce nesedí.")

    votes = {}
    for name, count in zip(names, counts):
        votes[name.get_text(strip=True)] = to_number(count.get_text())
    return registered, envelopes, valid, votes


def save_csv(file_name: str, rows: list[list[Any]], parties: list[str]
             ) -> None:
    """Uloží výsledky obcí do CSV souboru včetně hlavičky."""
    header = ["code", "location", "registered", "envelopes", "valid"]
    # utf-8-sig, aby Excel správně zobrazil diakritiku
    with open(file_name, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(header + parties)
        writer.writerows(rows)


def scrape_municipalities(session: requests.Session,
                          municipalities: list[Municipality]
                          ) -> tuple[list[tuple], list[str]]:
    """Stáhne výsledky všech obcí.

    Vrátí výsledky obcí a seznam stran v pořadí, v jakém se na webu objevily.
    """
    parties = []
    results = []
    for number, (code, name, link) in enumerate(municipalities, 1):
        print(f"\robec {number}/{len(municipalities)}", end="")
        try:
            page = download_page(session, link)
            registered, envelopes, valid, votes = get_results(page)
        except ValueError as error:
            raise ValueError(f"obec {name} ({code}): {error}") from error
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

    try:
        # with zajistí zavření session i při chybě
        with requests.Session() as session:
            page = download_page(session, url)
            municipalities = get_municipalities(page, url)
            if not municipalities:
                print("Na stránce nejsou žádné obce, zkontroluj odkaz.")
                sys.exit(1)
            results, parties = scrape_municipalities(session, municipalities)
    except requests.RequestException as error:
        print("\nNepodařilo se stáhnout data:", error)
        sys.exit(1)
    except ValueError as error:
        print("\nNepodařilo se zpracovat data,", error)
        sys.exit(1)

    print("UKLADAM DO SOUBORU:", file_name)
    try:
        save_csv(file_name, build_rows(results, parties), parties)
    except OSError as error:
        print("Nepodařilo se uložit soubor:", error)
        sys.exit(1)
    print("UKONCUJI election-scraper")


if __name__ == "__main__":
    main()
