"""Read one actual acquisition by scene, point, antenna and repeat; indices are one-based."""
import argparse
import csv
from pathlib import Path
import h5py
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario',required=True,choices=['sc1','sc2','sc3','sc4'])
    parser.add_argument('--point',required=True,help='P01, P03, … or CAL for calibration')
    parser.add_argument('--repeat',required=True,type=int)
    parser.add_argument('--antenna',required=True,choices=['directional','omni'])
    parser.add_argument('--root',type=Path,default=ROOT,help='Directory containing the restored data/ tree')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    with (ROOT/'metadata/measurements.csv').open(encoding='utf-8-sig',newline='') as stream:
        selected=[r for r in csv.DictReader(stream) if r['scenario']==args.scenario and r['point'].upper()==args.point.upper()
                  and int(r['repeat_index'])==args.repeat and r['antenna']==args.antenna]
    if len(selected)!=1:
        parser.error(f'Expected one acquisition, found {len(selected)}; check the point/repeat.')
    record=selected[0]
    raw=args.root/record['raw_file']
    if not raw.is_file():
        parser.error(f'Restore the release data first: {record["raw_file"]}')
    pos=int(record['raw_position_index'])-1
    repeat=int(record['repeat_index'])-1
    with h5py.File(raw,'r') as h:
        vector=h['S21'][:,repeat,pos]
        s21=vector['real'].astype('float64')+1j*vector['imag'].astype('float64')
        freq=h['frequencyHz'][:].reshape(-1)
        time=h['timeSec'][:].reshape(-1)
        tdr=h['TDR'][:,repeat,pos]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream)
        writer.writerow(['frequency_hz','s21_real','s21_imag','s21_magnitude_db','s21_phase_deg','time_sec','tdr_raw'])
        writer.writerows(zip(freq,s21.real,s21.imag,20*np.log10(np.maximum(np.abs(s21),1e-30)),np.angle(s21,deg=True),time,tdr))
    print(f'{record["campaign"]}: {record["point"]}, raw position {pos+1}, repeat {repeat+1}; {len(freq)} rows -> {args.output}')

if __name__=='__main__':
    main()
