##### https://uszipcode.readthedocs.io/index.html #####
##### Use this file to keep track of zipcode research #####

from uszipcode import SearchEngine, SimpleZipcode

search = SearchEngine(simple_zipcode=True)

def get_counties_by_state(state):
    counties = []
    #res = search.query(city="Fairfax", state="VA")
    res = search.by_state(state=state, sort_by='zipcode', returns = 50)
    for zip in res:
        counties.append(zip.county)
    return counties


def get_cities_by_median_income(lower, upper):
    cities = []
    res = search.by_median_household_income(lower=lower, upper=upper, sort_by='median_household_income', ascending=False, returns = 50)
    for zip in res:
        cities.append(zip.major_city)
    return cities


#result = get_counties_by_state("Virginia")
result = get_cities_by_median_income(50000, 100000)
print(result)