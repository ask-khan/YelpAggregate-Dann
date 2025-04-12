import requests

def search(query):
    s = requests.session()
    s.params = {
        "api_key": "eb6a9e6c87d455804e789baecdc8819ffdc5dad68effbd297cbe0f55d12bee19",
        "engine": "google",
    }
    r = s.get("https://serpapi.com/search.json", params={"q": query})
    data = r.json()

    facebook_url = None
    instagram_url = None
    hours = None
    order_links = None
    order=""

    monopentime = None
    monclosetime = None
    tueopentime = None
    tueclosetime = None
    wedopentime = None
    wedclosetime = None
    thuopentime = None
    thuclosetime = None
    friopentime = None
    friclosetime = None
    satopentime = None
    satclosetime = None
    sunopentime = None
    sunclosetime = None

    try:
        for profile in data["knowledge_graph"]["profiles"]:
            if profile.get("name", "") == "Facebook":
                facebook_url = profile["link"]
            if profile.get("name", "") == "Instagram":
                instagram_url = profile["link"]
    except KeyError:
        pass

    try:
        # Kind of ugly
        order = data["knowledge_graph"]["order"]
        order_links = order
    except KeyError:
        order = ""

    # TODO: Doesn't seem to return what we are expecting? Only the domain, not the full URL

    try:
        menu = data["knowledge_graph"]["menu"]
    except KeyError:
        menu = None

    try:
        website = data["knowledge_graph"]["website"]
    except KeyError:
        website = None
    
    try:
        hours = data["knowledge_graph"]["hours"]
        if hours:
            for attr, value in hours.items():
                if(attr == 'monday' or attr == 'monday_labor_day'):
                    monopentime = value["opens"]
                    monclosetime = value["closes"]
                if(attr == 'wednesday' or attr == 'wednesday_veterans_day'):
                    wedopentime = value["opens"]
                    wedclosetime = value["closes"]
            tueopentime = hours["tuesday"]["opens"]
            tueclosetime = hours["tuesday"]["closes"]
            thuopentime = hours["thursday"]["opens"]
            thuclosetime = hours["thursday"]["closes"]
            friopentime = hours["friday"]["opens"]
            friclosetime = hours["friday"]["closes"]
            satopentime = hours["saturday"]["opens"]
            satclosetime = hours["saturday"]["closes"]
            sunopentime = hours["sunday"]["opens"]
            sunclosetime = hours["sunday"]["closes"]

    except KeyError:
        pass

    # If Facebook URL is not in knowledge graph, look for a Facebook URL in organic results
    if not facebook_url:
        try:
            for result in data["organic_results"]:
                if "facebook" in result["title"].lower():
                    facebook_url = result["link"]
                    break
        except KeyError:
            pass
    if not hours:
        try:
            rr = s.get("https://serpapi.com/search.json", params={"q": query.replace("facebook", "")})
            newData = rr.json()
            try:

                hours = newData["knowledge_graph"]["hours"]
                if hours:
                    for attr, value in hours.items():
                        if(attr == 'monday' or attr == 'monday_labor_day'):
                            monopentime = value["opens"]
                            monclosetime = value["closes"]
                        if(attr == 'wednesday' or attr == 'wednesday_veterans_day'):
                            wedopentime = value["opens"]
                            wedclosetime = value["closes"]
                    tueopentime = hours["tuesday"]["opens"]
                    tueclosetime = hours["tuesday"]["closes"]
                    thuopentime = hours["thursday"]["opens"]
                    thuclosetime = hours["thursday"]["closes"]
                    friopentime = hours["friday"]["opens"]
                    friclosetime = hours["friday"]["closes"]
                    satopentime = hours["saturday"]["opens"]
                    satclosetime = hours["saturday"]["closes"]
                    sunopentime = hours["sunday"]["opens"]
                    sunclosetime = hours["sunday"]["closes"]

            except KeyError:
                pass
            try:
                # Kind of ugly
                order = newData["knowledge_graph"]["order"]
                order_links = order
            except KeyError:
                order = ""
        except KeyError:
            pass
    return {
        "facebook_url": facebook_url,
        "instagram_url": instagram_url,
        "has_doordash": "doordash" in order,
        "has_postmates": "postmates" in order,
        "has_ubereats": "uber" in order,
        "has_grubhub": "grubhub" in order,
        "has_caviar": "caviar" in order,
        "has_chownow": "chownow" in order,
        "order_links": order_links,
        "menu_links": menu,
        "website": website,
        "monopentime" : monopentime,
        "monclosetime" : monclosetime,
        "tueopentime" : tueopentime,
        "tueclosetime" : tueclosetime,
        "wedopentime" : wedopentime,
        "wedclosetime" : wedclosetime,
        "thuopentime" : thuopentime,
        "thuclosetime" : thuclosetime,
        "friopentime" : friopentime,
        "friclosetime" : friclosetime,
        "satopentime" : satopentime,
        "satclosetime" : satclosetime,
        "sunopentime" : sunopentime,
        "sunclosetime" : sunclosetime
    }
