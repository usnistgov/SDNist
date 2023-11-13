from metareport.common import \
    json, Dict, List, Path, pd, Optional


def create_empty_jsons(paths: List[Path]):
    for path in paths:
        for file in path.glob('**/*.csv'):
            json_file = file.with_suffix('.json')
            if not json_file.exists():
                with open(json_file, 'w') as f:
                    json.dump({}, f)
                    print('Created empty json file: {}'.format(json_file))


paths = [Path("toy_synthetic_data/syn/synthetic")]
out_dir = Path('data')

if __name__ == "__main__":
    create_empty_jsons(paths)
