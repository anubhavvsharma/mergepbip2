import copy
import json
import pathlib
import uuid

ROOT = pathlib.Path(__file__).resolve().parent / 'mergepbip2-main'
PAGES = ROOT / 'Mergefile.Report/definition/pages'
SOURCE = PAGES / '35d0881ddb25c6a26e73'
DEST = PAGES / '4d192e86b046a85ab4e5'
templates = {p.parent.name: json.loads(p.read_text(encoding='utf-8-sig')) for p in SOURCE.glob('visuals/*/visual.json')}
visuals = []
def lit(v): return {'expr': {'Literal': {'Value': str(v)}}}
def color(v): return {'solid': {'color': lit("'" + v + "'")}}
def field(table, prop, measure=False):
    return {'Measure' if measure else 'Column': {'Expression': {'SourceRef': {'Entity': table}}, 'Property': prop}}
def projection(table, prop, measure=False, label=None):
    d = {'field': field(table, prop, measure), 'queryRef': table+'.'+prop, 'nativeQueryRef': label or prop}
    if not measure: d['active'] = True
    return d
def make(template, x, y, w, h):
    d = copy.deepcopy(templates[template]); d['name'] = uuid.uuid4().hex[:20]
    d['position'] = dict(x=x,y=y,width=w,height=h,z=len(visuals)*1000,tabOrder=len(visuals)*1000)
    d.pop('filterConfig', None)
    visuals.append(d)
    return d
def panel(x,y,w,h,fill='#FFFFFF'):
    d=make('06903788f8b04ceabfa3',x,y,w,h)
    d['visual']['objects']['fill'][0]['properties']['fillColor']=color(fill)
    return d
def text(value,x,y,w,h=26,size='11pt',ink='#20242C',bold=False):
    d=make('b87e60ac650c4a1a9d4c',x,y,w,h)
    d['visual']['objects']['general'][0]['properties']['paragraphs']=[{'textRuns':[{'value':value,'textStyle':{'fontFamily':'Segoe UI','fontSize':size,'color':ink,'fontWeight':'bold' if bold else 'normal'}}]}]
    return d
def slicer(label,table,prop,x,y,w):
    text(label,x,y,w,24,'11pt','#63666D',True)
    d=make('54cabc1272da489f85b5',x,y+28,w,52)
    d['visual']['query']={'queryState':{'Values':{'projections':[projection(table,prop)]}}}
    d['visual']['objects']['header'][0]['properties']['text']=lit("'"+label+"'")
def nav(label,y,target,selected=False):
    if selected: panel(14,y,232,46)
    text(label,30,y+12,212,26,'10pt','#F58220' if selected else '#FFFFFF',True)
    if target:
        d=make('27e23ab9a4364ea89173',14,y,232,46)
        for fill in d['visual']['objects']['fill']: fill['properties']['show']=lit('false')
        d['visual']['visualContainerObjects']['visualLink'][0]['properties']['navigationSection']=lit("'"+target+"'")

panel(0,0,1920,1080,'#F58220')
panel(260,74,1660,1006,'#F7F7F5')
text('GSK',22,14,72,32,'18px','#FFFFFF',True)
text('Citation Impact',108,14,420,32,'18px','#FFFFFF',True)
nav('Portfolio Overview',84,SOURCE.name)
nav('Citation Impact',136,DEST.name,True)
for label,y in [('Most Cited Publications',188),('Attention & Reach',240),('Journal Landscape',292),('Sentiment & Reception',344)]: nav(label,y,None)
text('SOURCES',22,976,210,20,'8pt','#FFFFFF',True)
text('Dimensions — publications, citations\nAltmetric — attention, sentiment',22,1008,225,56,'8pt','#FFFFFF')
panel(280,78,1620,118)
for i,(label,table,prop) in enumerate([
    ('Business Unit','dim_Product','Business Unit'),('Primary Product','dim_Product','Primary Product'),
    ('Priority','dim_Product','Priority Label'),('Managed by','dim_Managed','Managed by'),('Region','PublicationRegion','Region')]):
    slicer(label,table,prop,292+i*322,88,304)
