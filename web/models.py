import peewee
from web import db
import datetime
from flask_login import UserMixin
from web import login_manager
from werkzeug.security import generate_password_hash, check_password_hash


class BaseModel(peewee.Model):
    class Meta:
        database = db


class User(UserMixin, BaseModel):
    email = peewee.CharField()
    # hashed/salted representation of password
    password = peewee.CharField()
    utc_created = peewee.DateTimeField(default=datetime.datetime.utcnow)
    # Last login
    utc_activity = peewee.DateTimeField(null=True)
    is_admin = peewee.BooleanField(default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

@login_manager.user_loader
def load_user(uid):
    u = list(User.select().where(User.id == uid))
    if u:
        u = u[0]
        # Set this whenever the user interacts in a way that requires login info
        u.utc_activity = datetime.datetime.utcnow()
        u.save()
        return u


class Job(BaseModel):
    kind = peewee.CharField()
    created = peewee.DateTimeField(default=datetime.datetime.utcnow)
    state = peewee.CharField(default="new")
    finished = peewee.DateTimeField(null=True)


class YelpSearch(BaseModel):
    search_type = peewee.CharField()
    location_string = peewee.CharField(null=True)
    county_id = peewee.IntegerField(null=True)
    latitude = peewee.CharField(null=True)
    longitude = peewee.CharField(null=True)
    radius = peewee.IntegerField(null=True)
    category = peewee.CharField(null=True)
    job = peewee.ForeignKeyField(Job, backref="yelp_searches")
    created = peewee.DateTimeField(default=datetime.datetime.utcnow)
    circles = peewee.TextField(null=True)
    start_index = peewee.IntegerField(default=0)


class YelpRecord(BaseModel):
    search = peewee.ForeignKeyField(YelpSearch, backref="records")
    yelp_id = peewee.CharField()
    is_closed = peewee.BooleanField()
    name = peewee.TextField()
    phone = peewee.TextField()
    street = peewee.TextField(null=True)
    city = peewee.TextField()
    state = peewee.TextField()
    zip_code = peewee.TextField()
    country = peewee.TextField()
    url = peewee.TextField()
    rating = peewee.TextField()
    review_count = peewee.TextField()
    price_range = peewee.TextField(null=True)
    categories = peewee.TextField()
    order_type = peewee.TextField()
    is_chain = peewee.BooleanField()


class GoogleSearch(BaseModel):
    search_string = peewee.TextField()
    yelp_record = peewee.ForeignKeyField(YelpRecord, backref="google_searches")
    job = peewee.ForeignKeyField(Job, backref="google_searches")
    created = peewee.DateTimeField(default=datetime.datetime.utcnow)


class GoogleResult(BaseModel):
    search = peewee.ForeignKeyField(GoogleSearch, backref="results")
    doordash = peewee.BooleanField()
    postmates = peewee.BooleanField()
    ubereats = peewee.BooleanField()
    grubhub = peewee.BooleanField()
    caviar = peewee.BooleanField()
    chownow = peewee.BooleanField()
    facebook_url = peewee.TextField(null=True)
    instagram_url = peewee.TextField(null=True)
    order_links = peewee.TextField(null=True)
    menu_links = peewee.TextField(null=True)
    website = peewee.TextField(null=True)
    monopentime = peewee.CharField(null=True)
    monclosetime = peewee.CharField(null=True)
    tueopentime = peewee.CharField(null=True)
    tueclosetime = peewee.CharField(null=True)
    wedopentime = peewee.CharField(null=True)
    wedclosetime = peewee.CharField(null=True)
    thuopentime = peewee.CharField(null=True)
    thuclosetime = peewee.CharField(null=True)
    friopentime = peewee.CharField(null=True)
    friclosetime = peewee.CharField(null=True)
    satopentime = peewee.CharField(null=True)
    satclosetime = peewee.CharField(null=True)
    sunopentime = peewee.CharField(null=True)
    sunclosetime = peewee.CharField(null=True)


class FacebookSearch(BaseModel):
    url = peewee.TextField()
    yelp_record = peewee.ForeignKeyField(YelpRecord, backref="facebook_searches")
    job = peewee.ForeignKeyField(Job, backref="facebook_searches")
    created = peewee.DateTimeField(default=datetime.datetime.utcnow)


class FacebookResult(BaseModel):
    search = peewee.ForeignKeyField(FacebookSearch, backref="results")
    email = peewee.TextField(null=True)


class Chain(BaseModel):
    name = peewee.CharField(unique=True)
    confidence = peewee.IntegerField()

class ApiKeys(BaseModel):
    key = peewee.TextField(null=True)
    ratelimit = peewee.TextField(null=True)

def create_all_tables():
    db.create_tables([
        User,
        Job,
        YelpSearch,
        YelpRecord,
        GoogleSearch,
        GoogleResult,
        FacebookSearch,
        FacebookResult,
        Chain,
        ApiKeys
    ])


# Create initial tables
if __name__ == "__main__":
    create_all_tables()
