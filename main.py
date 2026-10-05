import csv
import sys
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HOSTS = ("volby.cz", "www.volby.cz", "volby.gov.cz", "www.volby.gov.cz")
EXAMPLE = ('python main.py "https://www.volby.cz/pls/ps2017nss/ps32?'
           'xjazyk=CZ&xkraj=13&xnumnuts=7201" vysledky_kromeriz.csv')


def check_arguments(args):
    """Zkontroluje argumenty z příkazové řádky a vrátí odkaz a název
    souboru. Když něco nesedí, vypíše proč a ukončí program."""
    if len(args) != 3:
        print("Program potřebuje 2 argumenty: odkaz na územní celek "
              "a název výstupního souboru.")
        print("Příklad:", EXAMPLE)
        sys.exit(1)

    url, file_name = args[1], args[2]
    address = urlparse(url)
    if address.netloc not in HOSTS or \
            not address.path.endswith("/ps2017nss/ps32"):
        print("První argument musí být odkaz na územní celek z volby.cz "
              "(stránka se seznamem obcí, ve výsledcích sloupec "
              "'Výběr obce').")
        print("Příklad:", EXAMPLE)
        sys.exit(1)

    if not file_name.endswith(".csv"):
        print("Druhý argument musí být název souboru s koncovkou .csv.")
        sys.exit(1)

    return url, file_name


def download_page(session, url):
    response = session.get(url, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"
    return BeautifulSoup(response.text, "html.parser")


def to_number(text):
    # čísla jsou na webu s mezerou (nbsp) mezi tisíci, např. "13 104"
    return int(text.replace("\xa0", "").replace(" ", ""))


def get_municipalities(soup, url):
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


def get_results(soup):
    """Z výsledků jedné obce vytáhne voliče, obálky, platné hlasy
    a slovník hlasů pro jednotlivé strany."""
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


def save_csv(file_name, rows, parties):
    header = ["code", "location", "registered", "envelopes", "valid"]
    # utf-8-sig, aby Excel správně zobrazil diakritiku
    with open(file_name, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(header + parties)
        writer.writerows(rows)


def main():
    url, file_name = check_arguments(sys.argv)
    print("STAHUJI DATA Z VYBRANEHO URL:", url)

    session = requests.Session()
    parties = []
    results = []
    try:
        municipalities = get_municipalities(download_page(session, url), url)
        if not municipalities:
            print("Na stránce nejsou žádné obce, zkontroluj odkaz.")
            sys.exit(1)

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
    except requests.RequestException as error:
        print("\nNepodařilo se stáhnout data:", error)
        sys.exit(1)

    rows = []
    for code, name, registered, envelopes, valid, votes in results:
        party_votes = [votes.get(party, 0) for party in parties]
        rows.append([code, name, registered, envelopes, valid] + party_votes)

    print("UKLADAM DO SOUBORU:", file_name)
    save_csv(file_name, rows, parties)
    print("UKONCUJI election-scraper")


if __name__ == "__main__":
    main()
