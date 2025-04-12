from web import app, db, models
from flask import url_for, request, redirect, render_template, flash, abort, make_response, jsonify
from web.models import Job, YelpSearch, YelpRecord, GoogleSearch, FacebookSearch, FacebookResult, GoogleResult, User, Chain, ApiKeys
from web.forms import KeyForm, SearchForm, GoogleSubmitJobForm, LoginForm, GoogleNextNForm, ChainForm, UserForm
from urllib.parse import urlparse, urljoin
from flask_login import login_required, current_user, login_user, logout_user
#from yelp import ComputeYelpCircles, yelp
from yelp_circles import ComputeYelpCircles
import google_serp
from threading import Thread
import time
import yelp
from peewee import JOIN
from outreach import importToOutreach
import humanize
import datetime
import jinja2
import requests
import pandas as pd

def check_search_exists(record):
    try:
        record.googlesearch.job
    except:
        return False
    else:
        return True
jinja2.filters.FILTERS['check_search_exists'] = check_search_exists


# http://flask.pocoo.org/snippets/62/
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@app.context_processor
def navbar_process():
    nav_items = [
        ("Yelp Searches", "searches", url_for("searches")),
        ("Jobs", "jobs", url_for("jobs")),
        ("Facebook Searches", "facebook_searches", url_for("facebook_searches")),
        ("Facebook Results", "facebook_results", url_for("facebook_results")),
        ("Google Searches", "google_searches", url_for("google_searches")),
        ("Google Results", "google_results", url_for("google_results")),
        ("Chains", "chains", url_for("chains")),
        ("Users", "users", url_for("users")),
    ]
    return dict(nav_items=nav_items, current_endpoint=request.endpoint)


@app.before_request
def _db_connect():
    db.connect()
    models.create_all_tables()

@app.teardown_request
def _db_close(exc):
    if not db.is_closed():
        db.close()


@app.template_filter('checkbox')
def checkbox(s):
    if s is True:
        return "✔"
    if s is False:
        return "❌"
    if s is None:
        return ""
    return s


@app.template_filter('humandelta')
def humanizedt(dt):
    return humanize.naturaltime(datetime.datetime.utcnow() - dt)


@app.template_filter('humanduration')
def humanizeduration(delt):
    return humanize.naturaldelta(delt)


@app.route("/")
@login_required
def index():
    """Redirect users to review page"""
    return redirect(url_for("searches"))


@app.route("/searches", methods=["GET", "POST"])
@login_required
def searches():
    search_form = SearchForm()
    key_form = KeyForm()
    if key_form.validate_on_submit():
        keys = ApiKeys.select()
        if keys:
            keys = ApiKeys.select().get()
            keys.key = key_form.key.data
            keys.ratelimit = '-'
        else:
            keys = ApiKeys(key=key_form.key.data, ratelimit='-')
        keys.save()
        return redirect(url_for("searches"))

    if search_form.validate_on_submit():
        location = search_form.location.data.split('#')
        location_string = location[0]
        county_id = location[1]
        new_job = Job(kind="yelp")
        new_search = YelpSearch(search_type=search_form.search_from.data,
                                # latitude=search_form.latitude.data,
                                # longitude=search_form.longitude.data,
                                # radius=search_form.radius.data,
                                category=search_form.category.data,
                                location_string=location_string,
                                county_id = county_id,
                                job=new_job)

        new_job.save()
        new_search.save()
        return redirect(url_for("searches"))
    
    ratelimit = 0
    ratelimits = ApiKeys.select()
    if ratelimits:
        ratelimit = ratelimits.get().ratelimit

    currentkey = ''
    for keys in ApiKeys.select():
        currentkey = keys.key
   
    return render_template("searches.html", searches=YelpSearch.select(YelpSearch, Job).join(Job).order_by(YelpSearch.id.desc()), ratelimit=ratelimit, current_key=currentkey, key_form=key_form, search_form=search_form, YelpRecord=YelpRecord)


