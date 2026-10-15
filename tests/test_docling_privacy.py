import builtins
import os
import sys
import unittest
from unittest.mock import patch

from engineering.document_intelligence import DoclingDocumentParser, DocumentParseError


class DoclingPrivacyTests(unittest.TestCase):
    def test_telemetry_is_disabled_before_optional_runtime_import(self):
        original = builtins.__import__
        for initial in (None, '0'):
            with self.subTest(initial=initial), patch.dict(os.environ, {}, clear=True), patch.dict(sys.modules):
                sys.modules.pop('onnxruntime', None)
                if initial is not None:
                    os.environ['ORT_DISABLE_TELEMETRY'] = initial

                def inspect_import(name, *args, **kwargs):
                    if name == 'onnxruntime' or name.startswith('docling.'):
                        self.assertEqual(os.environ.get('ORT_DISABLE_TELEMETRY'), '1')
                        raise ImportError('Optional dependencies absent in unit test')
                    return original(name, *args, **kwargs)

                with patch('builtins.__import__', side_effect=inspect_import):
                    with self.assertRaises(DocumentParseError):
                        DoclingDocumentParser()._converter()

    def test_runtime_loaded_without_process_opt_out_blocks_conversion(self):
        with patch.dict(os.environ, {}, clear=True), patch.dict(sys.modules, {'onnxruntime': object()}):
            with self.assertRaisesRegex(DocumentParseError, 'telemetry.*restart'):
                DoclingDocumentParser()._converter()

    def test_preconfigured_runtime_disables_platform_events_before_docling(self):
        from types import SimpleNamespace
        disabled = []
        runtime = SimpleNamespace(disable_telemetry_events=lambda: disabled.append(True))
        original = builtins.__import__

        def inspect_import(name, *args, **kwargs):
            if name.startswith('docling.'):
                self.assertEqual(disabled, [True])
                raise ImportError('No Docling in minimal environment')
            return original(name, *args, **kwargs)

        with patch.dict(os.environ, {'ORT_DISABLE_TELEMETRY': '1'}), \
                patch.dict(sys.modules, {'onnxruntime': runtime}), \
                patch('builtins.__import__', side_effect=inspect_import):
            with self.assertRaises(DocumentParseError):
                DoclingDocumentParser()._converter()


if __name__ == '__main__':
    unittest.main()
