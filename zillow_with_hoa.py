from lxml import html
import requests
import unicodecsv as csv
import argparse
import json
import io
from zipcodes_util import *


def clean(text):
    if text:
        return ' '.join(' '.join(text).split())
    return None


def get_headers():
    # Creating headers.
    headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "pragma": "no-cache",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "cross-site",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
}

        # {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        #        'accept-encoding': 'gzip, deflate, sdch, br',
        #        'accept-language': 'en-GB,en;q=0.8,en-US;q=0.6,ml;q=0.4',
        #        'cache-control': 'max-age=0',
        #        'upgrade-insecure-requests': '1',
        #        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'}
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

def create_detail_url(zipcode, filter):
    # Creating Zillow URL based on the filter.

    url = "https://www.zillow.com/homes/for_sale/{0}_rb/?fromHomePage=true&shouldFireSellPageImplicitClaimGA=false&fromHomePageTab=buy".format(zipcode)

    print(url)
    return url


def save_to_file(response):
	with io.open("response.html", "w", encoding="utf-8") as fp:
		fp.write(response.text)


def write_data_to_csv(data, count):
    # saving scraped data to csv.

    with open("Data/properties-%s.csv" % (city), 'ab') as csvfile:
        fieldnames = ['title', 'city', 'state', 'postal_code', 'zestimate', 'rentZestimate', 'HOA', 'price', 'yearBuilt', 'area', 'daysOnZillow', 'facts and features', 'url', 'P2R']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if count==0:
            writer.writeheader()
        for row in data:
            writer.writerow(row)


def get_response(url, is_hoa=False):
    # Getting response from zillow.com.

    for i in range(5):
        response = requests.get(url, headers=get_headers())
        if is_hoa is False:
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
    price = price.replace('/mo', '')
    price = price.replace('+', '')
    return price



def get_hoa(property_url):
    is_hoa = True
    print("now retrieving:", property_url)
    response_detail = get_response(property_url, is_hoa)
    detail_parser = html.fromstring(response_detail.text)
    # raw_detail_json_data = detail_parser.xpath('//script[@id="hdpApolloPreloadedData"]//text()')
    raw_detail_json_data = detail_parser.xpath('//span[@class="Text-aiai24-0 IJYzV"]//text()')

    lst = raw_detail_json_data
    it = iter(lst)
    res_dct = dict(zip(it, it))
    hoa = remove_dollar_and_comma(res_dct.get("HOA fee: ", "0"))

    if hoa is None:
        hoa = 0

    return hoa


    # try:
    #     for i in range(0, len(raw_detail_json_data)):
    #         item = str(raw_detail_json_data[i])
    #         if item == "HOA fee: ":
    #             hoa_dollar = str(raw_detail_json_data[i + 1])
    #             hoa = remove_dollar_and_comma(hoa_dollar)
    #             break
    #
    #     if hoa is None:
    #         hoa = 0
    #
    #     return hoa
    # except Exception as e:
    #     print(e)


def get_data_from_json(raw_json_data):
    # getting data from json (type 2 of their A/B testing page)

    if clean(raw_json_data) is not None:
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
            zestimate_unrefined = property_info.get('zestimate') if property_info.get('zestimate') is not None else '0'
            zestimate = int(str(zestimate_unrefined).replace('+', ''))
            rentZestimate = property_info.get('rentZestimate')
            price = remove_dollar_and_comma(properties.get('price')) if properties.get('price') is not None else '0'
            yearBuilt = property_info.get('yearBuilt')
            daysOnZillow = property_info.get('daysOnZillow')
            bedrooms = properties.get('beds')
            bathrooms = properties.get('baths')
            area = properties.get('area')
            info = f'{bedrooms} beds, {bathrooms} baths'
            property_url = properties.get('detailUrl')
            unrefined_hoa = get_hoa(property_url) #TODO: Make this function run faster this is slowing down the overall program.
            hoa = unrefined_hoa if unrefined_hoa is not None and unrefined_hoa != "None" else '0'



            title = properties.get('statusText')
            # TODO days_on_market = properties.get('variableData').get('text')

            if zestimate not in [None, '', 0] and rentZestimate not in [None, '', 0]:
                price_to_rent =str(int(zestimate)/(12*int(rentZestimate-int(hoa))))
            elif price not in [None, ''] and rentZestimate not in [None, '']:
                price_to_rent = str(int(price)/(12*int(rentZestimate-int(hoa))))
            else:
                price_to_rent = "0"



            data = {'city': city,
                    'state': state,
                    'postal_code': postal_code,
                    'zestimate': zestimate,
                    'rentZestimate' : rentZestimate,
                    'HOA' : hoa,
                    'price': price,
                    'yearBuilt' : yearBuilt,
                    'area': area,
                    'daysOnZillow' : daysOnZillow,
                    'facts and features': info,
                    'url': property_url,
                    'title': title,
                    'P2R': price_to_rent}

            if data['P2R'] != "0":
                properties_list.append(data)

        return properties_list

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
    argparser.add_argument('city', help='')
    argparser.add_argument('state', help='')
    argparser.add_argument('sort', nargs='?', help='', default='Homes For You')
    args = argparser.parse_args()
    city = args.city
    state = args.state
    sort = args.sort

    # uncomment to debug
    # city = "denver"
    # state = "colorado"
    # sort = ""



    print ("Fetching data for %s" % (city))

    zipcode_list = get_zip_of_rich_by_city_state(city, state)

    count = 0
    for zipcode in zipcode_list:
        scraped_data = parse(zipcode, sort)
        if scraped_data:
            print ("Writing data to output file")
            write_data_to_csv(scraped_data, count)
        count+=1
