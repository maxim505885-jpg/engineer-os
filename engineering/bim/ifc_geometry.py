"""Optional isolated mesh bounds; PROJECT geometry is not physical verification."""
import json
import math
import subprocess
import sys
from pathlib import Path
from .ifc_adapter import inspect_ifc, _hash


def inspect_geometry(path, **options):
    return _inspect_geometry(path,**options)


def inspect_geometry_in_worker(path, **options):
    """Pure mesh operation for a caller that already applied resource limits."""
    return _inspect_geometry(path,**options,_inline=True)


def _inspect_geometry(path, *, expected_sha256, max_entities=100000, max_elements=1000,
                      max_vertices=200000, timeout_seconds=30, _inline=False):
    base=dict(status='BLOCK',scope='IFC_PROJECT_MESH_BOUNDS_ONLY',data_class='PROJECT',
              acceptance_granted=False,calculation_model_verified=False,elements=[],reasons=[])
    if (type(max_elements) is not int or not 1<=max_elements<=1000 or
        type(max_vertices) is not int or not 1<=max_vertices<=200000 or
        type(timeout_seconds) not in (int,float) or not math.isfinite(timeout_seconds) or
        not 0<timeout_seconds<=60):
        return dict(base,reasons=['IFC_GEOMETRY_LIMIT_INVALID'])
    inventory=inspect_ifc(path,expected_sha256=expected_sha256,max_entities=max_entities)
    if inventory['status']=='BLOCK':return dict(base,reasons=inventory['reasons'])
    if len(inventory['elements'])>max_elements:return dict(base,reasons=['IFC_GEOMETRY_ELEMENT_LIMIT'])
    try:
        if _inline:rows=_mesh_rows(str(Path(path).resolve()),max_vertices)
        else:
            process=subprocess.run([sys.executable,'-m','engineering.bim.ifc_geometry',str(Path(path).resolve()),
                                str(max_vertices)],capture_output=True,text=True,timeout=timeout_seconds)
            if process.returncode or len(process.stdout)>2*1024*1024:
                return dict(base,reasons=['IFC_GEOMETRY_WORKER_FAILED_OR_OUTPUT_LIMIT'])
            rows=json.loads(process.stdout,parse_constant=lambda value: (_ for _ in ()).throw(ValueError('NONFINITE_JSON')))
        if _hash(path)!=expected_sha256:return dict(base,reasons=['IFC_SOURCE_CHANGED_DURING_READ'])
        expected={r['guid'] for r in inventory['elements']}
        if not isinstance(rows,list) or {r['guid'] for r in rows}!=expected or len(rows)!=len(expected):
            return dict(base,reasons=['IFC_GEOMETRY_PROVENANCE_INVALID'])
        types={r['guid']:r['type'] for r in inventory['elements']}
        total=0
        for row in rows:
            keys={'guid','type','visibility','geometry_status','coordinate_unit','bounds_m'}
            evaluated=row.get('geometry_status')=='MESH_BOUNDS_EVALUATED'
            if evaluated:keys.add('vertex_count')
            if set(row)!=keys or row['type']!=types[row['guid']] or row['coordinate_unit']!='m':
                raise ValueError('INVALID_WORKER_ROW')
            if evaluated:
                count=row['vertex_count'];bounds=row['bounds_m']
                if type(count) is not int or not 0<count<=max_vertices or row['visibility']!='VISIBLE':
                    raise ValueError('INVALID_WORKER_MESH')
                total+=count
                if total>max_vertices:raise ValueError('IFC_GEOMETRY_VERTEX_LIMIT')
                if (not isinstance(bounds,list) or len(bounds)!=2 or
                    any(not isinstance(v,list) or len(v)!=3 for v in bounds) or
                    any(type(x) not in (int,float) or not math.isfinite(x) for v in bounds for x in v) or
                    any(bounds[0][i]>bounds[1][i] for i in range(3))):
                    raise ValueError('INVALID_WORKER_BOUNDS')
            elif (row['geometry_status']!='NOT_VERIFIED' or row['bounds_m'] is not None or
                  row['visibility'] not in ('NOT_VISIBLE','NOT_VERIFIED')):
                raise ValueError('INVALID_WORKER_UNVERIFIED')
            row.update(source_sha256=expected_sha256,locator='ifc:guid:'+row['guid'],data_class='PROJECT')
        return dict(base,status='UNCERTAINTY',source_sha256=expected_sha256,
                    length_to_m=inventory['length_to_m'],elements=rows,
                    limitations=['MESH_BOUNDS_NOT_STRUCTURAL_VERIFICATION','NOT_ACTUAL_MEASUREMENTS',
                                 'NO_SOLID_VALIDITY_OR_CLASH_OR_VOLUME_CLAIM',
                                 'RESOURCE_BOUNDARY_EXTERNAL_TO_DOMAIN' if _inline else 'KERNEL_MEMORY_NOT_HARD_CAPPED'])
    except subprocess.TimeoutExpired:return dict(base,reasons=['IFC_GEOMETRY_TIMEOUT'])
    except Exception:return dict(base,reasons=['IFC_GEOMETRY_NOT_VERIFIED'])


def _mesh_rows(path,max_vertices):
    import ifcopenshell
    import ifcopenshell.geom
    from .ifc_adapter import SUPPORTED
    model=ifcopenshell.open(path);settings=ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS,True)
    rows=[];total=0
    for kind in SUPPORTED:
        for entity in model.by_type(kind):
            row=dict(guid=entity.GlobalId,type=entity.is_a(),visibility='NOT_VISIBLE',
                     geometry_status='NOT_VERIFIED',coordinate_unit='m',bounds_m=None)
            if entity.Representation:
                try:
                    shape=ifcopenshell.geom.create_shape(settings,entity)
                    vertices=shape.geometry.verts;total+=len(vertices)//3
                    if total>max_vertices:raise ValueError('IFC_GEOMETRY_VERTEX_LIMIT')
                    if not vertices or len(vertices)%3 or not all(math.isfinite(x) for x in vertices):
                        raise ValueError('IFC_GEOMETRY_VERTICES_INVALID')
                    row.update(visibility='VISIBLE',geometry_status='MESH_BOUNDS_EVALUATED',
                               vertex_count=len(vertices)//3,
                               bounds_m=[[min(vertices[i::3]) for i in range(3)],
                                         [max(vertices[i::3]) for i in range(3)]])
                except (ValueError,MemoryError):raise
                except Exception:row.update(visibility='NOT_VERIFIED',geometry_status='NOT_VERIFIED')
            rows.append(row)
    return rows

if __name__=='__main__':print(json.dumps(_mesh_rows(sys.argv[1],int(sys.argv[2])),allow_nan=False))
