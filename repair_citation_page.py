"""Repair the saved Citation Impact visuals using native Power BI visuals."""
import copy
import json
import pathlib
import uuid
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT = ROOT / 'mergepbip2-main'
PAGES = PROJECT / 'Mergefile.Report/definition/pages'
PAGE = PAGES / '4d192e86b046a85ab4e5'
SOURCE = PAGES / '35d0881ddb25c6a26e73/visuals'
backup = ROOT / 'citation_before_repair.zip'
if not backup.exists():
    with zipfile.ZipFile(backup, 'w', zipfile.ZIP_DEFLATED) as archive:
        for p in PAGE.rglob('*'):
            if p.is_file(): archive.write(p, p.relative_to(PROJECT))

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def lit(v): return {'expr':{'Literal':{'Value':v}}}
def color(v): return {'solid':{'color':lit("'"+v+"'")}}
def field(table,prop,measure=False): return {'Measure' if measure else 'Column':{'Expression':{'SourceRef':{'Entity':table}},'Property':prop}}
def projection(table,prop,measure=False): return {'field':field(table,prop,measure),'queryRef':table+'.'+prop,'nativeQueryRef':prop,'active':True}

files = [(p,read(p)) for p in PAGE.glob('visuals/*/visual.json')]
charts = sorted([(p,d) for p,d in files if d['visual']['visualType'].startswith('deneb') or d['visual']['visualType'] in ('stackedColumnChart','clusteredColumnChart')], key=lambda item:item[1]['position']['x'])
assert len(charts)==2, 'Expected exactly two citation charts'
template=read(SOURCE/'aa4901b690cb4ef38169/visual.json')
for i,(p,d) in enumerate(charts):
    measure=['Total Citations','Recent Citations'][i]
    d['visual']=copy.deepcopy(template['visual'])
    d['position'].update(x=292+816*i,y=452,width=780,height=288)
    d.pop('filterConfig',None)
    v=d['visual'];v['visualType']='clusteredColumnChart'
    v['query']={'queryState':{'Category':{'projections':[projection('enr_publication','publication_year')]},'Y':{'projections':[projection('_Measures',measure,True)]}},'sortDefinition':{'sort':[{'field':field('enr_publication','publication_year'),'direction':'Ascending'}]}}
    o=v['objects']
    o['dataPoint'][1]['properties']['fill']['solid']['color']['expr']=field('_Measures','Citation Year Color',True)
    for axis in ['categoryAxis','valueAxis']:
        o[axis][0]['properties']['showAxisTitle']=lit('false')
        o[axis][0]['properties'].pop('titleText',None)
    o['valueAxis'][0]['properties'].update(gridlineShow=lit('true'),labelDisplayUnits=lit('1000D'))
    o['labels'][0]['properties'].update(labelDisplayUnits=lit('1D'),fontSize=lit('9D'))
    v['drillFilterOtherVisuals']=True
    write(p,d)
    # Explicit legend swatches preserve a single full-width bar per year.
    for j,(label,ink) in enumerate([('Previous years','#CFCDC6'),('Current year','#F58220')]):
        ident=uuid.uuid5(uuid.NAMESPACE_URL,f'citation-legend-{i}-{j}').hex[:20]
        t=read(SOURCE/'387a5418f0c24148a4e8/visual.json');t['name']=ident
        t['position'].update(x=500+i*816+j*160,y=746,width=160,height=22,z=60000+i*2000+j*1000)
        t['visual']['objects']['general'][0]['properties']['paragraphs']=[{'textRuns':[{'value':'■ ','textStyle':{'fontFamily':'Segoe UI','fontSize':'10px','color':ink}},{'value':label,'textStyle':{'fontFamily':'Segoe UI','fontSize':'9px','color':'#747985'}}]}]
        write(PAGE/'visuals'/ident/'visual.json',t)

for p,d in files:
    v=d['visual'];kind=v['visualType']
    if kind=='card':
        v['objects']['labels'][0]['properties']['labelDisplayUnits']=lit('1D')
        prop=v['query']['queryState']['Values']['projections'][0]['field']['Measure']['Property']
        v['objects']['labels'][0]['properties']['labelPrecision']=lit('1L' if prop in ('Median Citations','Cited Publications %') else '0L')
    elif kind=='tableEx':
        for q in v['query']['queryState']['Values']['projections']:q['active']=True
        v['objects']['columnFormatting']=[{'selector':{'metadata':'_Measures.'+m},'properties':{'dataBars':{'positiveColor':color('#EE875F'),'negativeColor':color('#EE875F'),'axisColor':color('#FFFFFF'),'reverseDirection':lit('false'),'hideText':lit('false')},'labelDisplayUnits':lit('1D'),'labelPrecision':lit('0L')}} for m in ['Total Citations','Recent Citations']]
        v['objects']['general']=[{'properties':{'autoSizeColumnWidth':lit('false')}}]
        v['drillFilterOtherVisuals']=True
    elif kind=='slicer':
        v['objects']['header'][0]['properties']['show']=lit('false')
        # Remove inherited stale filter values while retaining the bound field.
        v['objects']['general']=[{'properties':{}}]
    else: continue
    write(p,d)

measures=PROJECT/'Mergefile.SemanticModel/definition/tables/_Measures.tmdl'
s=measures.read_text(encoding='utf-8-sig')
if "measure 'Citation Year Color'" not in s:
    addition="\n\tmeasure 'Citation Year Color' =\n\t\t\tVAR LatestYear = CALCULATE ( MAX ( enr_publication[publication_year] ), REMOVEFILTERS ( enr_publication[publication_year] ), REMOVEFILTERS ( 'Date'[Year] ) )\n\t\t\tRETURN IF ( SELECTEDVALUE ( enr_publication[publication_year] ) = LatestYear, \"#F58220\", \"#CFCDC6\" )\n\t\tlineageTag: "+str(uuid.uuid4())+'\n'
    # Insert among measures, before any table-level partitions or annotations.
    pos=s.index('\n\tmeasure ')
    s=s[:pos]+addition+s[pos:]
    measures.write_text(s,encoding='utf-8')
print('Repaired native charts, activated table measures, added citation data bars and full-number cards.')
