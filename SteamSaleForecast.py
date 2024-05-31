import requests
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta

game = 'portal'
url = f'https://gg.deals/game/{game}/#price-history'
r = requests.get(url)
soup = bs(r.text, 'lxml')

dataUrl = 'https://gg.deals'+soup.select_one('#historical-chart-container')['data-without-keyshops-url']
r  = requests.get(dataUrl, headers={'X-Requested-With': 'XMLHttpRequest'})

data = r.json()['chartData']['retail']

today = datetime.now()
last_year = today - timedelta(days=1000)
filtered_data = [
    {'date': item['name'], 'price': item['y']}
    for item in data
    if datetime.fromtimestamp(item['x'] / 1000) >= last_year and datetime.fromtimestamp(item['x'] / 1000) <= today and item['shop'] == 'Steam'
]

# Extract dates and prices
dates = [d['date'] for d in filtered_data]
prices = [d['price'] for d in filtered_data]

# Extract dates where price is min
dates_low = [datetime.strptime(dates[i].split(' - ')[0], "%d %b %Y %H:%M") for i in range(len(filtered_data)) if prices[i] == min(prices)]

# Calculate durations between consecutive min prices
durations = [(dates_low[i+1] - dates_low[i]).days for i in range(len(dates_low)-1)]

# Calculate average duration
average_duration = sum(durations) / len(durations)

# Forecast the next occurrence
last_date = dates_low[-1]
forecasted_date = (last_date + timedelta(days=average_duration))

if (forecasted_date.day < 15):
    print("Forecasted date for the next lowest price is around beginning of", forecasted_date.strftime("%b"))
else:
    print("Forecasted date for the next lowest price is around end of", forecasted_date.strftime("%b"))
