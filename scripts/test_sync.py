import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError
from sync import sync_one, validate

SPEC = {'path': 'Apple AI.lsr', 'url': 'https://raw.githubusercontent.com/example/rules/main/Apple.lsr', 'min_rules': 3,
        'required_rules': ['DOMAIN,apple-relay.apple.com']}
GOOD = b'DOMAIN,apple-relay.apple.com\nDOMAIN,apple-relay.cloudflare.com\nDOMAIN,apple-relay.fastly-edge.com\n'

class RetentionTests(unittest.TestCase):
    def test_failures_preserve_exact_bytes(self):
        for result in [b'', b' \n# comments only\n', b'<html>Error</html>', b'404: Not Found', b'\xff',
                       b'DOMAIN,example.com\n', GOOD + b'MATCH,DIRECT\n', GOOD.replace(b'fastly-edge.com', b'bad..com')]:
            with self.subTest(result=result), tempfile.TemporaryDirectory() as d:
                p = Path(d) / SPEC['path']; p.write_bytes(GOOD)
                self.assertEqual(sync_one(Path(d), SPEC, lambda _: result)['state'], 'retained')
                self.assertEqual(p.read_bytes(), GOOD)

    def test_404_deleted_timeout_preserve(self):
        for error in [HTTPError(SPEC['url'], 404, 'deleted', None, None), TimeoutError('timeout'), OSError('network down')]:
            with self.subTest(error=error), tempfile.TemporaryDirectory() as d:
                p = Path(d) / SPEC['path']; p.write_bytes(GOOD)
                def fetch(_): raise error
                self.assertEqual(sync_one(Path(d), SPEC, fetch)['state'], 'retained')
                self.assertEqual(p.read_bytes(), GOOD)

    def test_valid_update_and_no_change(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.assertEqual(sync_one(root, SPEC, lambda _: GOOD)['state'], 'updated')
            self.assertEqual(sync_one(root, SPEC, lambda _: GOOD)['state'], 'unchanged')
            new = GOOD + b'DOMAIN,gspe1-ssl.ls.apple.com\n'
            self.assertEqual(sync_one(root, SPEC, lambda _: new)['state'], 'updated')
            self.assertEqual((root / SPEC['path']).read_bytes(), new)

    def test_truncation_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); old = GOOD + b''.join(f'DOMAIN,d{i}.example.com\n'.encode() for i in range(20))
            (root / SPEC['path']).write_bytes(old)
            self.assertEqual(sync_one(root, SPEC, lambda _: GOOD)['state'], 'retained')
            self.assertEqual((root / SPEC['path']).read_bytes(), old)

    def test_missing_file_not_created_on_failure(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(sync_one(Path(d), SPEC, lambda _: b'')['state'], 'unavailable')
            self.assertFalse((Path(d) / SPEC['path']).exists())

if __name__ == '__main__': unittest.main()
