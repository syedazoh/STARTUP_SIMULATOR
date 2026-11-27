"""Bounded historical transactions, kept separate from the simulator ledger."""
import csv
import io
import json
from datetime import datetime, timezone
from hashlib import sha256
from decimal import Decimal
from collections import defaultdict
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from pymongo.errors import DuplicateKeyError

class RetailRow(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    record_id:str=Field(min_length=1,max_length=120,pattern=r'^[\w.-]+$')
    invoice_id:str=Field(min_length=1,max_length=40)
    stock_code:str=Field(min_length=1,max_length=40)
    description:str=Field(min_length=1,max_length=500)
    quantity:int=Field(strict=True,ge=-1000000,le=1000000)
    unit_price_minor:int=Field(strict=True,gt=0,le=10**10)
    invoiced_at:datetime
    country:str=Field(min_length=1,max_length=100)
    source_row:int=Field(strict=True,ge=2)
    source_sheet:str=Field(default="Not recorded in upload",max_length=80)

    @field_validator('quantity')
    @classmethod
    def nonzero(cls,value):
        if value==0:raise ValueError('Zero quantity is not a transaction')
        return value

COLUMNS=list(RetailRow.model_fields)
MAX_BYTES=1024*1024

def parse(content,format):
    if len(content)>MAX_BYTES:raise HTTPException(413,'Retail file exceeds 1 MiB')
    errors=[];rows=[]
    try:
        text=content.decode('utf-8-sig')
        raw=json.loads(text) if format=='json' else list(csv.DictReader(io.StringIO(text))) if format=='csv' else None
        if not isinstance(raw,list) or not 1<=len(raw)<=1000:raise ValueError('Provide 1–1000 transaction rows')
        seen=set()
        for i,record in enumerate(raw,2):
            try:
                if format=='csv':
                    record=dict(record)
                    for field in ['quantity','unit_price_minor','source_row']:
                        value=record.get(field,'')
                        if not isinstance(value,str) or not value.lstrip('-').isdigit():raise ValueError(f'{field} requires an integer')
                        record[field]=int(value)
                row=RetailRow.model_validate(record)
                if row.record_id in seen:raise ValueError('Duplicate record_id in file')
                if row.invoice_id.upper().startswith('C') and row.quantity>0:raise ValueError('Cancellation invoice with positive quantity requires source review')
                seen.add(row.record_id);rows.append(row.model_dump(mode='json'))
            except (ValidationError,ValueError,TypeError) as exc:
                message='; '.join(e['msg'] for e in exc.errors(include_input=False)) if isinstance(exc,ValidationError) else str(exc)
                if len(errors)<20:errors.append({'row':i,'error':message[:500]})
    except (ValueError,UnicodeError,TypeError) as exc:raise HTTPException(422,str(exc)[:300]) from None
    return {'valid':not errors,'rows':rows,'errors':errors,'currency':'GBP','source_claim':'UCI Online Retail II — uploaded attribution, not independent source verification','timezone':'Original source time; timezone unspecified'}

def summarize(rows):
    products=defaultdict(lambda:{'gross_units':0,'returned_units':0,'adjustment_units':0,'net_units':0,'net_sales_minor':0})
    gross=returns=adjustments=net=0
    for row in rows:
        quantity,price=row['quantity'],row['unit_price_minor'];amount=quantity*price;net+=amount
        p=products[row['stock_code']];p['description']=row['description'];p['net_units']+=quantity;p['net_sales_minor']+=amount
        if quantity>0:gross+=amount;p['gross_units']+=quantity
        elif row['invoice_id'].upper().startswith('C'):returns-=amount;p['returned_units']-=quantity
        else:adjustments+=amount;p['adjustment_units']+=quantity
    return {'currency':'GBP','gross_sales_minor':gross,'cancellations_minor':returns,'other_adjustments_minor':adjustments,'net_sales_minor':net,'transaction_count':len(rows),'products':[{'stock_code':code,**data} for code,data in sorted(products.items(),key=lambda item:(-item[1]['gross_units'],item[0]))], 'rule':'Signed quantity × integer GBP pence. C-invoice negative quantities are cancellations; other negatives are separate adjustments. This is a historical slice, not your startup revenue.'}

async def import_rows(db,business,content,format,expected_digest):
    preview=parse(content,format)
    if not preview['valid']:raise HTTPException(422,preview['errors'])
    digest=sha256(json.dumps(preview['rows'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if digest!=expected_digest:raise HTTPException(409,'Preview changed; review the file again')
    identity=sha256(f'{business.id}:{digest}'.encode()).hexdigest()
    doc={'_id':identity,'import_id':identity,'business_id':business.id,'digest':digest,'rows':preview['rows'],'summary':summarize(preview['rows']),'source_claim':preview['source_claim'],'created_at':datetime.now(timezone.utc)}
    try:await db['retail_imports'].insert_one(doc)
    except DuplicateKeyError:pass
    return {k:v for k,v in doc.items() if k not in {'_id','rows'}}

async def latest(db,business_id):
    return await db['retail_imports'].find_one({'business_id':business_id},sort=[('created_at',-1)])
