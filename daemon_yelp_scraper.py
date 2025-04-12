from web.models import YelpSearch, YelpRecord, Job
import time
import yelp
from yelp_circles import ComputeYelpCircles
import datetime

while Job.select().where(Job.kind == "yelp", Job.state != "complete").exists():
    print("running")
    for j in Job.select().where(Job.kind == "yelp", Job.state != "complete"):
        try:
            search = list(j.yelp_searches)[0]
            if j.state == "new":
                circle_scraper = ComputeYelpCircles(search.county_id, search.category, search.search_type)
                try:
                    circles = circle_scraper.get_circles()
                    j.state = "intermediate"
                    j.save()
                    search.circles = str(circles)
                    search.save()
                except Exception as e:
                    print(f"Error in circle computation: {e}")
                    continue

            else:
                completed, results, completed_till = yelp.search_all_circles(eval(search.circles), search.start_index, search.category, search.search_type)
                print("Result Length: ",len(results))
                if results:
                    all_records = [{
                        "search": search,
                        "yelp_id": r["id"],
                        "is_closed": r["is_closed"],
                        "name": r["name"],
                        "phone": r["phone"],
                        "street": r["location"]["address1"],
                        "city": r["location"]["city"],
                        "state": r["location"]["state"],
                        "zip_code": r["location"]["zip_code"],
                        "country": r["location"]["country"],
                        "url": r["url"],
                        "rating": r["rating"],
                        "review_count": r["review_count"],
                        "price_range": r.get("price", None),
                        "categories": ", ".join(c["title"] for c in r["categories"]),
                        "order_type": ", ".join(r["transactions"]),
                        "is_chain": False
                    } for r in results]

                    if all_records:
                        existing_ids = {r.yelp_id for r in YelpRecord.select().where(YelpRecord.search==search)}
                        new_records = [r for r in all_records if r['yelp_id'] not in existing_ids]
                        
                        if new_records:
                            YelpRecord.insert_many(new_records).execute()

                if completed:
                    j.state = "complete"
                    j.finished = datetime.datetime.utcnow()
                    j.save()
                    search.start_index = completed_till + 1
                    search.save()
                else:
                    search.start_index = completed_till
                    search.save()
                    
        except IndexError:
            print(f"No searches found for job {j.id}")
            continue
        except Exception as e:
            print(f"Error processing job {j.id}: {e}")
            continue

    print("done")
    time.sleep(5)

print("All jobs completed")