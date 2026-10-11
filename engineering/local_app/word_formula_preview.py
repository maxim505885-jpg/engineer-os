"""Passive, bounded LibreOffice OMML preview; source layout/math never verified.

Ordinals are zero-based, document-order ``oMath`` occurrences within the named
part. Formula identity matches ET.tostring(source), including any sibling tail.
The separately hashed isolated render fragment omits that tail.
Only a sanitized single-formula scaffold, never the uploaded package, is opened.
"""
import copy
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import zipfile
from xml.etree import ElementTree as ET

# Direct script invocation is used for the isolated raster child.
if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engineering.local_app.office import M, W, Package, OfficeError

MAX_SOURCE_BYTES = 256 * 1024 * 1024
MAX_PART_XML = 16 * 1024 * 1024
MAX_FORMULA_XML = 512 * 1024
MAX_NODES = 300000
MAX_FORMULA_NODES = 10000
MAX_SCAFFOLD = 8 * 1024 * 1024
MAX_PDF_BYTES = 16 * 1024 * 1024
MAX_PNG_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 8_000_000
MAX_DIMENSION = 4096
TIMEOUT = 60
DPI = 120
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
OFFICE_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/'

MATH_TAGS = set('oMath oMathPara oMathParaPr acc accPr bar barPr borderBox borderBoxPr box boxPr brk chr ctrlPr d dPr deg degHide den diff dSub dSup e eqArr eqArrPr f fPr func funcPr fName groupChr groupChrPr grow hideBot hideLeft hideRight hideTop interSp intraSp jc lim limLoc limLow limLowPr limUpp limUppPr lit m mPr maxDist mc mcPr mcs mr nary naryPr noBreak nor num objDist opEmu phantom phantomPr plcHide pos r rPr rad radPr sPre sPrePr sSub sSubPr sSubSup sSubSupPr sSup sSupPr scr sepChr show shP smallFrac spacing strikeBLTR strikeH strikeTLBR strikeV sty sub subHide sup supHide t transp type vertJc wrapIndent wrapRight zeroAsc zeroDesc zeroWid aln alnScr argPr argSz begChr count cGp cGpRule cSp endChr rSp rSpRule baseJc mathPr mathFont brkBin brkBinSub defJc dispDef interSp intraSp lMargin rMargin preSp postSp intLim naryLim'.split())
WORD_TAGS = set('pPr rPr pStyle rStyle rFonts b bCs i iCs caps smallCaps strike dstrike outline shadow emboss imprint noProof snapToGrid vanish webHidden color spacing w kern position sz szCs highlight u effect bdr shd fitText vertAlign rtl cs em lang eastAsianLayout specVanish oMath jc keepNext keepLines pageBreakBefore widowControl numPr ilvl numId suppressLineNumbers pBdr tabs tab suppressAutoHyphens kinsoku wordWrap overflowPunct topLinePunct autoSpaceDE autoSpaceDN bidi adjustRightInd contextualSpacing mirrorIndents suppressOverlap ind textAlignment textDirection outlineLvl divId cnfStyle styles docDefaults rPrDefault pPrDefault style name aliases basedOn next link autoRedefine hidden uiPriority semiHidden unhideWhenUsed qFormat locked personal personalCompose personalReply rsid fontTable fonts font altName panose1 charset family notTrueType pitch sig settings defaultTabStop characterSpacingControl'.split())
THEME_TAGS = set('theme themeElements clrScheme dk1 lt1 dk2 lt2 accent1 accent2 accent3 accent4 accent5 accent6 hlink folHlink sysClr srgbClr fontScheme majorFont minorFont latin ea cs font fmtScheme fillStyleLst solidFill gradFill gsLst gs schemeClr tint shade satMod lumMod lumOff alpha lin path fillToRect tileRect lnStyleLst ln prstDash bevel miter headEnd tailEnd effectStyleLst effectStyle effectLst outerShdw innerShdw prstShdw reflection softEdge glow blur bgFillStyleLst objectDefaults spDef lnDef txDef spPr bodyPr lstStyle style extraClrSchemeLst extraClrScheme clrMap custClrLst custClr'.split())


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _passive(element, strict=False):
    """Allow typography/schema trees only; no foreign tags or relationship attrs."""
    def allowed(node):
        return (node.tag.startswith(M) and node.tag[len(M):] in MATH_TAGS or
                node.tag.startswith(W) and node.tag[len(W):] in WORD_TAGS or
                node.tag.startswith(A) and node.tag[len(A):] in THEME_TAGS)
    if not allowed(element):
        if strict:
            raise OfficeError('Formula contains unsupported/active XML')
        return None
    result = ET.Element(element.tag)
    for key, value in element.attrib.items():
        if (key.startswith('{') and not key.startswith((W, M, A, '{http://www.w3.org/XML/1998/namespace}'))) or key.lower().rsplit('}', 1)[-1] in {'href', 'src', 'target', 'targetmode'}:
            if strict:
                raise OfficeError('Formula contains relationship/active attribute')
            continue
        result.set(key, value)
    result.text = element.text
    for child in element:
        passive = _passive(child, strict)
        if passive is not None:
            result.append(passive)
    # Tails can belong to unrelated sibling text and are always omitted.
    return result


