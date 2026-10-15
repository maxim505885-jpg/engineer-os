"""Read-only, exact DXF comparison. A converted DXF cannot prove DWG fidelity."""
from collections import Counter
import hashlib
import math
from pathlib import Path

from .dxf_workflow import _geometry, _layers, _load, _resources


def compare_dxf(source, output, *, source_sha256):
    report=dict(status='BLOCK',scope='DXF_SERIALIZED_DATA_ONLY',reasons=[],
                acceptance_granted=False,dwg_equivalence_verified=False,
                engineering_verified=False)
    try:
        before,identity=_load(source,source_sha256,inventory=True)
        after,output_identity=_load(output,inventory=True)
        old=_geometry(before);new=_geometry(after)
        old_types={e.dxf.handle:e.dxftype() for block in before.blocks for e in block}
        new_types={e.dxf.handle:e.dxftype() for block in after.blocks for e in block}
        missing=sorted(set(old)-set(new));added=sorted(set(new)-set(old))
        changed=sorted(h for h in set(old)&set(new) if old[h]!=new[h])
        reasons=[]
        from ezdxf.lldxf.tagwriter import TagCollector
        for doc in (before,after):
            for block in doc.blocks:
                for entity in block:
                    for tag in TagCollector.dxftags(entity):
                        values=tuple(tag.value) if hasattr(tag.value,'x') else (tag.value,)
                        if any(isinstance(v,float) and not math.isfinite(v) for v in values):
                            reasons.append('NONFINITE_SOURCE_GEOMETRY')
        if missing:reasons.append('SOURCE_ENTITIES_MISSING')
        if added:reasons.append('ENTITIES_ADDED')
        if changed:reasons.append('ENTITY_DATA_CHANGED')
        if before.units==0 or after.units==0 or not 1<=before.units<=24 or not 1<=after.units<=24:
            reasons.append('DECLARED_UNITS_REQUIRED')
        if before.units!=after.units:reasons.append('UNITS_CHANGED')
        if before.dxfversion!=after.dxfversion:reasons.append('DXF_VERSION_CHANGED')
        if _layers(before)!=_layers(after):reasons.append('LAYER_DATA_CHANGED')
        if _resources(before)!=_resources(after):reasons.append('RESOURCE_DATA_CHANGED')
        # Audit separate in-memory copies: ezdxf audit may repair its argument.
        for path in (source,output):
            from .dxf_workflow import _reader
            audit=_reader().readfile(path).audit()
            if audit.has_errors or audit.has_fixes:reasons.append('DXF_AUDIT_ERRORS_OR_REPAIRS')
        for path,expected in ((source,identity['source_sha256']),(output,output_identity['source_sha256'])):
            if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:
                reasons.append('SOURCE_CHANGED_DURING_COMPARISON')
        return dict(report,status='BLOCK' if reasons else 'PASS',reasons=list(dict.fromkeys(reasons)),
                    source_sha256=identity['source_sha256'],output_sha256=output_identity['source_sha256'],
                    source_entities=len(old),output_entities=len(new),
                    missing_handles=missing,added_handles=added,changed_handles=changed,
                    missing_by_type=dict(Counter(old_types[h] for h in missing)),
                    added_by_type=dict(Counter(new_types[h] for h in added)),
                    changed_by_type=dict(Counter(old_types[h] for h in changed)))
    except Exception:
        return dict(report,reasons=['DXF_COMPARISON_UNAVAILABLE_OR_IDENTITY_INVALID'])
