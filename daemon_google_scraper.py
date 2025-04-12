from web.models import GoogleResult, Job
import time
import google_serp
import datetime

def process_google_jobs():
   while Job.select().where(Job.kind == "google", Job.state == "new").exists():
       for j in Job.select().where(Job.kind == "google", Job.state == "new"):
           try:
               print(j)
               search = list(j.google_searches)[0]

               res = google_serp.search(search.search_string)

               db_result = GoogleResult(
                   search=search,
                   doordash=res["has_doordash"],
                   postmates=res["has_postmates"], 
                   ubereats=res["has_ubereats"],
                   grubhub=res["has_grubhub"],
                   caviar=res["has_caviar"], 
                   chownow=res["has_chownow"],
                   facebook_url=res["facebook_url"],
                   instagram_url=res["instagram_url"],
                   order_links=res["order_links"],
                   menu_links=res["menu_links"],
                   website=res["website"],
                   monopentime=res["monopentime"],
                   monclosetime=res["monclosetime"],
                   tueopentime=res["tueopentime"],
                   tueclosetime=res["tueclosetime"],
                   wedopentime=res["wedopentime"],
                   wedclosetime=res["wedclosetime"],
                   thuopentime=res["thuopentime"],
                   thuclosetime=res["thuclosetime"],
                   friopentime=res["friopentime"],
                   friclosetime=res["friclosetime"],
                   satopentime=res["satopentime"],
                   satclosetime=res["satclosetime"],
                   sunopentime=res["sunopentime"],
                   sunclosetime=res["sunclosetime"]
               )

               db_result.save()
               j.state = "complete"
               j.finished = datetime.datetime.utcnow()
               j.save()

           except Exception as e:
               print(f"Error processing job {j.id}: {str(e)}")
               continue

       time.sleep(5)

   print("All google jobs completed")

if __name__ == "__main__":
   process_google_jobs()