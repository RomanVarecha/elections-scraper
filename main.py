import sys
from urllib.parse import urlparse

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


def main():
    url, file_name = check_arguments(sys.argv)
    print("STAHUJI DATA Z VYBRANEHO URL:", url)


if __name__ == "__main__":
    main()
