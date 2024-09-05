import datetime
import uuid


def generate_s3_key() -> str:
    now = datetime.datetime.now(datetime.UTC)
    return now.isoformat() + "-" + str(uuid.uuid4())
