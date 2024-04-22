# check how timezone gets printed when converting to json?


from datetime import datetime, timezone
from typing import TypedDict
import json


class tlog(TypedDict):
    time: datetime
    name: str


t = datetime.now(timezone.utc)

tdict: tlog = {"time": t, "name": "swarnim"}

tjson = json.dumps(tdict, indent=2)
