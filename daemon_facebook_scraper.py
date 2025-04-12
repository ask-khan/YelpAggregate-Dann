from web.models import FacebookResult, Job
import time
import facebook
import datetime

while True:
    for j in Job.select().where(Job.kind == "facebook", Job.state == "new"):
        print(j)
        try:
            search = list(j.facebook_searches)[0]

            db_result = FacebookResult(
                search=search,
                email=facebook.get_email(search.url)
            )

            db_result.save()
            j.state = "complete"
            j.finished = datetime.datetime.utcnow()
            j.save()
        except IndexError:
            print('Wait a moment while the jobs are creating...')
            pass

    print("done")
    time.sleep(5)
