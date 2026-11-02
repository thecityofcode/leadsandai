import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import server

class WorkflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        server.DB = Path(cls.tmp.name) / 'test.sqlite'
        cls.http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.url = f'http://127.0.0.1:{cls.http.server_port}'
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.tmp.cleanup()

    def request(self, path, data=None, method=None):
        with urlopen(Request(self.url+path, data=json.dumps(data).encode() if data is not None else None,
                             method=method, headers={'Content-Type':'application/json'})) as r:
            return r.read()

    def test_lead_to_preview_and_meeting(self):
        lead = json.loads(self.request('/api/leads', {'company':'Test <Studio>', 'email':'test@example.com'}, 'POST'))
        lead.update(requirements='A shop & booking site', plan='Ecommerce Website', meeting='2027-01-05T10:00', preview=True)
        self.request('/api/leads/'+str(lead['id']), lead, 'PUT')
        saved = json.loads(self.request('/api/leads'))
        self.assertEqual(saved[0]['plan'], 'Ecommerce Website')
        self.assertEqual(saved[0]['meeting'], '2027-01-05T10:00')
        preview = self.request('/preview/'+str(lead['id'])).decode()
        self.assertIn('Test &lt;Studio&gt;', preview)
        self.assertIn('A shop &amp; booking site', preview)
        self.assertIn('Your growth workspace', self.request('/').decode())

    def test_reject_blank_business(self):
        with self.assertRaises(HTTPError) as error:
            self.request('/api/leads', {'company':' '}, 'POST')
        self.assertEqual(error.exception.code, 400)

    def test_missing_lead(self):
        with self.assertRaises(HTTPError) as error:
            self.request('/api/leads/999999', {'company':'Missing'}, 'PUT')
        self.assertEqual(error.exception.code, 404)
