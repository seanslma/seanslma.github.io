import os
import sys
import pandas as pd
import xml.etree.ElementTree as eltree

typ = 'rec'
dir = r'C:\mssql\migrate_cli'
dtfile = os.path.join(dir, f'list_{typ}.txt')
report_file = 'DataMigrationReport.xml'

folder = 'tmp\\' if typ == 'db' else rf'tmp\{typ}__'
dt_name = 'db_name' if typ == 'db' else 'tb_name'


def main(argv):
    reports = [
        [dt] + parse_xml(os.path.join(dir, f'{folder}{dt}', report_file))
        for dt in load_dt_names(dtfile)
    ]
    cols = [
        dt_name,
        'total_tables',
        'tables_successfully_migrated',
        'tables_partially_migrated',
        'tables_failed_to_migrate',
    ]
    df = pd.DataFrame(columns=cols, data=reports)
    df.to_csv(os.path.join(dir, 'wrk', f'migrate_report_{typ}.csv'), index=False)
    ok = 1


def load_dt_names(dtfile):
    with open(dtfile, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    return lines


def parse_xml(xmlfile):
    tree = eltree.parse(xmlfile)  # create element tree object
    root = tree.getroot()  # get root element
    attrib = root[0].attrib  # get first child's attribute
    report = [
        attrib['total-tables'],
        attrib['tables-successfully-migrated'],
        attrib['tables-partially-migrated'],
        attrib['tables-failed-to-migrate'],
    ]
    return report


if __name__ == "__main__":
    main(sys.argv)
