# DISCONTINUED
### NOTE:  You may still find value in this project in the `generate.py` script for pulling in icons from CoinMarketCap and identifying the dominant colors for all the icons.  Alternatively you can find these colors in the `cryptocurrency.json` manifest.



# cryptocurrency-data

This repository is meant to provide cryptocurrency data for hobbyists looking to build their own websites.  It provides basic data and access to all of the cryptocurrency icons ( available on CoinMarketcap ).

--------------

`cryptocurrency.json` contains the current symbol, name, ranks as well icon data ( dominant color for theming, icon url and for some icons: base64 encoded svg representing the icon. )

`currency.json` contains a large selection of currency data and current exchange rates to the USD.

`cryptocurrency/*.json` contains current and historic price data for all cryptocurrencies listed in the manifest.  *NOTE* this isn't a full history for the coin.  If you want a full price history you should look at using CoinMarketcap or Coin Gecko APIs.

------------
All the data in this repository is updated nightly.

