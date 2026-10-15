"""Installed local capabilities; presence is never proof of a successful run."""
import importlib.metadata
import os
from pathlib import Path
import shutil


def report():
    packages={}
    for name in ('docling','PyMuPDF','Pillow','ezdxf','olefile','img2table','paddleocr','pywebview','pyvista','pywin32','ifcopenshell','PyniteFEA'):
        try:packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:packages[name]='NOT_INSTALLED'
    from .doc_conversion import converter_identity
    scad=Path(os.environ['ENGINEER_OS_SCAD_HOME']) if os.environ.get('ENGINEER_OS_SCAD_HOME') else None
    from .capability_receipts import capability_report,find_tesseract
    return dict(status='UNCERTAINTY',execution_verified=False,acceptance_granted=False,packages=packages,
                profile=capability_report(os.environ.get('ENGINEER_OS_PROFILE','native')),
                libreoffice=converter_identity(),tesseract=find_tesseract() is not None,
                tables=dict(optional_python_configured=bool(os.environ.get('ENGINEER_OS_TABLE_PYTHON')),local_models_configured=bool(os.environ.get('ENGINEER_OS_PADDLE_MODELS_MANIFEST')),execution_verified=False),
                lira=dict(input_reader='IMPLEMENTED',result_reader='IMPLEMENTED',vendor_execution_verified=False,model_result_association_verified=False),
                scad=dict(sdk_configured=scad is not None,header_present=bool(scad and (scad/'API'/'Include'/'ScadAPIX.hxx').is_file()),adapter='NOT_IMPLEMENTED',vendor_execution_verified=False),
                pdf_viewer=dict(engine='PDF.js',local_only=True,execution_verified=False))
