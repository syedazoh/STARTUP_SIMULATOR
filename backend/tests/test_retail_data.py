"""Synthetic arithmetic fixtures, never mislabelled as downloaded UCI rows."""
import csv,io,json
from tests.test_businesses import client,_register_and_login,_auth_headers
from app.services.retail_data import parse,summarize

def rows():
    base={'description':'Synthetic product','invoiced_at':'2010-01-01T12:00:00','country':'United Kingdom'}
    return [{**base,'record_id':f'fixture-{i}','invoice_id':invoice,'stock_code':code,'quantity':q,'unit_price_minor':p,'source_row':i+2} for i,(invoice,code,q,p) in enumerate([('1','A',3,200),('C1','A',-1,200),('2','B',2,100),('3','B',-1,100)])]

def test_sales_demand_returns_and_adjustments_are_exact_and_distinct():
    result=summarize(parse(json.dumps(rows()).encode(),'json')['rows'])
    assert result['gross_sales_minor']==800;assert result['cancellations_minor']==200;assert result['other_adjustments_minor']==-100;assert result['net_sales_minor']==500
    assert result['products'][0]['stock_code']=='A';assert result['products'][0]['returned_units']==1;assert result['currency']=='GBP'

def test_validation_rejects_duplicate_zero_bad_money_and_cancellation_sign():
    for records in [rows()+[rows()[0]],[{**rows()[0],'quantity':0}],[{**rows()[0],'unit_price_minor':True}],[{**rows()[0],'quantity':1.5}],[{**rows()[0],'invoice_id':'C1'}]]:
        result=parse(json.dumps(records).encode(),'json');assert result['valid'] is False;assert result['errors'][0]['row']>=2

def test_preview_import_is_scoped_and_idempotent_without_ledger_effects(client):
    owner=_auth_headers(_register_and_login(client,'retail-owner@example.com'));other=_auth_headers(_register_and_login(client,'retail-other@example.com'))
    bid=client.post('/api/businesses',headers=owner,json={'company_name':'Retail fixture','industry':'Software'}).json()['id'];root=f'/api/businesses/{bid}/retail'
    content=json.dumps(rows()).encode();files={'file':('synthetic-arithmetic-fixture.json',content,'application/json')}
    preview=client.post(root+'/preview',headers=owner,files=files,data={'format':'json'});assert preview.status_code==200,preview.text
    assert preview.json()['valid'];assert 'uploaded attribution' in preview.json()['source_claim']
    data={'format':'json','expected_digest':preview.json()['digest']}
    first=client.post(root+'/import',headers=owner,files=files,data=data);assert first.status_code==200,first.text
    assert client.post(root+'/import',headers=owner,files=files,data=data).json()['import_id']==first.json()['import_id']
    assert client.post(root+'/import',headers=owner,files=files,data={**data,'expected_digest':'bad'}).status_code==409
    assert client.get(root,headers=other).status_code==403;assert client.post(root+'/import',headers=other,files=files,data=data).status_code==403
    assert client.get(f'/api/businesses/{bid}/tasks',headers=owner).json()==[]
    assert client.get(root,headers=owner).json()['summary']['net_sales_minor']==500