@app.route("/searches/<sid>/export")
@login_required
def export(sid):
    search = YelpSearch.select().where(YelpSearch.id == sid).get()
    rows = [
        [
            "Yelp ID",
            "Is Closed",
            "Restaurant Name",
            "Facebook Email",
            "Website URL",
            "Phone",
            "Full Address",
            "Street",
            "City",
            "State",
            "ZIP Code",
            "Country",
            "Yelp URL",
            "Yelp Rating",
            "Yelp Review Count",
            "Yelp Price Range",
            "Yelp Categories",
            "Yelp Order Type",
            "Doordash",
            "Postmates",
            "Uber Eats",
            "Grubhub",
            "Caviar",
            "ChowNow",
            "Ordering Links",
            "Menu Links",
            "Instagram URL",
            "Facebook URL",
            "Mon Open",
            "Mon Close",
            "Tue Open",
            "Tue Close",
            "Wed Open",
            "Wed Close",
            "Thu Open",
            "Thu Close",
            "Fri Open",
            "Fri Close",
            "Sat Open",
            "Sat Close",
            "Sun Open",
            "Sun Close",

        ]
    ]

    for record in search.records.where(YelpRecord.is_chain == False).order_by(YelpRecord.id.desc()):
        facebook_email = None
        website_url = None
        doordash = None
        postmates = None
        ubereats = None
        grubhub = None
        caviar = None
        chownow = None
        facebook_url = None
        instagram_url = None
        order_links = None
        menu_links = None
        monOpenTime = None
        monCloseTime = None
        tueOpenTime = None
        tueCloseTime = None
        wedOpenTime = None
        wedCloseTime = None
        thuOpenTime = None
        thuCloseTime = None
        friOpenTime = None
        friCloseTime = None
        satOpenTime = None
        satCloseTime = None
        sunOpenTime = None
        sunCloseTime = None

        # Get Facebook email if it exists
        fs = list(record.facebook_searches)
        if fs:
            fr = list(fs[0].results)
            if fr:
                facebook_email = fr[0].email

        # Get google search if it exists
        gs = list(record.google_searches)
        if gs:
            gr = list(gs[0].results)
            if gr:
                website_url = gr[0].website
                doordash = gr[0].doordash
                postmates = gr[0].postmates
                ubereats = gr[0].ubereats
                grubhub = gr[0].grubhub
                caviar = gr[0].caviar
                chownow = gr[0].chownow
                facebook_url = gr[0].facebook_url
                instagram_url = gr[0].instagram_url
                order_links = gr[0].order_links
                menu_links = gr[0].menu_links
                monOpenTime = gr[0].monopentime
                monCloseTime = gr[0].monclosetime
                tueOpenTime = gr[0].tueopentime
                tueCloseTime = gr[0].tueclosetime
                wedOpenTime = gr[0].wedopentime
                wedCloseTime = gr[0].wedclosetime
                thuOpenTime = gr[0].thuopentime
                thuCloseTime = gr[0].thuclosetime
                friOpenTime = gr[0].friopentime
                friCloseTime = gr[0].friclosetime
                satOpenTime = gr[0].satopentime
                satCloseTime = gr[0].satclosetime
                sunOpenTime = gr[0].sunopentime
                sunCloseTime = gr[0].sunclosetime

        rows.append(
            [
                record.yelp_id,
                record.is_closed,
                record.name,
                facebook_email,
                website_url,
                record.phone,
                (str(record.street) + ", " + str(record.city) + ", " + str(record.state) + " " + str(record.zip_code) + ", "+ str(record.country)).strip(),
                record.street,
                record.city,
                record.state,
                record.zip_code,
                record.country,
                record.url,
                record.rating,
                record.review_count,
                record.price_range,
                record.categories,
                record.order_type,
                doordash,
                postmates,
                ubereats,
                grubhub,
                caviar,
                chownow,
                order_links,
                menu_links,
                instagram_url,
                facebook_url,
                monOpenTime,
                monCloseTime,
                tueOpenTime,
                tueCloseTime,
                wedOpenTime,
                wedCloseTime,
                thuOpenTime,
                thuCloseTime,
                friOpenTime,
                friCloseTime,
                satOpenTime,
                satCloseTime,
                sunOpenTime,
                sunCloseTime
            ]
        )

    output = ""

    for row in rows:
        row_s = ""

        for column in row:
            if column is True:
                row_s += "Yes,"
            elif column is False:
                row_s += "No,"
            elif column is None:
                row_s += ","
            else:
                row_s += f"\"{column}\","
        row_s += "\n"
        output += row_s

    response = make_response(output)
    response.headers["Content-Disposition"] = f"attachment; filename={sid}_{int(time.time())}_export.csv"
    response.headers["Content-Type"] = "text/csv"
    return response

