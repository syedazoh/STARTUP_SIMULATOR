#!/usr/bin/env python3
"""Reproducible bounded OOXML slice. Never manufacture missing UCI observations.
Usage: python scripts/prepare_uci_retail.py /path/to/online_retail_II.xlsx
Workbook must be downloaded from the official UCI source. No customer IDs are retained.
"""
import argparse,csv,hashlib,json,math,re,zipfile
from pathlib import Path
from decimal import Decimal,InvalidOperation
from datetime import datetime,timedelta
from xml.etree import ElementTree as ET
NS='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
SOURCE='https://archive.ics.uci.edu/dataset/502/online+retail+ii'

def extract(workbook,limit):
    fingerprint=hashlib.sha256(workbook.read_bytes()).hexdigest();sales=[];returns=[];rejected={};scanned=0
    with zipfile.ZipFile(workbook) as z:
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            with z.open('xl/sharedStrings.xml') as f:
                for _,el in ET.iterparse(f,events=['end']):
                    if el.tag==NS+'si':strings.append(''.join(x.text or '' for x in el.iter(NS+'t')));el.clear()
        sheets=sorted(name for name in z.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',name))
        for sheet in sheets:
            header=None
            with z.open(sheet) as f:
                for _,el in ET.iterparse(f,events=['end']):
                    if el.tag!=NS+'row':continue
                    values={}
                    for cell in el.findall(NS+'c'):
                        col=re.sub(r'\d','',cell.attrib['r']);value=cell.findtext(NS+'v')
                        if cell.attrib.get('t')=='s':value=strings[int(value)] if value is not None else ''
                        elif cell.attrib.get('t')=='inlineStr':value=''.join(x.text or '' for x in cell.iter(NS+'t'))
                        values[col]=value
                    source_row=int(el.attrib['r']);el.clear()
                    if header is None:header={col:(value or '').strip() for col,value in values.items()};continue
                    record={header.get(col,col):value for col,value in values.items()};scanned+=1
                    try:
                        quantity=Decimal(record.get('Quantity') or 'NaN');price=Decimal(record.get('Price',record.get('UnitPrice')) or 'NaN');invoice=str(record.get('Invoice',record.get('InvoiceNo')) or '').strip();description=(record.get('Description') or '').strip();stock=str(record.get('StockCode') or '').strip()
                        if not quantity.is_finite() or quantity!=int(quantity) or quantity==0 or not price.is_finite() or price<=0 or price*100!=(price*100).to_integral_value() or not invoice or not description or not stock:raise ValueError('invalid quantity/price/identity')
                        if invoice.upper().startswith('C') and quantity>0:raise ValueError('positive cancellation quantity')
                        date=record.get('InvoiceDate') or '';date=(datetime(1899,12,30)+timedelta(days=float(date))).isoformat(timespec='seconds')
                        row={'record_id':hashlib.sha256(f'{fingerprint}:{sheet}:{source_row}'.encode()).hexdigest(),'invoice_id':invoice,'stock_code':stock,'description':description,'quantity':int(quantity),'unit_price_minor':int(price*100),'invoiced_at':date,'country':record.get('Country') or 'Unspecified in source','source_row':source_row,'source_sheet':sheet}
                        bucket=returns if quantity<0 else sales
                        if len(bucket)<(max(1,limit//5) if quantity<0 else limit-max(1,limit//5)):bucket.append(row)
                    except (ValueError,InvalidOperation,OverflowError,TypeError) as error:rejected[str(error)]=rejected.get(str(error),0)+1
                    if len(sales)+len(returns)>=limit:break
            if len(sales)+len(returns)>=limit:break
    return sales+returns,{'source_url':SOURCE,'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','source_workbook_sha256':fingerprint,'scanned_rows':scanned,'excluded_counts':rejected,'selection':'First bounded positive-quantity rows and first bounded negative-quantity rows in sheet order. Stratified illustration, not an unbiased population sample.','changes':['Customer ID omitted','ISO local timestamps; source timezone unspecified','Exact positive prices converted to integer GBP pence','Signed quantities and cancellation invoice markers retained','Invalid/blank/non-positive-price rows excluded and counted'],'attribution':'Online Retail II, UCI Machine Learning Repository; verify original creator/donor credit from the linked official metadata before redistribution.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('workbook',type=Path);parser.add_argument('--out',type=Path,default=Path('datasets/retail-uci-v1'));parser.add_argument('--limit',type=int,default=250);args=parser.parse_args()
    if not 10<=args.limit<=1000:parser.error('--limit must be between 10 and 1000')
    rows,metadata=extract(args.workbook,args.limit)
    if not rows:raise SystemExit('No valid source rows; no synthetic substitute was written.')
    args.out.mkdir(parents=True,exist_ok=True);(args.out/'transactions.json').write_text(json.dumps(rows,indent=2)+'\n');metadata['selected_rows']=len(rows)
    with (args.out/'transactions.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
    metadata['transformed_json_sha256']=hashlib.sha256((args.out/'transactions.json').read_bytes()).hexdigest();(args.out/'provenance.json').write_text(json.dumps(metadata,indent=2)+'\n');print(f'Wrote {len(rows)} attributed source rows; source hash {metadata["source_workbook_sha256"]}')
if __name__=='__main__':main()
