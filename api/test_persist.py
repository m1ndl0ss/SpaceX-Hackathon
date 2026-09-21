"""Smoke the persistence API against a throwaway SQLite file."""
import os
import tempfile
from pathlib import Path

os.environ['APP_DB'] = str(Path(tempfile.mkdtemp()) / 'app.db')

from fastapi.testclient import TestClient

from api.main import app


def run():
    with TestClient(app) as client:
        health = client.get('/health').json()
        assert health['persist'] is True

        sites = client.get('/sites').json()
        assert len(sites) == 3
        assert sites[0]['coords']
        assert 'fundingGap' in sites[0]

        stats = client.get('/stats').json()
        assert stats['hectares'] == 2480
        assert stats['funding_eur'] == 186400
        assert stats['people'] == 126
        assert stats['funding_split'] is None

        lookups = client.get('/lookups').json()
        assert 'Dordrecht' in lookups['regions']
        assert any(h['id'] == 'survey' for h in lookups['helpOptions'])

        opps = {o['id']: o for o in client.get('/opportunities').json()}
        assert opps['wetlands']['spots'] == 7

        people = client.post('/auth/people', json={
            'name': 'Test Volunteer',
            'place': 'Dordrecht',
            'help': 'survey',
        }).json()
        assert people['org'] == 'Independent'
        assert people['type'] == 'person'
        assert people['role'] == 'people'
        assert people['joined'] == []
        token = people['token']
        headers = {'Authorization': f'Bearer {token}'}

        joined = client.post('/opportunities/wetlands/join', headers=headers).json()
        assert 'wetlands' in joined['joined']
        assert joined['opportunity']['spots'] == 6

        clash = client.post('/opportunities/wetlands/join', headers=headers)
        assert clash.status_code == 409

        left = client.post('/opportunities/wetlands/leave', headers=headers).json()
        assert 'wetlands' not in left['joined']
        assert left['opportunity']['spots'] == 7

        report = client.post('/reports', headers=headers, json={
            'place': 'Wantij',
            'note': 'Kingfisher bank slip',
        }).json()
        assert report['status'] == 'Awaiting verification'
        assert report['lng'] == 4.69
        assert report['lat'] == 51.805
        assert report['who'] == 'Test Volunteer'

        patched = client.patch(f"/reports/{report['id']}", json={'status': 'Verified'}).json()
        assert patched['status'] == 'Verified'

        org = client.post('/auth/org', json={}).json()
        assert org['name'] == 'Alex Morgan'
        assert org['place'] == 'Dordrecht'
        assert org['help'] == 'survey'
        assert org['org'] == 'South Holland'
        assert org['type'] == 'municipality'
        assert org['role'] == 'organisation'

        projects = client.get('/projects').json()
        assert projects[0]['id'] == 'dordrecht-east'
        assert projects[0]['label'] == 'Scenario 04'
        pid = projects[0]['id']

        scenario = client.post(f'/projects/{pid}/scenarios', json={
            'comparison': 'proposed',
            'name': 'Scenario 04',
            'inputs': {'year': 2030, 'power': 40, 'water': 12, 'land': 8, 'cooling': 3, 'buffer': 2},
            'results': {'temp': 1.4, 'habitat': -6, 'stress': 0.22, 'price': 18},
        }).json()
        assert scenario['comparison'] == 'proposed'
        assert scenario['inputs']['power'] == 40

        draft = client.post('/response-drafts', json={
            'site': 'biesbosch-reed',
            'type': 'survey-team',
        }).json()
        assert draft['site'] == 'biesbosch-reed'

        bad = client.post('/response-drafts', json={'site': '0', 'type': 'x'})
        assert bad.status_code == 404

        feed = client.get('/activity').json()
        kinds = {e['kind'] for e in feed}
        assert 'join' in kinds
        assert 'report' in kinds
        assert 'partner' in kinds
        assert 'funding' in kinds

        me = client.get('/users/me', headers=headers).json()
        assert me['id'] == people['id']
        print('ok', stats['hectares'], 'ha', stats['people'], 'people', len(feed), 'events')


if __name__ == '__main__':
    run()