def _scaffold(data, part, ordinal):
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_SOURCE_BYTES:
        raise OfficeError('Formula source byte limit/type')
    if (not isinstance(part, str) or len(part) > 1024 or not part.startswith('word/') or not part.endswith('.xml') or '\\' in part or any(ord(c) < 32 for c in part) or any(segment in {'', '.', '..'} for segment in part.split('/'))):
        raise OfficeError('Invalid formula part')
    if type(ordinal) is not int or not 0 <= ordinal < MAX_NODES:
        raise OfficeError('Invalid formula ordinal')
    package = None
    try:
        package = Package(data)
        def xml(name):
            if package.zip.getinfo(name).file_size > MAX_PART_XML:
                raise OfficeError('Formula part XML byte limit')
            root = package.xml(name)
            if sum(1 for _ in root.iter()) > MAX_NODES:
                raise OfficeError('Formula XML node limit')
            return root
        root = xml(part)
        if root.tag not in {W+'document', W+'hdr', W+'ftr', W+'footnotes', W+'endnotes'}:
            raise OfficeError('Invalid Word formula part root')
        formula = next((f for i, f in enumerate(root.iter(M+'oMath')) if i == ordinal), None)
        if formula is None:
            raise OfficeError('Formula ordinal unavailable')
        fragment = copy.deepcopy(formula); fragment.tail = None
        identity = ET.tostring(formula)
        render_identity = ET.tostring(fragment, encoding='utf-8')
        if len(identity) > MAX_FORMULA_XML or sum(1 for _ in fragment.iter()) > MAX_FORMULA_NODES:
            raise OfficeError('Formula XML limit')
        _passive(fragment, strict=True)  # Reject rather than alter selected syntax.
        parents = {child: parent for parent in root.iter() for child in parent}
        paragraph = None; math_para = None; ancestor = formula
        while ancestor in parents:
            ancestor = parents[ancestor]
            if ancestor.tag == M+'oMathPara' and math_para is None:
                math_para = ancestor
            if ancestor.tag == W+'p':
                paragraph = ancestor; break
        document = ET.Element(W+'document'); body = ET.SubElement(document, W+'body'); p = ET.SubElement(body, W+'p')
        if paragraph is not None:
            props = paragraph.find(W+'pPr')
            if props is not None:
                p.append(_passive(props))
        if math_para is not None:
            container = ET.SubElement(p, M+'oMathPara')
            props = math_para.find(M+'oMathParaPr')
            if props is not None:
                container.append(_passive(props, strict=True))
        else:
            container = p
        container.append(fragment)
        section = ET.SubElement(body, W+'sectPr')
        ET.SubElement(section, W+'pgSz', {W+'w': '12240', W+'h': '15840'})
        ET.SubElement(section, W+'pgMar', {W+'top': '720', W+'bottom': '720', W+'left': '720', W+'right': '720'})
        parts = {'word/document.xml': ET.tostring(document, encoding='utf-8', xml_declaration=True)}
        support = []
        for name in ('word/styles.xml', 'word/settings.xml', 'word/fontTable.xml', 'word/theme/theme1.xml'):
            if name in package.names:
                source = xml(name)
                passive = _passive(source)
                if passive is not None:
                    parts[name] = ET.tostring(passive, encoding='utf-8', xml_declaration=True)
                    support.append(dict(part=name, source_xml_sha256=_sha(ET.tostring(source, encoding='utf-8')), sanitized_xml_sha256=_sha(parts[name])))
        fonts = sorted({v for content in parts.values() for node in ET.fromstring(content).iter() for k, v in node.attrib.items() if (node.tag in {W+'rFonts', M+'mathFont'} and k.rsplit('}', 1)[-1] in {'ascii', 'hAnsi', 'eastAsia', 'cs', 'val'}) or (node.tag in {A+'latin', A+'ea', A+'cs', A+'font'} and k == 'typeface')})
        relations = ET.Element('{'+REL+'}Relationships')
        for index, name in enumerate(parts):
            if name == 'word/document.xml':
                continue
            kind = {'word/styles.xml': 'styles', 'word/settings.xml': 'settings', 'word/fontTable.xml': 'fontTable', 'word/theme/theme1.xml': 'theme'}[name]
            ET.SubElement(relations, '{'+REL+'}Relationship', Id='support'+str(index), Type=OFFICE_REL+kind, Target=name[len('word/'):])
        parts['word/_rels/document.xml.rels'] = ET.tostring(relations, encoding='utf-8').replace(b'ns0:', b'').replace(b'xmlns:ns0=', b'xmlns=')
        parts['_rels/.rels'] = f'<Relationships xmlns="{REL}"><Relationship Id="office" Type="{OFFICE_REL}officeDocument" Target="word/document.xml"/></Relationships>'.encode()
        types = ET.Element('{'+CT+'}Types')
        ET.SubElement(types, '{'+CT+'}Default', Extension='rels', ContentType='application/vnd.openxmlformats-package.relationships+xml')
        ET.SubElement(types, '{'+CT+'}Default', Extension='xml', ContentType='application/xml')
        for name in ['word/document.xml'] + [s['part'] for s in support]:
            suffix = {'word/document.xml': 'wordprocessingml.document.main', 'word/styles.xml': 'wordprocessingml.styles', 'word/settings.xml': 'wordprocessingml.settings', 'word/fontTable.xml': 'wordprocessingml.fontTable', 'word/theme/theme1.xml': 'theme'}[name]
            ET.SubElement(types, '{'+CT+'}Override', PartName='/'+name, ContentType='application/vnd.openxmlformats-officedocument.'+suffix+'+xml')
        parts['[Content_Types].xml'] = ET.tostring(types, encoding='utf-8').replace(b'ns0:', b'').replace(b'xmlns:ns0=', b'xmlns=')
        if sum(map(len, parts.values())) > MAX_SCAFFOLD:
            raise OfficeError('Formula scaffold byte limit')
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, content in parts.items():
                z.writestr(name, content)
        scaffold = stream.getvalue()
        return scaffold, dict(source_sha256=_sha(data), formula_sha256=_sha(identity), formula_serialization='ET_TOSTRING_SOURCE_INCLUDING_TAIL', isolated_render_fragment_sha256=_sha(render_identity), part=part, ordinal=ordinal, ordinal_base=0,
                              scaffold_sha256=_sha(scaffold), support_parts=support, support_parts_sanitized=True, support_parts_policy='TYPOGRAPHY_WHITELIST_RELATIONSHIP_ATTRIBUTES_AND_UNSUPPORTED_NODES_DISCARDED', embedded_source_fonts_retained=False,
                              fonts=dict(declared_families=fonts[:256], declared_inventory_truncated=len(fonts)>256, source_font_substitution_verified=False))
    except (KeyError, zipfile.BadZipFile, ET.ParseError, RecursionError, RuntimeError, OSError, ValueError) as error:
        if isinstance(error, OfficeError):
            raise
        raise OfficeError('Formula source unavailable/invalid XML package') from None
    finally:
        if package is not None:
            package.close()


