import pickle
import requests
import bs4


# Scrapes a list of company tickers from Wikipedia and places them into a pickle file.
def save_sp500_tickers():
    """

    :return:
    """
    print("Grabbing tickers")
    resp = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    soup = bs4.BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", {"id": "constituents"})

    tickers = []
    for row in table.findAll("tr")[1:]:
        ticker = row.findAll("td")[0].text.replace('\n', '')
        if "." in ticker:
            ticker = ticker.replace('.', '-')
        tickers.append(ticker)

    with open("sp500ticker.pickle", "wb") as f:
        pickle.dump(tickers, f)

    # TODO: Delete csv files that do not appear in the ticker list anymore.

    return tickers