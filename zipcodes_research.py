##### https://uszipcode.readthedocs.io/index.html #####
##### Use this file to keep track of zipcode research #####

from uszipcode import SearchEngine, SimpleZipcode, Zipcode
from zipcodes_util import *



def get_counties_by_state(state):
    search = SearchEngine(simple_zipcode=True)
    counties = []
    #res = search.query(city="Fairfax", state="VA")
    res = search.by_state(state=state, sort_by='zipcode', returns = 50)
    for zip in res:
        counties.append(zip.county)
    return counties


def get_cities_by_median_income(lower, upper):
    search = SearchEngine(simple_zipcode=True)
    cities = []
    res = search.by_median_household_income(lower=lower, upper=upper, sort_by='median_household_income', ascending=False, returns = 50)
    print(res)
    for zip in res:
        cities.append(zip.major_city)
    return cities

def get_zipcodes_by_median_income(lower, upper):
    search = SearchEngine(simple_zipcode=True)
    cities = []
    res = search.by_median_household_income(lower=lower, upper=upper, sort_by='median_household_income', ascending=False, returns = 50)
    print(res)
    for zip in res:
        cities.append(zip.major_city)
    return cities

def get_zip_of_rich_by_city_state(city, state):
    lat, lng = get_lat_lng_of_city_state(city, state)
    zips = get_zipcode_of_richest_near_city(lat, lng)
    return zips

# Currently set to get top 20 with 100 mile radius
def get_zipcode_of_richest_near_city(lat, lng):
    search = SearchEngine(simple_zipcode=True)
    zip=[]
    radius = 100
    res = search.query(
        lat=lat,
        lng=lng,
        radius=radius,
        sort_by=Zipcode.median_household_income,
        ascending=False,
        returns=100,
    )
    print(res)
    for i in res:
        zip.append(str(i.median_household_income) + " " + i.major_city)

    return zip



x = get_zip_of_rich_by_city_state('fairfax', 'va')
print(x)