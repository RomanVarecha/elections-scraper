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


def main():
    url, file_name = check_arguments(sys.argv)
    print("STAHUJI DATA Z VYBRANEHO URL:", url)

    session = requests.Session()
    municipalities = get_municipalities(download_page(session, url), url)
    for code, name, link in municipalities:
        print(code, name, link)
    print("Počet obcí:", len(municipalities))


if __name__ == "__main__":
    main()