@app.route("/bulk-import-into-outreach/<sid>", methods=["GET"])
@login_required
def outreach(sid):
    accounts = []
    prospects = []
    search = YelpSearch.select().where(YelpSearch.id == sid).get()
    df = pd.read_csv('county_state.csv')
    county_maps = df.values
    county_name = ''
    for c in county_maps:
        if c[0] == search.county_id:
            county_name = f"{c[2]}, {c[1]}"
    for record in search.records.where(YelpRecord.is_chain == False).order_by(YelpRecord.id.desc()):
        facebook_email = None
        website_url = None
        doordash = None
        postmates = None
        ubereats = None
        grubhub = None
        caviar = None
        chownow = None
        facebook_url = None
        instagram_url = None
        order_links = None
        menu_links = None
        monOpenTime = None
        monCloseTime = None
        tueOpenTime = None
        tueCloseTime = None
        wedOpenTime = None
        wedCloseTime = None
        thuOpenTime = None
        thuCloseTime = None
        friOpenTime = None
        friCloseTime = None
        satOpenTime = None
        satCloseTime = None
        sunOpenTime = None
        sunCloseTime = None

        # Get Facebook email if it exists
        fs = list(record.facebook_searches)
        if fs:
            fr = list(fs[0].results)
            if fr:
                facebook_email = fr[0].email

        # Get google search if it exists
        gs = list(record.google_searches)
        if gs:
            gr = list(gs[0].results)
            if gr:
                website_url = gr[0].website
                doordash = gr[0].doordash
                postmates = gr[0].postmates
                ubereats = gr[0].ubereats
                grubhub = gr[0].grubhub
                caviar = gr[0].caviar
                chownow = gr[0].chownow
                facebook_url = gr[0].facebook_url
                instagram_url = gr[0].instagram_url
                order_links = gr[0].order_links
                menu_links = gr[0].menu_links
                monOpenTime = gr[0].monopentime
                monCloseTime = gr[0].monclosetime
                tueOpenTime = gr[0].tueopentime
                tueCloseTime = gr[0].tueclosetime
                wedOpenTime = gr[0].wedopentime
                wedCloseTime = gr[0].wedclosetime
                thuOpenTime = gr[0].thuopentime
                thuCloseTime = gr[0].thuclosetime
                friOpenTime = gr[0].friopentime
                friCloseTime = gr[0].friclosetime
                satOpenTime = gr[0].satopentime
                satCloseTime = gr[0].satclosetime
                sunOpenTime = gr[0].sunopentime
                sunCloseTime = gr[0].sunclosetime

        accounts.append(
            {
                "customId": record.yelp_id or "",     
                "domain": website_url or "",      
                "locality": county_name, # county
                "name": record.name or "",      
                "naturalName": record.name or "",
                "websiteUrl": website_url or "",   
                "custom1": facebook_email or "",    
                "custom2": record.street or "",
                "custom3": "",
                "custom4": record.city or "",
                "custom5": record.state or "",
                "custom6": record.zip_code or "",
                "custom7": record.url or "",
                "custom8": record.rating or "",
                "custom9": record.review_count or "",
                "custom10": record.price_range or "",
                "custom11": record.categories or "",
                "custom12": doordash,
                "custom13": postmates,
                "custom14": ubereats,
                "custom15": grubhub,
                "custom16": caviar,
                "custom17": chownow,
                "custom18": order_links or "",
                "custom19": menu_links or "",
                "custom20": instagram_url or "",
                "custom21": facebook_url or "",
                "custom22": monOpenTime or "",
                "custom23": monCloseTime or "",
                "custom24": tueOpenTime or "",
                "custom25": tueCloseTime or "",
                "custom26": wedOpenTime or "",
                "custom27": wedCloseTime or "",
                "custom28": thuOpenTime or "",
                "custom29": thuCloseTime or "",
                "custom30": friOpenTime or "",
                "custom31": friCloseTime or "",
                "custom32": satOpenTime or "",
                "custom33": satCloseTime or "",
                "custom34": sunOpenTime or "",
                "custom35": sunCloseTime or "",
                "custom36": record.phone or ""
            }
        )
    
        prospects.append(
            {
                "addressCity": record.city or "", 
                "addressCountry": record.country or "", 
                "addressState": record.state or "", 
                "addressStreet": record.street or "",
                "addressStreet2": '' or "", 
                "addressZip": record.zip_code or "",
                "emails": [facebook_email] or [], 
                "facebookUrl": facebook_url or "", 
                "region": county_name,  # county
                "websiteUrl1": website_url or "", 
                "workPhones": [record.phone] or [], 
                "custom1": record.name or ""
            }
        )

    response = importToOutreach(accounts, prospects)
    # return redirect(url_for("bulk-import-into-outreach/<sid>"))

    return(response)

