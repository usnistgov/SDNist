import hashlib


def deid_data_hash(deid_data_path: str) -> str:
    """
    Compute the hash of the deid data csv file at
    give deid_data_path
    """
    with open(deid_data_path, 'r') as f:
        data_lines = f.readlines()
    data_str = ''
    for l in data_lines:
        data_str += l
    hasher = hashlib.sha1()
    hasher.update(data_str.encode('utf-8'))
    return hasher.hexdigest()

