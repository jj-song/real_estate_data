##### https://uszipcode.readthedocs.io/index.html #####

from uszipcode import SearchEngine

search = SearchEngine(simple_zipcode=True)

def get_all_zipcodes_of_city(city, state):
    zipcodes = []
    res = search.by_city_and_state(city, state)
    for zip in res:
        zipcodes.append(zip.zipcode)
    return zipcodes