@app.route("/searches/<sid>", methods=["GET", "POST"])
@login_required
def records(sid):
    google_n_form = GoogleNextNForm()
    if google_n_form.validate_on_submit():
        if google_n_form.n.data and google_n_form.validate():
            eligible_records = []
            for rec in YelpSearch.select().where(YelpSearch.id == sid).get().records.where(YelpRecord.is_chain == False).order_by(YelpRecord.id.desc()):
                if not list(rec.google_searches):
                    eligible_records.append(rec)

            # Trim to desired size
            eligible_records = eligible_records[:int(google_n_form.n.data)]
            print('www', eligible_records)
            for record in eligible_records:
                new_job = Job(kind="google")
                new_search = GoogleSearch(
                    search_string=f"{record.name} {record.street}, {record.city}, {record.state} {record.zip_code} facebook",
                    yelp_record=record,
                    job=new_job
                )
                new_job.save()
                new_search.save()

            return redirect(url_for("records", sid=sid))

    google_form = GoogleSubmitJobForm()
    if google_form.validate_on_submit():
        record = YelpRecord.select().where(YelpRecord.id == google_form.record_id.data).get()

        new_job = Job(kind="google")
        new_search = GoogleSearch(
            search_string=f"{record.name} {record.street}, {record.city}, {record.state} {record.zip_code} facebook",
            yelp_record=record,
            job=new_job
        )
        new_job.save()
        new_search.save()
        return redirect(url_for("records", sid=sid))

    record_query = (
                    YelpRecord
                    .select(YelpRecord, GoogleSearch, Job, GoogleResult, FacebookSearch, FacebookResult)
                    .join(GoogleSearch, JOIN.LEFT_OUTER)
                    .join(Job, JOIN.LEFT_OUTER)
                    .switch(GoogleSearch)
                    .join(GoogleResult, JOIN.LEFT_OUTER)
                    .switch(YelpRecord)
                    .join(FacebookSearch, JOIN.LEFT_OUTER)
                    .join(FacebookResult, JOIN.LEFT_OUTER)
                    .where(YelpRecord.search == sid)
                    .where(YelpRecord.is_chain == False)
                    .order_by(YelpRecord.id.desc())
                    )

    return render_template("records.html", records=record_query, google_form=google_form, google_n_form=google_n_form, sid=sid)


@app.route("/jobs")
@login_required
def jobs():
    return render_template("jobs.html", jobs=Job.select().order_by(Job.id.desc()).limit(1000))


@app.route("/chains", methods=["GET", "POST"])
@login_required
def chains():
    chain_form = ChainForm()
    if chain_form.validate_on_submit():
        new_chain = Chain(name=chain_form.name.data, confidence=90)
        new_chain.save()
        return redirect(url_for("chains"))

    return render_template("chains.html", chains=Chain.select().order_by(Chain.id.desc()).limit(1000), chain_form=chain_form)


@app.route("/users", methods=["GET", "POST"])
@login_required
def users():
    user_form = UserForm()
    if user_form.validate_on_submit():
        new_user = User()
        new_user.email = user_form.email.data
        new_user.is_admin = user_form.is_admin.data
        new_user.set_password(user_form.password.data)
        new_user.save()
        return redirect(url_for("users"))

    return render_template("users.html", users=User.select().order_by(User.id.desc()).limit(1000), is_admin=current_user.is_admin, user_form=user_form)


