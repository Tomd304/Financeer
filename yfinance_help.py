import yfinance as yf

#def ticker_info_dict(ticker):
#        company = {}
#        company["info"] = yf.Ticker(ticker).info
#        print(company["info"])
#        company["price"] = yf.Ticker(ticker).history(period='7d')
#        print(company["price"])
#        companyr = {
#                    "symbol":company["info"]["symbol"], 
#                    "name":company["info"]["shortName"], 
#                    "exchange":company["info"]["exchange"], 
#                    "currency":company["info"]["currency"],
#                    "price":company["price"]["Close"][-1]                    
#                    }
#        return companyr;

     

def filter_badhtml(str):
    print(str)
    newstr = str.replace("&#39", "'")
    print(newstr)
    return newstr



###############################   KEYS BELOW AVAILABLE IN INFO FROM ALL TYPES OF FINANCIAL ITEMS    #####################################

#previousClose
#regularMarketOpen
#twoHundredDayAverage        
#trailingAnnualDividendYield 
#payoutRatio
#volume24Hr
#regularMarketDayHigh        
#navPrice
#averageDailyVolume10Day     
#totalAssets
#regularMarketPreviousClose  
#fiftyDayAverage
#trailingAnnualDividendRate  
#open
#toCurrency
#averageVolume10days
#expireDate
#yield
#algorithm
#dividendRate
#exDividendDate
#beta
#circulatingSupply
#startDate
#regularMarketDayLow
#priceHint
#currency
#regularMarketVolume
#lastMarket
#maxSupply
#openInterest
#marketCap
#volumeAllCurrencies
#strikePrice
#averageVolume
#priceToSalesTrailing12Months
#dayLow
#ask
#ytdReturn
#askSize
#volume
#fiftyTwoWeekHigh
#forwardPE
#maxAge
#fromCurrency
#fiveYearAvgDividendYield    
#fiftyTwoWeekLow
#bid
#tradeable
#dividendYield
#bidSize
#dayHigh
#exchange
#shortName
#exchangeTimezoneName
#exchangeTimezoneShortName
#isEsgPopulated
#gmtOffSetMilliseconds
#quoteType
#symbol
#market
#regularMarketPrice
#logo_url