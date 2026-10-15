import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class Stage11DesignSystemTests(unittest.TestCase):
    def text(self,path):
        return (ROOT/path).read_text(encoding="utf-8")

    def test_design_system_and_workflow_navigation_exist(self):
        html=self.text("engineering/local_app/ui/index.html")
        self.assertIn('id="ui-mode-toggle"',html)
        for anchor in ["#files","#tz-panel","#evidence-panel","#domain-panel","#real-case-panel","#final-audit-panel"]:
            self.assertIn(anchor,html)
        self.assertIn("VALIDATION FIRST",html)

    def test_status_tokens_and_accessibility_rules_exist(self):
        css=self.text("engineering/local_app/ui/styles.css")
        for token in ["--pass:","--warn:","--uncertain:","--block:","--focus:"]:
            self.assertIn(token,css)
        self.assertIn(":focus-visible",css)
        self.assertIn("prefers-reduced-motion",css)
        self.assertIn('body[data-ui-mode="normal"] #advanced-domain-packet-form',css)

    def test_status_semantics_preserve_textual_decisions(self):
        js=self.text("engineering/local_app/ui/app.js")
        self.assertIn("function toneClass",js)
        self.assertIn("NOT ACCEPTED",js)
        self.assertIn("UNCERTAINTY",js)
        self.assertIn("BLOCK",js)
        self.assertIn("domainPanel.id='domain-panel'",js)

    def test_design_document_exists(self):
        doc=self.text("docs/design/ENGINEER_OS_DESIGN_SYSTEM.md")
        self.assertIn("Color is never the only carrier of meaning",doc)
        self.assertIn("Normal mode",doc)
        self.assertIn("Advanced mode",doc)

if __name__=="__main__":
    unittest.main()
