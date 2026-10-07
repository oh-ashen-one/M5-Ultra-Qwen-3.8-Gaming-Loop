from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.source_artifact import complete_csharp
from loop_controller.core import Halt

class SourceArtifactTests(unittest.TestCase):
    def response(self,content,finish='stop',**extra):
        return dict(choices=[dict(finish_reason=finish,message=dict(content=content,**extra))])
    def test_preserves_only_completed_public_source(self):
        data=self.response('```csharp\nclass Original {}\n```',reasoning_content='PRIVATE')
        self.assertEqual(complete_csharp(data),'class Original {}\n')
        for response in [self.response('class Original {}','length'),self.response(None),
                self.response('class Original {}',tool_calls=[{}]),self.response('<think>private</think>class X{}'),
                self.response('```csharp\nclass A{}\n```\n```csharp\nclass B{}\n```')]:
            with self.assertRaises(Halt):complete_csharp(response)
    def test_size_boundary_rejects_without_truncation(self):
        with self.assertRaises(Halt):complete_csharp(self.response('class A{}'),max_bytes=3)
        with self.assertRaises(Halt):complete_csharp(self.response('class A\n{\n}'),max_lines=2)

if __name__=='__main__':unittest.main()
