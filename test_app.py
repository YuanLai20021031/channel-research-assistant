import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app import create_app

BRIEF = {'product': 'Task management for teams of 1-20', 'audience': 'UK small business owners', 'market': 'United Kingdom', 'mode': 'sample'}


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        base = Path(__file__).parent / 'instance'
        base.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=base)
        self.path = Path(self.temp.name) / 'test.db'
        self.client = create_app(self.path).test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_saved_result_survives_app_restart(self):
        response = self.client.post('/api/research', json=BRIEF)
        self.assertEqual(response.status_code, 201)
        report = response.get_json()
        self.assertEqual(len(report['channels']), 3)
        reopened = create_app(self.path).test_client().get('/api/reports').get_json()
        self.assertEqual(reopened[0]['id'], report['id'])
        self.assertIn(BRIEF['product'], report['draft'])

    def test_changed_market_does_not_reuse_uk_recommendations(self):
        response = self.client.post('/api/research', json={**BRIEF, 'market': 'Japan'})
        self.assertEqual(response.get_json()['channels'], [])
        self.assertTrue(response.get_json()['next_step'])

    def test_missing_and_wrong_type_inputs(self):
        for body in ({}, [], {**BRIEF, 'product': ' '}, {**BRIEF, 'market': 42}):
            self.assertEqual(self.client.post('/api/research', json=body).status_code, 400)

    def test_missing_key_reports_failure_without_fake_results(self):
        with patch.dict('os.environ', {'TAVILY_API_KEY': ''}):
            r = self.client.post('/api/research', json={**BRIEF, 'mode': 'live'})
        self.assertEqual(r.status_code, 502)
        self.assertIn('not configured', r.get_json()['error'])
        self.assertEqual(self.client.get('/api/reports').get_json(), [])

    def test_live_candidates_are_limited_and_deduplicated(self):
        from app import search_channels
        import io, json
        data = {'results': [{'title': str(i), 'url': f'https://channel{i//2}.example/contact', 'content': 'A community newsletter accepting editorial contributions.'} for i in range(10)]}
        with patch.dict('os.environ', {'TAVILY_API_KEY': 'test'}), patch('app.urlopen', return_value=io.BytesIO(json.dumps(data).encode())):
            candidates = search_channels(BRIEF)
        self.assertEqual(len(candidates), 3)
        self.assertEqual(len({x['url'] for x in candidates}), 3)


if __name__ == '__main__':
    unittest.main()
