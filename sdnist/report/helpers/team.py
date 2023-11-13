import re
import uuid
import time


def team_uid() -> str:
    # Generating a UUID
    generated_uuid = uuid.uuid4()

    # Getting the current timestamp
    current_timestamp = int(time.time() * 1000000)  # Microseconds precision

    # Combining UUID and timestamp into a string
    combined_string = f"{generated_uuid}-{current_timestamp}"

    return combined_string


def is_valid_team_uid(identifier: str) -> bool:
    try:
        uuid_part, timestamp = identifier.rsplit('-', 1)
        uuid.UUID(uuid_part)
        if not re.match(r'^\d+$', timestamp):
            raise ValueError
        return True
    except ValueError:
        return False


def is_valid_email(email: str) -> bool:
    pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
    return bool(pattern.match(email))
