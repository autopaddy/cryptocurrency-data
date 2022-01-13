"""
    Purpose of this script is to collect the most up to date crypto data
    and process them into manifest files that can be used in any web application.
"""
from asyncio import futures
import base64
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from datetime import date
import json
import subprocess
import concurrent.futures
import os


def _shellCmd(cmd):
    # Executes shell commands returning an ascii decoded output and error
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True)
    out, err = proc.communicate()

    return out.decode('ascii'), err


def formatPriceEntry(_, date, price):
    # Format needed when writing to file
    return {date: {price: price}}


def getData(key):
    # Requests the coin data from coinmarketcap
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
        # Can't recover if we error here.  Exit the program.
        print(f"ERROR: Failed to fetch coin data from Coinmarketcap: {e}")
        exit(1)


def getDominantColor(id):
    # This script uses ImageMagick to process the image for its 2 most dominant colors.
    cmd = f"curl --silent https://s2.coinmarketcap.com/static/img/coins/32x32/{id}.png | magick identify -depth 6 -verbose png:- | sort -n - | tail -2 | awk '{{print $3}}'"
    out, err = _shellCmd(cmd)

    if err:
        print(f'WARNING failed to get dominant color for: {id}: {err}')
        return 'FFFFFFFF'
    else:
        # Split output into 1st & 2nd most dominant color
        # Most dominant is on the bottom.  That's why we're unpacking second -> first.
        second, first = out.splitlines()

        # Replace the end with FF to force color not to be transparent
        first = first[:-2] + 'FF'
        second = second[:-2] + 'FF'

        # If first choice is just pure white or pure black then use 2nd color
        # We do this because in most cases we get these color due to the background image
        if first == '#000000FF' or first == '#FFFFFFFF':
            return second

        return first


def parseData(data):
    # Returns a tuple with a new manfiest entry and a new coin price entry.
    return (
        {
            "id": data["id"],
            "name": data["name"],
            "symbol": data["symbol"],
            "rank": data["rank"],
            "color": getDominantColor(data["id"]),
            "icon": ''
        },
        {
            "id": data["id"],
            "date": date.today().strftime('%Y%m%d'),
            "price": data["quote"]["USD"]["price"]
        }
    )


def processSpotHQIcons(manifest):
    # Downloads and processes the cryptoicons.co icons.
    # Checks our existing manifest to make sure we've got a match for the coin.
    # The icon gets base64 encoded which can be used inline in your application.
    zipFile = '/tmp/cryptoicons.zip'
    dir = '/tmp/_cryptoicons'

    curlCmd = f'curl --silent https://codeload.github.com/spothq/cryptocurrency-icons/zip/master > {zipFile}'
    unzipCmd = f'unzip -d {dir} {zipFile}'

    _, curlErr = _shellCmd(curlCmd)
    _, unzipErr = _shellCmd(unzipCmd)

    if curlErr:
        print(f'ERROR: unable to download cryptoicons: {curlErr}')
        exit(1)

    if unzipErr:
        print(f'ERROR: print failed to unzip: {unzipErr}')
        exit(1)

    with open(f'{dir}/cryptocurrency-icons-master/manifest.json', 'r') as spotHQManifest:
        contents = json.loads(spotHQManifest.read())

        for item in manifest:
            if any(d['name'].lower() == item['name'].lower() and d['symbol'].lower() == item['symbol'].lower() for d in contents):
                print(f"Adding spotHQ icon for {item['name']} to the manifest")

                # Find the color entry in the spothq manifest and use it for our entry.
                for _item in contents:
                    if (_item['name'] == item['name']):
                        item['color'] = _item['color']
                        break

                with open(f'{dir}/cryptocurrency-icons-master/svg/color/{item["symbol"].lower()}.svg', 'rb') as svgFile:
                    svg = svgFile.read()
                    svg64 = f'data:image/svg+xml;base64,{base64.b64encode(svg)}'
                    item['icon'] = svg64

    return manifest


if __name__ == "__main__":
    key = os.environ.get('CMC_API_KEY')
    if not key:
        print('No key was provided - exiting!')
        exit(1)

    manifest = []
    with open('manifest.json', 'r') as manifestJson:
        manifest = json.loads(manifestJson.read())

    data = getData(key)
    manifest = []
    coins = []

    with concurrent.futures.ProcessPoolExecutor(40) as e:
        futures = [e.submit(parseData, entry) for entry in data]
        for r in concurrent.futures.as_completed(futures):
            result = r.result()
            print(f"proccessing {result[0]['name']}")

            manifest.append(result[0])
            coins.append(result[1])

    for coin in coins:
        finalCoin = []
        finalCoin.append(formatPriceEntry(coin))

        file = f"cryptocurrency/{coin['id']}.json"
        # Get all the current coin data up to this point
        if os.path.isfile(file):
            with open(file, 'r') as coinJson:
                contents = json.loads(coinJson.read())
                for c in contents:
                    # Already formatted so don't need to call formatPriceEntry
                    finalCoin.append(c)

        # Write the new entry to file
        with open(file, 'w') as coinJson:
            coinJson.write(json.dumps(finalCoin))

    # Prioritise using icons from SpotHQ
    manifest = processSpotHQIcons(manifest)

    # Sort manifest, in place, by rank
    manifest.sort(key=lambda x: x['rank'], reverse=False)

    # Overwrite the existing manifest JSON
    with open('manifest.json', 'w') as manifestJson:
        manifestJson.write(json.dumps(manifest))
