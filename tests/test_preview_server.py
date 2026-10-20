"""Exercise preview URL boundaries with synthetic files, never local mail settings."""
import http.client
import importlib.util
from pathlib import Path
import tempfile
import threading
import unittest


class PreviewPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(__file__).resolve().parents[1] / 'website' / 'server.py'
        spec = importlib.util.spec_from_file_location('lan_preview_test', source)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = (Path(cls.temp.name) / 'site').resolve()
        cls.root.mkdir()
        cls.module.ROOT = cls.root
        cls.module.CONFIG = cls.root / 'website' / '.mail-config.json'
        for name in ('index.html', 'ru/index.html', 'website.js', 'website.i18n.js',
                     'website.css', 'lan-ehitus.svg', 'images/photo.jpg',
                     'images/photo name.jpg', 'fonts/font.woff2', 'service-example.jpg',
                     'preview-room.jpg', 'website/server.py', 'NOTES.md',
                     'website/.mail-config.json', 'images/.hidden'):
            target = cls.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('synthetic fixture: ' + name)
        outside = Path(cls.temp.name) / 'outside.txt'
        outside.write_text('synthetic outside fixture')
        (cls.root / 'images' / 'outside.jpg').symlink_to(outside)
        cls.server = cls.module.ThreadingHTTPServer(('127.0.0.1', 0), cls.module.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.temp.cleanup()

    def get(self, path):
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=5)
        try:
            connection.request('GET', path)
            response = connection.getresponse()
            return response.status, response.read()
        finally:
            connection.close()

    def test_public_pages_and_assets(self):
        for path in ('/', '/ru/', '/ru/index.html', '/website.js?v=1', '/website.i18n.js',
                     '/website.css', '/lan-ehitus.svg', '/images/photo.jpg',
                     '/images/photo%20name.jpg', '/fonts/font.woff2',
                     '/service-example.jpg', '/preview-room.jpg'):
            with self.subTest(path=path):
                self.assertEqual(self.get(path)[0], 200)

    def test_private_files_and_encoded_traversal(self):
        for path in ('/website/server.py', '/NOTES.md', '/website/.mail-config.json',
                     '/images/../website/server.py', '/images/%2e%2e/website/server.py',
                     '/fonts/%2E%2E/website/server.py', '/images/%2e%2e/NOTES.md',
                     '/images/%2e%2e%2fwebsite%2fserver.py',
                     '/images/%252e%252e/website/server.py',
                     '/images/./photo.jpg', '/images/.hidden', '/images/%2ehidden',
                     '/images/%00photo.jpg', '/images/outside.jpg'):
            with self.subTest(path=path):
                self.assertEqual(self.get(path)[0], 404)


if __name__ == '__main__':
    unittest.main()
