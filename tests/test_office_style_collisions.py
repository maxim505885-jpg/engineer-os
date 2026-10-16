import io,unittest,zipfile
from engineering.local_app.office import read
from tests.test_office_documents import docx,W

def with_styles(styles):
    out=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(docx('Source text'))) as src,zipfile.ZipFile(out,'w') as dst:
        for name in src.namelist():dst.writestr(name,src.read(name))
        dst.writestr('word/styles.xml','<w:styles xmlns:w="'+W+'">'+styles+'</w:styles>')
    return out.getvalue()

class OfficeStyleCollisionTests(unittest.TestCase):
    def test_different_ids_same_type_and_name_are_flagged_without_text_rewrite(self):
        data=with_styles('<w:style w:type="paragraph" w:styleId="a"><w:name w:val="Normal"/></w:style><w:style w:type="paragraph" w:styleId="Normal0"><w:name w:val="Normal"/></w:style>')
        units,limits=read(data,'docx')
        self.assertIn('DUPLICATE_STYLE_NAMES_LAYOUT_UNVERIFIED',limits)
        self.assertEqual(units[0]['text'],'Source text')
    def test_distinct_names_or_style_types_do_not_trigger_collision(self):
        for kind,name in [('paragraph','Other'),('character','Normal')]:
            data=with_styles('<w:style w:type="paragraph" w:styleId="a"><w:name w:val="Normal"/></w:style><w:style w:type="'+kind+'" w:styleId="b"><w:name w:val="'+name+'"/></w:style>')
            self.assertNotIn('DUPLICATE_STYLE_NAMES_LAYOUT_UNVERIFIED',read(data,'docx')[1])
if __name__=='__main__':unittest.main()
