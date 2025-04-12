from web.models import GoogleSearch, YelpRecord, Job

for record in YelpRecord.select():
    if not list(record.google_searches):
        new_job = Job(kind="google")
        new_search = GoogleSearch(
            search_string=f"{record.name} {record.street}, {record.city}, {record.state} {record.zip_code}",
            yelp_record=record,
            job=new_job
        )

        new_job.save()
        new_search.save()
