##### https://uszipcode.readthedocs.io/index.html #####

from uszipcode import SearchEngine, SimpleZipcode, Zipcode

search = SearchEngine(simple_zipcode=True)

def get_all_zipcodes_of_city(city, state):
    zipcodes = []
    res = search.by_city_and_state(city, state)
    for zip in res:
        zipcodes.append(zip.zipcode)
    return zipcodes


def get_lat_lng_of_city_state(city, state):
    count = 0
    search = SearchEngine(simple_zipcode=True)
    info = []
    res = search.by_city_and_state(city=city, state=state)
    for zip in res:
        if zip.lat is not None and count==0:
            info.append(zip.lat)
            info.append(zip.lng)
            count=count+1
    return info

# Currently set to get top 20 with 100 mile radius
def get_zipcode_of_richest_near_city(lat, lng):
    search = SearchEngine(simple_zipcode=True)
    zip=[]
    radius = 50
    res = search.query(
        lat=lat,
        lng=lng,
        radius=radius,
        sort_by=Zipcode.median_household_income,
        ascending=False,
        returns=1,
    )
    for i in res:
        zip.append(i.zipcode)

    return zip

def get_zip_of_rich_by_city_state(city, state):
    lat, lng = get_lat_lng_of_city_state(city, state)
    zips = get_zipcode_of_richest_near_city(lat, lng)
    return zips