def _converter():
    value = os.environ.get('ENGINEER_OS_DOC_CONVERTER') or shutil.which('soffice') or shutil.which('libreoffice')
    path = Path(value).resolve() if value else None
    return path if path and path.is_file() else None


def _run(command, root, timeout, log_name):
    if timeout <= 0:
        raise OfficeError('Formula preview timeout')
    if sys.platform == 'linux':
        command = [sys.executable, str(Path(__file__).with_name('doc_sandbox.py'))] + command
    elif sys.platform != 'win32':
        raise OfficeError('Controlled formula converter unavailable on platform')
    options = dict(start_new_session=True) if sys.platform != 'win32' else dict(creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    log_path = root/log_name
    with log_path.open('wb') as log:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, cwd=root, **options)
        deadline = time.monotonic()+timeout
        try:
            while True:
                if log_path.stat().st_size > MAX_PDF_BYTES:
                    raise OfficeError('Formula converter log byte limit')
                left = deadline-time.monotonic()
                if left <= 0:
                    raise OfficeError('Formula preview timeout')
                try:
                    code = process.wait(timeout=min(0.1, left))
                    break
                except subprocess.TimeoutExpired:
                    continue
        finally:
            # Also remove descendants left behind by a successful/failed launcher.
            if sys.platform == 'linux':
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            elif process.poll() is None:
                try:
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False)
                finally:
                    process.kill()
            if process.poll() is None:
                process.wait(timeout=5)
    if log_path.stat().st_size > MAX_PDF_BYTES:
        raise OfficeError('Formula converter log byte limit')
    if code != 0:
        # Keep failure provenance after the temporary profile/logs are removed.
        # Read only a bounded suffix; no command/env dump or source package data.
        with log_path.open('rb') as failed_log:
            failed_log.seek(max(0, log_path.stat().st_size-1200))
            diagnostic = failed_log.read(1200).decode('utf-8', errors='replace').strip()
        diagnostic = ''.join(c if c in '\n\t' or ord(c) >= 32 else '?' for c in diagnostic)
        raise OfficeError(f'Formula converter/rasterizer failed ({log_name}, exit {code}): {diagnostic}')
    return log_path.read_bytes()[:4096].decode('utf-8', errors='replace').strip()


