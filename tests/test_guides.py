import json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class GuideContent(unittest.TestCase):
    def test_complete_guides_with_local_licensed_photos(self):
        guides=json.loads((ROOT/'guides.json').read_text(encoding='utf-8'))
        self.assertEqual(len(guides),28)
        for key,g in guides.items():
            with self.subTest(guide=key):
                self.assertGreaterEqual(len(g['photos']),2)
                self.assertGreaterEqual(len({p['source'] for p in g['photos']}),2)
                self.assertGreater(len(' '.join(g['history'])),350)
                self.assertEqual(len(g['stops']),3)
                self.assertGreaterEqual(len(g['tips']),3)
                for p in g['photos']:
                    self.assertTrue(p['src'].startswith('/guide-photos/'))
                    self.assertTrue((ROOT/'static'/p['src'].lstrip('/')).is_file())
                    self.assertTrue(p['author'])
                    self.assertTrue(p['license'])
                    self.assertTrue(p['license_url'].startswith('https://'))
                self.assertGreaterEqual(len(g['sources']),2)

if __name__=='__main__':unittest.main()
