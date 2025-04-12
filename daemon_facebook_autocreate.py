from web.models import FacebookSearch, GoogleSearch, Job
import time

while True:
    for goog in GoogleSearch.select():
        if list(goog.results):
            if list(goog.results)[0].facebook_url:
                if not list(goog.yelp_record.facebook_searches):
                    new_job = Job(
                        kind="facebook",
                    )
                    new_search = FacebookSearch(
                        url=list(goog.results)[0].facebook_url,
                        yelp_record=goog.yelp_record,
                        job=new_job
                    )

                    new_job.save()
                    new_search.save()
                    print("created")
                    time.sleep(5)


    print("finished")
    time.sleep(30)
