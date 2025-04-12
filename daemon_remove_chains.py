import time
from web.models import Chain, YelpRecord

while True:
    # Both the chain and the restaurant name are converted to lowercase when they are fuzzy tested
    chains = list(map(lambda c: c.name.lower(), Chain().select()))

    for record in YelpRecord.select().where(YelpRecord.is_chain == False):
        if record.name.lower() in chains:
            print(f"Flagging {record.name} because it's in the chain list")
            record.is_chain = True
            record.save()

    print("done")
    time.sleep(15)