panel(280,206,1620,100)
slicer('Business area','dim_Product','Business Unit',292,216,360)
slicer('Disclosure type','enr_publication','publication_type',694,216,360)
text('Impact factor',1096,216,360,24,'11pt','#63666D',True)
text('Not available',1108,252,340,30,'10pt','#89867F')
slicer('Open access route','enr_publication','OA Group',1498,216,388)
for i,(label,measure) in enumerate([('Total Citations','Total Citations'),('Cited Publications','Cited Publications'),('% Cited','Cited Publications %'),('Median Citations','Median Citations')]):
    x=280+i*408
    panel(x,318,396,94)
    text(label,x+16,328,364,22,'10pt','#63666D',True)
    d=make('858f1646559147d2a345',x+16,354,364,48)
    d['visual']['query']={'queryState':{'Values':{'projections':[projection('_Measures',measure,True)]}}}
    d['visual']['objects']['labels'][0]['properties']['color']=color('#F58220' if i>=2 else '#20242C')

for i,(title,measures) in enumerate([
    ('Total Citations by Year',['Previous Years Citations','Current Year Citations']),
    ('Recent Citations by Year',['Previous Years Recent Citations','Current Year Recent Citations'])]):
    x=280+i*816
    panel(x,422,804,354)
    text(title,x+18,434,768,26,'11pt','#20242C',True)
    d=make('aa4901b690cb4ef38169',x+12,466,780,298)
    v=d['visual']; v['visualType']='stackedColumnChart'
    v['query']={'queryState':{'Category':{'projections':[projection('enr_publication','publication_year')]},'Y':{'projections':[projection('_Measures',m,True,label) for m,label in zip(measures,['Previous years','Current year'])]}},'sortDefinition':{'sort':[{'field':field('enr_publication','publication_year'),'direction':'Ascending'}]}}
    o=v['objects']
    o['dataPoint']=[{'properties':{'fill':color(c)},'selector':{'metadata':'_Measures.'+m}} for m,c in zip(measures,['#CFCDC6','#F58220'])]
    o['legend']=[{'properties':{'show':lit('true'),'position':lit("'Bottom'"),'showTitle':lit('false'),'fontSize':lit('8D')}}]
    for axis in ['categoryAxis','valueAxis']: o[axis][0]['properties']['showAxisTitle']=lit('false')
    o['valueAxis'][0]['properties']['gridlineShow']=lit('true')
    o['labels'][0]['properties']['fontSize']=lit('9D')

panel(280,790,1620,266)
text('Publication Detail',298,802,1578,26,'11pt','#20242C',True)
d=make('aa4901b690cb4ef38169',294,836,1590,206)
cols=[projection('_Measures','Citation Detail Serial',True,'#'),projection('enr_publication','Publication Short Name'),projection('enr_publication','journal_title_raw',label='Journal'),projection('enr_publication','publication_year',label='Year'),projection('_Measures','Total Citations',True),projection('_Measures','Recent Citations',True)]
d['visual']={'visualType':'tableEx','query':{'queryState':{'Values':{'projections':cols}},'sortDefinition':{'sort':[{'field':field('_Measures','Total Citations',True),'direction':'Descending'}]}},'objects':{
    'grid':[{'properties':{'gridVertical':lit('false'),'gridHorizontal':lit('true'),'rowPadding':lit('5D'),'textSize':lit('9D')}}],
    'columnHeaders':[{'properties':{'fontColor':color('#63666D'),'backColor':color('#FFFFFF'),'fontSize':lit('9D'),'wordWrap':lit('false')}}],
    'values':[{'properties':{'fontColorPrimary':color('#20242C'),'backColorPrimary':color('#FFFFFF'),'backColorSecondary':color('#FAF9F7'),'fontSize':lit('9D'),'wordWrap':lit('false')}}],
    'total':[{'properties':{'totals':lit('false')}}],
    'columnWidth':[{'properties':{'value':lit(str(w)+'D')},'selector':{'metadata':c['queryRef']}} for c,w in zip(cols,[44,480,280,100,330,330])]
},'visualContainerObjects':copy.deepcopy(templates['aa4901b690cb4ef38169']['visual']['visualContainerObjects'])}

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
assert not DEST.exists(), 'Citation Impact page already exists; refusing to overwrite.'
page=json.loads((SOURCE/'page.json').read_text()); page.update(name=DEST.name,displayName='Citation Impact')
write(DEST/'page.json',page)
for d in visuals: write(DEST/'visuals'/d['name']/'visual.json',d)
metadata=json.loads((PAGES/'pages.json').read_text()); metadata['pageOrder'].append(DEST.name); metadata['activePageName']=DEST.name
write(PAGES/'pages.json',metadata)
print(f'Created Citation Impact: {len(visuals)} visuals, two column charts, no median series.')
import runpy
runpy.run_path(str(pathlib.Path(__file__).with_name('repair_citation_page.py')), run_name='__main__')