def _raster_pdf(path):
    """Runs in an isolated child during production; bounds before allocating pixels."""
    import fitz
    if not 0 < path.stat().st_size <= MAX_PDF_BYTES:
        raise OfficeError('Formula PDF byte limit')
    with fitz.open(path) as pdf:
        if len(pdf) != 1:
            raise OfficeError('Formula preview requires a single derived page')
        page = pdf[0]; scale = DPI/72
        width = math.ceil(page.rect.width*scale); height = math.ceil(page.rect.height*scale)
        if not 0 < width <= MAX_DIMENSION or not 0 < height <= MAX_DIMENSION or width*height > MAX_PIXELS:
            raise OfficeError('Formula preview pixel limit')
        pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csRGB, alpha=False)
        from PIL import Image, ImageChops
        image = Image.frombytes('RGB', (pixmap.width, pixmap.height), pixmap.samples)
        bbox = ImageChops.difference(image, Image.new('RGB', image.size, 'white')).getbbox()
        if bbox is None:
            raise OfficeError('Formula preview has no visible rendered marks')
        crop = (max(0, bbox[0]-12), max(0, bbox[1]-12), min(pixmap.width, bbox[2]+12), min(pixmap.height, bbox[3]+12))
        image = image.crop(crop)
        buffer = io.BytesIO(); image.save(buffer, format='PNG'); png = buffer.getvalue()
        if not 0 < len(png) <= MAX_PNG_BYTES:
            raise OfficeError('Formula PNG byte limit')
        fonts = []
        for row in page.get_fonts()[:256]:
            name, extension, kind, buffer = pdf.extract_font(row[0])
            fonts.append(dict(pdf_family=row[3], pdf_font_name=name, kind=kind, extension=extension,
                              embedded_font_sha256=_sha(buffer) if buffer else None))
        return png, dict(width=image.width, height=image.height, full_derived_page_width=pixmap.width, full_derived_page_height=pixmap.height, derived_page_crop=list(crop), dpi=DPI, rasterizer='PyMuPDF', rasterizer_version=fitz.VersionBind, derived_pdf_fonts=fonts)


