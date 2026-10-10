import unittest
from engineering.document_intelligence.stage13_acceptance import (
    MODULE_REQUIRED, DOCUMENT_REQUIRED, audit
)


class Stage13AcceptanceTests(unittest.TestCase):
    def test_module_can_pass_without_document_pass(self):
        result=audit(dict.fromkeys(MODULE_REQUIRED,'PASS'),{})
        self.assertEqual(result['module']['status'],'ACCEPTED')
        self.assertEqual(result['document']['status'],'BLOCK')
        self.assertEqual(result['overall_status'],'BLOCK')

    def test_missing_checks_never_accept_module(self):
        result=audit({'pdf_ingestion':'PASS'}, {})
        self.assertEqual(result['module']['status'],'BLOCK')
        self.assertIn('docx_ingestion',result['module']['missing'])
        self.assertEqual(result['module']['results']['docx_ingestion'],'NOT_RUN')

    def test_warning_is_not_pass(self):
        module=dict.fromkeys(MODULE_REQUIRED,'PASS')
        module['table_source_mapping']='UNCERTAINTY'
        result=audit(module,dict.fromkeys(DOCUMENT_REQUIRED,'PASS'))
        self.assertEqual(result['module']['status'],'BLOCK')
        self.assertEqual(result['document']['status'],'ACCEPTED')
        self.assertEqual(result['overall_status'],'BLOCK')


if __name__=='__main__':
    unittest.main()
