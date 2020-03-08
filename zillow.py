from lxml import html
import requests
import unicodecsv as csv
import argparse
import json
import io
from zipcodes import get_all_zipcodes_of_city


def clean(text):
    if text:
        return ' '.join(' '.join(text).split())
    return None


def get_headers():
    # Creating headers.
    headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
               'accept-encoding': 'gzip, deflate, sdch, br',
               'accept-language': 'en-GB,en;q=0.8,en-US;q=0.6,ml;q=0.4',
               'cache-control': 'max-age=0',
               'upgrade-insecure-requests': '1',
               'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'}
    return headers


def create_url(zipcode, filter):
    # Creating Zillow URL based on the filter.

    if filter == "newest":
        url = "https://www.zillow.com/homes/for_sale/{0}/0_singlestory/days_sort".format(zipcode)
    elif filter == "cheapest":
        url = "https://www.zillow.com/homes/for_sale/{0}/0_singlestory/pricea_sort/".format(zipcode)
    else:
        url = "https://www.zillow.com/homes/for_sale/{0}_rb/?fromHomePage=true&shouldFireSellPageImplicitClaimGA=false&fromHomePageTab=buy".format(zipcode)
    print(url)
    return url


def save_to_file(response):
	with io.open("response.html", "w", encoding="utf-8") as fp:
		fp.write(response.text)


def write_data_to_csv(data, count):
    # saving scraped data to csv.

    with open("properties-aggregated_5.csv", 'ab') as csvfile:
        fieldnames = ['title', 'city', 'state', 'postal_code', 'zestimate', 'rentZestimate', 'price', 'yearBuilt', 'area', 'daysOnZillow', 'facts and features', 'real estate provider', 'url', 'P2R']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if count==0:
            writer.writeheader()
        for row in data:
            writer.writerow(row)


def get_response(url):
    # Getting response from zillow.com.

    for i in range(5):
        response = requests.get(url, headers=get_headers())
        print("status code received:", response.status_code)
        if response.status_code != 200:
            # saving response to file for debugging purpose.
            save_to_file(response)
            continue
        else:
            save_to_file(response)
            return response
    return None

def remove_dollar_and_comma(price):
    price = price.replace(',', '')
    price = price.replace('$', '')
    return price

def get_data_from_json(raw_json_data):
    # getting data from json (type 2 of their A/B testing page)

    cleaned_data = clean(raw_json_data).replace('<!--', "").replace("-->", "")
    properties_list = []


    try:
        json_data = json.loads(cleaned_data)
        search_results = json_data.get('searchResults').get('listResults', [])

        with open('sample_json.txt', 'w') as f:
            f.write(str(json_data))
            f.close


        for properties in search_results:
            property_info = properties.get('hdpData', {}).get('homeInfo')
            city = property_info.get('city')
            state = property_info.get('state')
            postal_code = property_info.get('zipcode')
            zestimate = property_info.get('zestimate')
            rentZestimate = property_info.get('rentZestimate')
            price = remove_dollar_and_comma(properties.get('price')) if properties.get('price') is not None else '0'
            yearBuilt = property_info.get('yearBuilt')
            daysOnZillow = property_info.get('daysOnZillow')
            bedrooms = properties.get('beds')
            bathrooms = properties.get('baths')
            area = properties.get('area')
            info = f'{bedrooms} beds, {bathrooms} baths'
            broker = properties.get('brokerName')
            property_url = properties.get('detailUrl')
            title = properties.get('statusText')
            # TODO days_on_market = properties.get('variableData').get('text')

            if zestimate not in [None, ''] and rentZestimate not in [None, '']:
                price_to_rent =str(int(zestimate)/(12*int(rentZestimate)))
            elif price not in [None, ''] and rentZestimate not in [None, '']:
                price_to_rent = str(int(price)/(12*int(rentZestimate)))
            else:
                price_to_rent = 0

            data = {'city': city,
                    'state': state,
                    'postal_code': postal_code,
                    'zestimate': zestimate,
                    'rentZestimate' : rentZestimate,
                    'price': price,
                    'yearBuilt' : yearBuilt,
                    'area': area,
                    'daysOnZillow' : daysOnZillow,
                    'facts and features': info,
                    'real estate provider': broker,
                    'url': property_url,
                    'title': title,
                    'P2R': price_to_rent}
            properties_list.append(data)

        return properties_list

    #except ValueError:
    except Exception as e:
        #print("Invalid json")
        print(e)
        return None


def parse(zipcode, filter=None):
    url = create_url(zipcode, filter)
    response = get_response(url)

    if not response:
        print("Failed to fetch the page, please check `response.html` to see the response received from zillow.com.")
        return None

    parser = html.fromstring(response.text)
    search_results = parser.xpath("//div[@id='search-results']//article")

    if not search_results:
        print("parsing from json data")
        # identified as type 2 page
        raw_json_data = parser.xpath('//script[@data-zrr-shared-data-key="mobileSearchPageStore"]//text()')
        return get_data_from_json(raw_json_data)

    print("parsing from html page")
    properties_list = []
    for properties in search_results:
        raw_address = properties.xpath(".//span[@itemprop='address']//span[@itemprop='streetAddress']//text()")
        raw_city = properties.xpath(".//span[@itemprop='address']//span[@itemprop='addressLocality']//text()")
        raw_state = properties.xpath(".//span[@itemprop='address']//span[@itemprop='addressRegion']//text()")
        raw_postal_code = properties.xpath(".//span[@itemprop='address']//span[@itemprop='postalCode']//text()")
        raw_price = properties.xpath(".//span[@class='zsg-photo-card-price']//text()")
        raw_info = properties.xpath(".//span[@class='zsg-photo-card-info']//text()")
        raw_broker_name = properties.xpath(".//span[@class='zsg-photo-card-broker-name']//text()")
        url = properties.xpath(".//a[contains(@class,'overlay-link')]/@href")
        raw_title = properties.xpath(".//h4//text()")

        address = clean(raw_address)
        city = clean(raw_city)
        state = clean(raw_state)
        postal_code = clean(raw_postal_code)
        price = clean(raw_price)
        info = clean(raw_info).replace(u"\xb7", ',')
        broker = clean(raw_broker_name)
        title = clean(raw_title)
        property_url = "https://www.zillow.com" + url[0] if url else None
        is_forsale = properties.xpath('.//span[@class="zsg-icon-for-sale"]')

        properties = {'address': address,
                      'city': city,
                      'state': state,
                      'postal_code': postal_code,
                      'price': price,
                      'facts and features': info,
                      'real estate provider': broker,
                      'url': property_url,
                      'title': title}
        if is_forsale:
            properties_list.append(properties)
    return properties_list


if __name__ == "__main__":
    # Reading arguments

    argparser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    #argparser.add_argument('zipcode', help='')
    argparser.add_argument('city', help='')
    argparser.add_argument('state', help='')
    sortorder_help = """
    available sort orders are :
    newest : Latest property details,
    cheapest : Properties with cheapest price
    """

    argparser.add_argument('sort', nargs='?', help=sortorder_help, default='Homes For You')
    args = argparser.parse_args()
    #zipcode = args.zipcode
    city = args.city
    state = args.state
    sort = args.sort


    print ("Fetching data for %s" % (city))

    zipcode_list = get_all_zipcodes_of_city(city, state)

    count = 0
    for zipcode in zipcode_list:
        scraped_data = parse(zipcode, sort)
        if scraped_data:
            print ("Writing data to output file")
            write_data_to_csv(scraped_data, count)
        count+=1
