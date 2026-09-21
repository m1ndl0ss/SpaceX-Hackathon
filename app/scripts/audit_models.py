"""Audit the checked-in models without retraining or modifying team artifacts."""
from pathlib import Path
import sys
import json
import itertools
import time

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP.parent / 'ai/models/src'))
from impact_models.schema import Treatment
from impact_models.infer import infer, load_boosters
from impact_models.features import FEATURE_COLUMNS
from impact_models.context import load_context, country_for_point
from impact_models.geo import min_dist_geometry_m

start = time.monotonic()
pins = {'Dordrecht': (4.72, 51.797), 'Limburg': (5.696, 50.851), 'Namur': (4.87, 50.47), 'Luxembourg': (6.13, 49.61), 'Ardennes': (6.13, 50.52)}
base = Path(APP.parent / 'ai/models/artifacts')
metrics = json.loads((base / 'metrics.json').read_text())
summary = json.loads((base / 'training_summary.json').read_text())
issues = {key: [] for key in ['invalid_ranges', 'scale_reversals', 'cooling_reversals', 'buffer_reversals', 'nearby_reversals', 'unexpected_habitat_time_variation']}
records = []
cache = {}
def predict(kind, name, scale=1.0, year=2035, cooling=False, buffer=False, nearby=()):
    key = (kind, name, scale, year, cooling, buffer, tuple(nearby))
    if key not in cache:
        treatment = Treatment(typeId=kind, center=pins[name], scale=scale, horizonYear=year, cooling=cooling, buffer=buffer, nearbyTreatments=[{'typeId': t, 'center': c} for t,c in nearby])
        result = infer(treatment)
        for head, q in result.outcomes.model_dump().items():
            if not q['p10'] <= q['p50'] <= q['p90'] or (head != 'tco2e' and q['p10'] < 0):
                issues['invalid_ranges'].append({'type':kind,'pin':name,'head':head,'values':q})
        cache[key] = result
    return cache[key]
for spec, name in itertools.product(load_context()['projectTypes'], pins):
    kind = spec['id']
    original = predict(kind,name)
    records.append({'type':kind,'pin':name,'outcomes':original.outcomes.model_dump(),'sites':len(original.sites),'country':original.country})
    for head in ['habitatHa','vegStress','jobsFte']:
        values = [getattr(predict(kind,name,scale=s).outcomes,head).p50 for s in [0.4,1.0,2.0]]
        if any(b + 1e-6 < a for a,b in zip(values,values[1:])):
            issues['scale_reversals'].append({'type':kind,'pin':name,'head':head,'values':values})
    buffered = predict(kind,name,buffer=True)
    for head in ['habitatHa','vegStress','riverTempC']:
        before,after = getattr(original.outcomes,head).p50,getattr(buffered.outcomes,head).p50
        if after > before + 1e-6:
            issues['buffer_reversals'].append({'type':kind,'pin':name,'head':head,'before':before,'after':after})
    if kind in ['datacentre','industrial']:
        cooled = predict(kind,name,cooling=True)
        if cooled.outcomes.riverTempC.p50 > original.outcomes.riverTempC.p50 + 1e-6:
            issues['cooling_reversals'].append({'type':kind,'pin':name,'before':original.outcomes.riverTempC.p50,'after':cooled.outcomes.riverTempC.p50})
    lng,lat = pins[name]
    busy = predict(kind,name,nearby=(('highway',(lng+0.001,lat+0.001)),))
    if busy.outcomes.habitatHa.p50 + 1e-6 < original.outcomes.habitatHa.p50:
        issues['nearby_reversals'].append({'type':kind,'pin':name,'before':original.outcomes.habitatHa.p50,'after':busy.outcomes.habitatHa.p50})
    values = [predict(kind,name,year=y).outcomes.habitatHa.p50 for y in [2026,2035,2040]]
    if max(values)-min(values) > 0.1:
        issues['unexpected_habitat_time_variation'].append({'type':kind,'pin':name,'values':values})

holes = {'type':'Polygon','coordinates':[[[4,50],[5,50],[5,51],[4,51],[4,50]],[[4.2,50.2],[4.8,50.2],[4.8,50.8],[4.2,50.8],[4.2,50.2]]]}
report = {
    'labelKind':'synthetic_scenario', 'artifactOnly':True, 'inferenceCount':len(cache), 'seconds':round(time.monotonic()-start,2),
    'featureOrderMatches': all(booster.feature_name() == list(FEATURE_COLUMNS) for booster in load_boosters().values()),
    'validation': {head:{'mae':data['p50']['mae'],'coverage80':data['coverage80'],'quantileCrossingBeforeSort':data['crossingBeforeSort']} for head,data in metrics['heads'].items()},
    'split':metrics['split'], 'constantFeatures':summary['constantFeatures'],
    'issues':issues, 'issueCounts':{key:len(value) for key,value in issues.items()},
    'geometryProbe': {'distanceInsidePolygonHoleM':min_dist_geometry_m((4.5,50.5),holes), 'expected':'Positive distance to polygon boundary; zero demonstrates that holes are ignored.'},
    'outOfRegionProbe': {'point':[0,0], 'assignedCountry':country_for_point((0,0)), 'schemaAccepts':bool(Treatment(typeId='wind',center=(0,0)))},
    'examples':records,
}
target = APP / 'docs/model-audit.json'
target.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['examples','issues','constantFeatures']},indent=2))
