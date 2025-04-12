from web.models import YelpSearch, Job

j = Job(kind="yelp")
search = YelpSearch(search_type="text", location_string="Corvallis, OR", job=j)

j.save()
search.save()
