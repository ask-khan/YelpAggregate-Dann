import requests
from web.models import ApiKeys

def __search(params):
    api_key = ''
    for keys in ApiKeys.select():
        api_key = keys.key
                        
    s = requests.session()
    s.headers = {
        "Authorization": "Bearer " + api_key
    }
    r = s.get("https://api.yelp.com/v3/businesses/search", params=params)
    ratelimits = ApiKeys.select()
    if ratelimits:
        ratelimits = ApiKeys.select().get()
        ratelimits.ratelimit = r.headers['ratelimit-remaining']
    else:
        ratelimits = ApiKeys(r.headers['ratelimit-remaining'])
    ratelimits.save()
    
    return r.json()["businesses"]


def search(latitude, longitude, radius, category='[]', search_type=''):
    results = []

    search_params = ({
        "term": search_type,
        "limit": 50,
        "latitude": latitude,
        "longitude": longitude,
        "radius": radius,
        "categories": ",".join(list(map(lambda c: c, eval(category)))),
    })

    while True:
        page = __search(search_params)
        results.extend(page)
        if len(page)<50:
            # print(search_params)
            break
        search_params.update({
            "offset": search_params.get("offset", 0) + 50
        })

    return results


def search_all_circles(circles, start_index=0, category='[]', search_type=''):
    data = []
    uniq_set = set()
    
    # Handle empty circles list or invalid start_index
    if not circles or start_index >= len(circles):
        return True, data, start_index

    last_index = start_index  # Initialize last_index before the loop
    
    try:
        for i, circle in enumerate(circles[start_index:]):
            last_index = start_index + i  # Update last_index in each iteration
            try:
                results = search(circle[0][1], circle[0][0], circle[1], category, search_type)
                
                for result in results:
                    if result['id'] not in uniq_set:
                        data.append(result)
                        uniq_set.add(result['id'])
                        
            except Exception as e:
                print(f"Error processing circle at index {last_index}: {str(e)}")
                return False, data, last_index
        
        return True, data, last_index
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False, data, last_index

# if __name__ == "__main__":
#     print(len(sget_circlesearch("Los Angeles, CA")))
