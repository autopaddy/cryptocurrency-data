"""
    Purpose of this script is to collect the most up to date crypto data
    and process them into manifest files that can be used.
"""
from asyncio import futures
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from datetime import date
import json
import subprocess
import concurrent.futures
import os

# Fetch data from coin tracker tool


def getData(key):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    parameters = {
        'start': '1',
        'limit': '5000',
        'convert': 'USD'
    }

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': key,
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        return json.loads(response.text)["data"]

    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
        exit(1)


def getDominantColor(id):
    cmd = f"curl --silent https://s2.coinmarketcap.com/static/img/coins/32x32/{id}.png | magick identify -depth 6 -verbose png:- | sort -n - | tail -1 | awk '{{print $3}}'"

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True)
    out, err = proc.communicate()

    if err:
        print(err)
        return 'FFFFFFFF'
    else:
        output = out.decode('ascii')
        # Ensures none of the icons of transparent
        output = output[:-3] + 'FF'
        return output


def parseData(data):
    return (
        {
            "id": data["id"],
            "name": data["name"],
            "symbol": data["symbol"],
            "color": getDominantColor(data["id"])
        },
        {
            "id": data["id"],
            "date": date.today().strftime('%Y-%m-%d'),
            "price": data["quote"]["USD"]["price"]
        }
    )


    # Find dominant color of the icon
    # Create the main manifest file ( unique ID,  coinmarketcap ID, name, symbol, slug, iconSrc, color )
    # Create individual JSON files for each coin containing price data.
if __name__ == "__main__":
    # DO NOT COMMIT THIS!!
    data = getData(os.environ.get('CMC_API_KEY'))
    manifest = []
    coins = []

    with concurrent.futures.ProcessPoolExecutor(40) as e:
        futures = [e.submit(parseData, entry) for entry in data]
        for r in concurrent.futures.as_completed(futures):
            result = r.result()
            print(f"proccessing {result[0]['name']}")

            manifest.append(result[0])
            coins.append(result[1])

    # Overwrite the existing manifest JSON
    with open('manifest.json', 'w+') as manifestJson:
        manifestJson.write(json.dumps(manifest))

    for coin in coins:
        finalCoin = []
        finalCoin.append(coin)
        file = f"cryptocurrency/{coin['id']}.json"
        # Get all the current coin data up to this point
        if os.path.isfile(file):
            with open(file, 'r') as coinJson:
                contents = json.loads(coinJson.read())
                for c in contents:
                    finalCoin.append(c)

        # Write the new entry to file
        with open(file, 'w') as coinJson:
            coinJson.write(json.dumps(finalCoin))
