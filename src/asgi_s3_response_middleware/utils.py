import datetime
import uuid


def generate_s3_key() -> str:
    return datetime.datetime.now().isoformat() + "-" + str(uuid.uuid4())
