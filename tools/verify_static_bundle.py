#!/usr/bin/env python3
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_PROBLEMS = 237
EXPECTED_SOURCES = 51


def read_data_from_html(path: Path):
    text = path.read_text(encoding='utf-8')
    m = re.search(r'const DATA = (.*?);\nconst CAN_EDIT\s*=\s*(true|false);', text, re.S)
    if not m:
        raise SystemExit(f'Не найден блок DATA/CAN_EDIT: {path}')
    return json.loads(m.group(1)), m.group(2) == 'true'


def main():
    public_data, public_edit = read_data_from_html(ROOT / 'docs' / 'index.html')
    admin_data, admin_edit = read_data_from_html(ROOT / 'docs' / 'admin.html')
    backup = json.loads((ROOT / 'docs' / 'data' / 'olympiad_database_full_backup.json').read_text(encoding='utf-8'))
    problems = json.loads((ROOT / 'docs' / 'data' / 'olympiad_problems_237.json').read_text(encoding='utf-8'))
    sources = json.loads((ROOT / 'docs' / 'data' / 'olympiad_source_catalog.json').read_text(encoding='utf-8'))

    checks = [
        ('public problem count', len(public_data.get('problems', [])), EXPECTED_PROBLEMS),
        ('admin problem count', len(admin_data.get('problems', [])), EXPECTED_PROBLEMS),
        ('backup problem count', len(backup.get('problems', [])), EXPECTED_PROBLEMS),
        ('problems json count', len(problems), EXPECTED_PROBLEMS),
        ('public source count', len(public_data.get('sources', [])), EXPECTED_SOURCES),
        ('admin source count', len(admin_data.get('sources', [])), EXPECTED_SOURCES),
        ('backup source count', len(backup.get('sources', [])), EXPECTED_SOURCES),
        ('source catalog count', len(sources), EXPECTED_SOURCES),
    ]
    ok = True
    for name, actual, expected in checks:
        status = 'OK' if actual == expected else 'FAIL'
        print(f'{status:4} {name}: {actual} expected {expected}')
        ok = ok and actual == expected

    print(('OK  ' if not public_edit else 'FAIL') + f'public CAN_EDIT: {public_edit}')
    print(('OK  ' if admin_edit else 'FAIL') + f'admin CAN_EDIT: {admin_edit}')
    ok = ok and (not public_edit) and admin_edit

    public_ids = [p.get('id') for p in public_data.get('problems', [])]
    admin_ids = [p.get('id') for p in admin_data.get('problems', [])]
    backup_ids = [p.get('id') for p in backup.get('problems', [])]
    json_ids = [p.get('id') for p in problems]
    same_ids = public_ids == admin_ids == backup_ids == json_ids
    print(('OK  ' if same_ids else 'FAIL') + 'problem ID order matches across HTML and JSON')
    ok = ok and same_ids

    if not ok:
        raise SystemExit(1)
    print('Пакет статической базы прошёл проверку.')


if __name__ == '__main__':
    main()