def render_formula(data: bytes, part: str, ordinal: int):
    """Return (PNG bytes, provenance dossier), or OfficeError (BLOCK, no preview)."""
    started = time.monotonic()
    scaffold, dossier = _scaffold(data, part, ordinal)
    executable = _converter()
    if executable is None:
        raise OfficeError('Local LibreOffice formula converter unavailable')
    if sys.platform not in {'linux', 'win32'}:
        raise OfficeError('Controlled formula converter unavailable on platform')
    def remaining():
        return TIMEOUT-(time.monotonic()-started)
    try:
        with tempfile.TemporaryDirectory(prefix='engineer-formula-') as temp:
            root = Path(temp); profile = root/'profile'; profile.mkdir(); out = root/'out'; out.mkdir()
            (profile/'registrymodifications.xcu').write_text('<?xml version="1.0"?><oor:items xmlns:oor="http://openoffice.org/2001/registry"><item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop></item><item oor:path="/org.openoffice.Office.Writer/Content/Update"><prop oor:name="Link" oor:op="fuse"><value>2</value></prop></item></oor:items>', encoding='utf-8')
            source = root/'formula.docx'; source.write_bytes(scaffold)
            version = _run([str(executable), '--version'], root, min(10, remaining()), 'version.log')
            command = [str(executable), '-env:UserInstallation='+profile.as_uri(), '--headless', '--nologo', '--nodefault', '--nofirststartwizard', '--norestore', '--convert-to', 'pdf:writer_pdf_Export', '--outdir', str(out), str(source)]
            _run(command, root, remaining(), 'conversion.log')
            pdf = out/'formula.pdf'
            if not pdf.is_file() or not 0 < pdf.stat().st_size <= MAX_PDF_BYTES:
                raise OfficeError('Formula conversion produced no bounded PDF')
            png_path = root/'preview.png'; metadata_path = root/'raster.json'
            _run([sys.executable, str(Path(__file__).resolve()), '--raster', str(pdf), str(png_path), str(metadata_path)], root, remaining(), 'raster.log')
            if not png_path.is_file() or not 0 < png_path.stat().st_size <= MAX_PNG_BYTES or not metadata_path.is_file() or metadata_path.stat().st_size > 65536:
                raise OfficeError('Formula rasterizer produced no bounded PNG')
            png = png_path.read_bytes(); raster = json.loads(metadata_path.read_text(encoding='utf-8'))
            dossier['fonts'].update(derived_pdf_fonts=raster.pop('derived_pdf_fonts'), source_font_substitution_verified=False)
            dossier.update(scope='DERIVED_UNVERIFIED', status='UNCERTAINTY', preview_sha256=_sha(png), pdf_sha256=_sha(pdf.read_bytes()),
                           converter=dict(path=str(executable), executable_sha256=_sha(executable.read_bytes()), version=version[:512], platform=sys.platform,
                                          adapter_sha256=_sha(Path(__file__).read_bytes()), sandbox_sha256=_sha(Path(__file__).with_name('doc_sandbox.py').read_bytes()) if sys.platform == 'linux' else None),
                           raster=raster, network_denied=sys.platform=='linux', macros_disabled=True, scaffold_passive=True,
                           original_package_opened_by_converter=False, layout_verified=False, math_verified=False,
                           font_substitution_verified=False, acceptance_granted=False, evaluated=False,
                           elapsed_seconds=round(time.monotonic()-started, 3),
                           limitations=['SOURCE_LAYOUT_NOT_VERIFIED', 'MATH_NOT_VERIFIED', 'FONT_SUBSTITUTION_NOT_VERIFIED', 'PASSIVE_SCAFFOLD_CONTEXT_OMITTED'] + ([] if sys.platform=='linux' else ['NETWORK_DENIAL_NOT_ENFORCED']),
                           limits=dict(source_bytes=MAX_SOURCE_BYTES, part_xml_bytes=MAX_PART_XML, formula_xml_bytes=MAX_FORMULA_XML, scaffold_bytes=MAX_SCAFFOLD, pdf_bytes=MAX_PDF_BYTES, png_bytes=MAX_PNG_BYTES, pixels=MAX_PIXELS, dimension=MAX_DIMENSION, timeout_seconds=TIMEOUT, derived_pages=1))
            return png, dossier
    except (OSError, subprocess.SubprocessError, ValueError, RuntimeError) as error:
        if isinstance(error, OfficeError):
            raise
        raise OfficeError('Formula preview converter/rasterizer unavailable or failed') from None


if __name__ == '__main__':
    if len(sys.argv) != 5 or sys.argv[1] != '--raster':
        raise SystemExit(2)
    png, metadata = _raster_pdf(Path(sys.argv[2]))
    Path(sys.argv[3]).write_bytes(png)
    Path(sys.argv[4]).write_text(json.dumps(metadata), encoding='utf-8')