@app.route("/facebook/searches")
@login_required
def facebook_searches():
    return render_template("facebook_searches.html", searches=FacebookSearch.select().order_by(FacebookSearch.id.desc()).limit(1000))


@app.route("/facebook/results")
@login_required
def facebook_results():
    return render_template("facebook_results.html", results=FacebookResult.select().order_by(FacebookResult.id.desc()).limit(1000))


@app.route("/google/searches")
@login_required
def google_searches():
    return render_template("google_searches.html", searches=GoogleSearch.select().order_by(GoogleSearch.id.desc()).limit(1000))


@app.route("/google/results")
@login_required
def google_results():
    return render_template("google_results.html", results=GoogleResult.select().order_by(GoogleResult.id.desc()).limit(1000))

@app.route('/check_google_all_jobs', methods=['GET'])
def check_google_all_jobs():
   try:
       # Check if any incomplete yelp jobs exist
       incomplete_jobs = Job.select().where(
           Job.kind == "google",
           Job.state != "complete"
       ).count()
       
       # Get total jobs count
       total_jobs = Job.select().where(
           Job.kind == "google"
       ).count()

       # Get completed jobs count 
       completed_jobs = Job.select().where(
           Job.kind == "google",
           Job.state == "complete"
       ).count()

       response = {
           'status': 'success',
           'total_jobs': total_jobs,
           'completed_jobs': completed_jobs,
           'incomplete_jobs': incomplete_jobs,
           'all_complete': incomplete_jobs == 0,
           'completion_percentage': (completed_jobs/total_jobs * 100) if total_jobs > 0 else 0
       }

       return jsonify(response), 200

   except Exception as e:
       return jsonify({
           'status': 'error',
           'message': str(e)
       }), 500

@app.route('/check_all_jobs', methods=['GET'])
def check_all_jobs():
   try:
       # Check if any incomplete yelp jobs exist
       incomplete_jobs = Job.select().where(
           Job.kind == "yelp",
           Job.state != "complete"
       ).count()
       
       # Get total jobs count
       total_jobs = Job.select().where(
           Job.kind == "yelp"
       ).count()

       # Get completed jobs count 
       completed_jobs = Job.select().where(
           Job.kind == "yelp",
           Job.state == "complete"
       ).count()

       response = {
           'status': 'success',
           'total_jobs': total_jobs,
           'completed_jobs': completed_jobs,
           'incomplete_jobs': incomplete_jobs,
           'all_complete': incomplete_jobs == 0,
           'completion_percentage': (completed_jobs/total_jobs * 100) if total_jobs > 0 else 0
       }

       return jsonify(response), 200

   except Exception as e:
       return jsonify({
           'status': 'error',
           'message': str(e)
       }), 500


@app.route('/run_google_script', methods=['POST'])
def run_google_script():
   try:
       # Start the job processing in a separate thread/process
       Thread(target=process_google_jobs).start()
       
       return jsonify({
           'status': 'success', 
           'message': 'Job processing started successfully'
       }), 200
       
   except Exception as e:
       return jsonify({
           'error': str(e)
       }), 500


@app.route('/run_script', methods=['POST'])
def run_script():
   try:
       # Start the job processing in a separate thread/process
       Thread(target=process_jobs).start()
       
       return jsonify({
           'status': 'success', 
           'message': 'Job processing started successfully'
       }), 200
       
   except Exception as e:
       return jsonify({
           'error': str(e)
       }), 500
   

def process_google_jobs():
    try:
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
    except Exception as e:
       print(f"Error in process_jobs: {str(e)}")
   

def process_jobs():
    try:
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
           
    except Exception as e:
        print(f"Error in process_jobs: {str(e)}")

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Log in the user, and redirect them to their final destination if needed"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    login_form = LoginForm()
    if login_form.validate_on_submit():
        email_valid = False

        user = User.select().where(User.email == login_form.email.data)
        if user:
            user = user[0]
            email_valid = True
            if user.check_password(login_form.password.data):
                password_valid = True

        if email_valid and password_valid:
            login_user(user, remember=True)

            next_url = request.args.get('next')
            if not is_safe_url(next_url):
                return abort(400)
            return redirect(next_url or url_for('index'))
        else:
            flash('Invalid email or password.', "error")
            return redirect(url_for('login'))

    return render_template('login.html', title='Sign In', form=login_form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
