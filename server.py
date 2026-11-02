import json, sqlite3, os, html
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent
DB = Path(os.environ.get('CRM_DB_PATH', str(ROOT / 'data/crm.sqlite')))
DB.parent.mkdir(exist_ok=True)

def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute('CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY, data TEXT NOT NULL)')
    return db

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'public'), **kwargs)

    def respond(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/leads':
            with connect() as db:
                self.respond([dict(json.loads(r['data']), id=r['id']) for r in db.execute('SELECT * FROM leads ORDER BY id DESC')])
        elif path.startswith('/preview/'):
            try:
                with connect() as db:
                    row = db.execute('SELECT * FROM leads WHERE id=?', (int(path.split('/')[-1]),)).fetchone()
                if not row: return self.send_error(404)
                lead = json.loads(row['data'])
                name = html.escape(lead['company'])
                description = html.escape(lead.get('requirements') or 'Thoughtful service. Exceptional results. Discover what we can do for you.')
                body = f'''<!doctype html><html><meta name="viewport" content="width=device-width, initial-scale=1"><title>{name}</title><style>body{{margin:0;background:#f4f1e9;color:#18392e;font:20px system-ui}}nav,main,footer{{padding:35px 8%}}nav{{border-bottom:1px solid #ccd2c8}}main{{padding-top:110px;max-width:900px;min-height:55vh}}h1{{font-size:clamp(48px,8vw,100px);line-height:1.05;letter-spacing:-5px}}p{{line-height:1.8;max-width:640px}}a{{display:inline-block;background:#18392e;color:white;padding:18px 30px;border-radius:40px;text-decoration:none}}small{{letter-spacing:3px}}</style><nav>{name}</nav><main><small>WELCOME TO {name.upper()}</small><h1>A better experience.<br>Built around you.</h1><p>{description}</p><a href="mailto:{html.escape(lead.get('email',''), quote=True)}">Get in touch ↗</a></main><footer>© {name} · Website concept preview</footer></html>'''.encode()
                self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.end_headers(); self.wfile.write(body)
            except ValueError: self.send_error(404)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path != '/api/leads': return self.send_error(404)
        self.save()

    def do_PUT(self):
        if not self.path.startswith('/api/leads/'): return self.send_error(404)
        self.save()

    def save(self):
        try:
            size = int(self.headers.get('Content-Length', 0))
            if size > 100000: return self.respond({'error':'Request too large'},413)
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict) or not str(data.get('company','')).strip():
                return self.respond({'error':'Company is required'},400)
            data.pop('id',None)
            with connect() as db:
                if self.command == 'PUT':
                    id = int(self.path.split('/')[-1])
                    result = db.execute('UPDATE leads SET data=? WHERE id=?',(json.dumps(data),id))
                    if not result.rowcount: return self.respond({'error':'Lead not found'},404)
                else:
                    id = db.execute('INSERT INTO leads(data) VALUES (?)',(json.dumps(data),)).lastrowid
            self.respond(dict(data,id=id))
        except (ValueError, TypeError): self.respond({'error':'Invalid request'},400)

if __name__ == '__main__':
    connect().close()
    ThreadingHTTPServer(('0.0.0.0',int(os.environ.get('PORT','3000'))),Handler).serve_forever()
