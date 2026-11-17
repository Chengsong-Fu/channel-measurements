"""Search the small acquisition catalog without downloading the raw data."""
import argparse
import csv
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--scenario',choices=['sc1','sc2','sc3','sc4'])
parser.add_argument('--point',help='P01, P03, … or CAL')
parser.add_argument('--repeat',type=int)
parser.add_argument('--antenna',choices=['directional','omni'])
parser.add_argument('--distance-min',type=float)
parser.add_argument('--distance-max',type=float)
parser.add_argument('--output',type=Path)
args=parser.parse_args()
with (Path(__file__).resolve().parents[1]/'metadata/measurements.csv').open(encoding='utf-8-sig',newline='') as stream:
    reader=csv.DictReader(stream)
    fields=reader.fieldnames
    matches=[]
    for row in reader:
        if args.scenario and row['scenario']!=args.scenario:continue
        if args.point and row['point'].upper()!=args.point.upper():continue
        if args.repeat and int(row['repeat_index'])!=args.repeat:continue
        if args.antenna and row['antenna']!=args.antenna:continue
        distance=float(row['distance_m']) if row['distance_m'] else None
        if args.distance_min is not None and (distance is None or distance<args.distance_min):continue
        if args.distance_max is not None and (distance is None or distance>args.distance_max):continue
        matches.append(row)
if args.output:
    with args.output.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader()
        writer.writerows(matches)
else:
    for row in matches[:30]:
        print(row['campaign'],row['point'],'R'+row['repeat_index'],row['distance_m'] or 'distance unavailable',row['antenna'])
print(f'{len(matches)} matching acquisitions')
