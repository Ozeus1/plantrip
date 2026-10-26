import json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class GuideContent(unittest.TestCase):
    def test_complete_guides_with_local_licensed_photos(self):
        guides=json.loads((ROOT/'guides.json').read_text(encoding='utf-8'))
        self.assertEqual(len(guides),51)
        for key,g in guides.items():
            with self.subTest(guide=key):
                if key in ('toscana-rural','champagne-reims'):
                    self.assertEqual(g['photos'],[])  # No unlicensed or unrelated placeholder photos.
                    self.assertEqual(len(g['stops']),3)
                    self.assertGreaterEqual(len(g['history']),2)
                    continue
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

    def test_all_rome_stops_have_distinct_photos_and_four_day_navigation(self):
        guides=json.loads((ROOT/'guides.json').read_text(encoding='utf-8'))
        rome=[g for g in guides.values() if g.get('rome_day')]
        self.assertEqual(len(rome),19)
        self.assertEqual([len([g for g in rome if g['rome_day']==d]) for d in range(1,5)],[6,6,3,4])
        for g in rome:
            self.assertGreaterEqual(len({p['source'] for p in g['photos']}),2)
            self.assertEqual(len(g['route_summary']),4)
            self.assertTrue(g['food'])
            self.assertGreater(len(g['booking']),80)
        self.assertGreaterEqual(len(guides['vaticano-museus']['photos']),4)
        self.assertGreaterEqual(len(guides['roma-popolo']['photos']),4)

if __name__=='__main__':unittest.main()
