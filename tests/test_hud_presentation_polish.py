import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from resume_hud_presentation_polish import inspect_polish, exact_content, compact


class HudPresentationPolishTests(unittest.TestCase):
    def test_transport_decode_requires_same_exact_scoped_source(self):
        import json
        source = 'var mat = Shader.Find("Unlit/Color");\nmat.color = new Color(.06f,.07f,.085f,1f);'
        accept = lambda value, _: compact(value) == compact(source)
        encoded = json.dumps(source)[1:-1]
        self.assertEqual(exact_content(encoded, accept, ''), source)
        self.assertEqual(exact_content(source, accept, ''), source)
        with self.assertRaises(ValueError): exact_content(encoded + 'Destroy(player);', accept, '')
        with self.assertRaises(ValueError): exact_content('System.IO.File.Delete("x");', accept, '')

    def row(self):
        def panel(name, text):
            return dict(name=name, text=text, cardShader='Unlit/Color', cardColor=[.06, .07, .085, 1],
                textRect=[.1,.82,.3,.90], captureTextRect=[.1,.82,.3,.90])
        return dict(time=2, health=44, pursuit=1, relay={'complete': True}, routeChapter={'hudPanels': [
            panel('HudStatus', 'HEALTH 44\nWANTED 1 / 3'), panel('MissionBoard', 'RELAY COMPLETE\nR reset')]})

    def test_real_state_and_complete_reset_hint_are_required(self):
        row = self.row(); self.assertTrue(inspect_polish([row])['passed'])
        row['health'] = 44.0
        self.assertTrue(inspect_polish([row])['passed'])
        fractional = copy.deepcopy(row); fractional['health'] = 44.5
        self.assertFalse(inspect_polish([fractional])['passed'])
        nonfinite = copy.deepcopy(row); nonfinite['health'] = float('nan')
        self.assertFalse(inspect_polish([nonfinite])['passed'])
        for kind in ('health', 'wanted', 'hint'):
            value = copy.deepcopy(row)
            if kind == 'health': value['health'] = 40
            if kind == 'wanted': value['pursuit'] = 2
            if kind == 'hint': value['routeChapter']['hudPanels'][1]['text'] = 'RELAY COMPLETE'
            with self.subTest(kind=kind): self.assertFalse(inspect_polish([value])['passed'])

    def test_lit_transparent_or_tiny_status_is_red(self):
        for kind in ('lit', 'transparent', 'tiny', 'missing'):
            value = self.row(); status = value['routeChapter']['hudPanels'][0]
            if kind == 'lit': status['cardShader'] = 'Standard'
            if kind == 'transparent': status['cardColor'][3] = .7
            if kind == 'tiny': status['captureTextRect'][1] = .89
            if kind == 'missing': del status['cardColor']
            with self.subTest(kind=kind): self.assertFalse(inspect_polish([value])['passed'])


if __name__ == '__main__': unittest.main()
