"""Opt-in linear XY frame/axial-truss control, explicit SI and provenance references."""
from dataclasses import dataclass, asdict
import hashlib
import json
import math
import re
import importlib.metadata

@dataclass(frozen=True)
class Node:
    name: str
    x_m: float
    y_m: float
    fix_x: bool = False
    fix_y: bool = False
    fix_rz: bool = False

@dataclass(frozen=True)
class Member:
    name: str
    start: str
    end: str
    elastic_modulus_pa: float
    area_m2: float
    iz_m4: float

@dataclass(frozen=True)
class PlanarInput:
    nodes: tuple[Node, ...]
    members: tuple[Member, ...]
    loads: tuple[tuple[str, float, float, float], ...]
    source_sha256: str
    evidence_ids: tuple[str, ...]
    units: str = 'N_m_Pa'
    kind: str = 'frame'

def provenance_valid(source, evidence):
    return (isinstance(source,str) and re.fullmatch('[0-9a-f]{64}',source) is not None
            and isinstance(evidence,tuple) and 0<len(evidence)<=100
            and all(isinstance(e,str) and e.strip() and len(e)<=200 for e in evidence)
            and len(set(evidence))==len(evidence))

def finite(value):
    return type(value) in (int,float) and math.isfinite(value) and abs(value)<=1e15

def calculate_planar(inputs):
    base=dict(status='BLOCK', data_class='CALCULATED',acceptance_granted=False,
              actual_structure_verified=False,normative_verification='NOT_RUN',
              scope='LINEAR_ELASTIC_XY_NODAL_LOAD_FRAME_OR_AXIAL_TRUSS')
    try:
        if not isinstance(inputs,PlanarInput):raise ValueError('TYPED_INPUT_REQUIRED')
        if inputs.units!='N_m_Pa':raise ValueError('EXPLICIT_SI_UNITS_REQUIRED')
        if not provenance_valid(inputs.source_sha256,inputs.evidence_ids):raise ValueError('SOURCE_AND_EVIDENCE_REFERENCES_REQUIRED')
        if inputs.kind not in ('frame','truss'):raise ValueError('UNSUPPORTED_MODEL_KIND')
        if not isinstance(inputs.nodes,tuple) or not 2<=len(inputs.nodes)<=500:raise ValueError('INVALID_NODES')
        if not isinstance(inputs.members,tuple) or not 1<=len(inputs.members)<=1000:raise ValueError('INVALID_MEMBERS')
        names={}
        for n in inputs.nodes:
            if not isinstance(n,Node) or not isinstance(n.name,str) or not n.name.strip() or n.name in names:raise ValueError('INVALID_NODE_ID')
            if not all(finite(v) for v in (n.x_m,n.y_m)) or not all(type(v) is bool for v in (n.fix_x,n.fix_y,n.fix_rz)):raise ValueError('INVALID_NODE_DATA')
            names[n.name]=n
        ids=set()
        for m in inputs.members:
            if not isinstance(m,Member) or not isinstance(m.name,str) or not m.name.strip() or m.name in ids or m.start not in names or m.end not in names:raise ValueError('INVALID_MEMBER_ID_OR_CONNECTIVITY')
            ids.add(m.name)
            if not all(finite(v) and v>0 for v in (m.elastic_modulus_pa,m.area_m2,m.iz_m4)):raise ValueError('POSITIVE_FINITE_PROPERTIES_REQUIRED')
            a,b=names[m.start],names[m.end]
            if math.hypot(a.x_m-b.x_m,a.y_m-b.y_m)<=1e-9:raise ValueError('ZERO_LENGTH_MEMBER')
        if not isinstance(inputs.loads,tuple) or not inputs.loads:raise ValueError('NODAL_LOADS_REQUIRED')
        for load in inputs.loads:
            if not isinstance(load,tuple) or len(load)!=4 or load[0] not in names or not all(finite(v) for v in load[1:]):raise ValueError('INVALID_NODAL_LOAD')
            if inputs.kind=='truss' and load[3]!=0:raise ValueError('TRUSS_MOMENT_UNSUPPORTED')
        raw=json.dumps(asdict(inputs),sort_keys=True,allow_nan=False,separators=(',',':'))
        base.update(source_sha256=inputs.source_sha256,evidence_ids=list(inputs.evidence_ids),inputs=asdict(inputs),input_sha256=hashlib.sha256(raw.encode()).hexdigest())
    except (ValueError,TypeError,AttributeError) as exc:
        return dict(base,reasons=[str(exc)])
    try:
        from Pynite import FEModel3D
        model=FEModel3D()
        for n in inputs.nodes:
            model.add_node(n.name,n.x_m,n.y_m,0)
            model.def_support(n.name,n.fix_x,n.fix_y,True,True,True,n.fix_rz or inputs.kind=='truss')
        for index,m in enumerate(inputs.members):
            key=str(index)
            # Out-of-plane constants and Poisson ratio are inactive numerical auxiliaries.
            model.add_material(key,m.elastic_modulus_pa,m.elastic_modulus_pa/2.6,.3,0)
            model.add_section(key,m.area_m2,m.iz_m4,m.iz_m4,m.iz_m4)
            model.add_member(m.name,m.start,m.end,key,key)
            if inputs.kind=='truss':model.def_releases(m.name,Rzi=True,Rzj=True)
        for name,fx,fy,mz in inputs.loads:
            for direction,value in (('FX',fx),('FY',fy),('MZ',mz)):
                if value:model.add_node_load(name,direction,value,case='control')
        model.add_load_combo('control',{'control':1.})
        model.analyze_linear(check_stability=True)
        result={n.name:dict(dx_m=float(model.nodes[n.name].DX['control']),dy_m=float(model.nodes[n.name].DY['control']),rz_rad=float(model.nodes[n.name].RZ['control']),reaction_fx_n=float(model.nodes[n.name].RxnFX['control']),reaction_fy_n=float(model.nodes[n.name].RxnFY['control']),reaction_mz_nm=float(model.nodes[n.name].RxnMZ['control'])) for n in inputs.nodes}
        if not all(math.isfinite(v) for n in result.values() for v in n.values()):raise ValueError('NONFINITE_SOLVER_RESULT')
        applied=[sum(l[i] for l in inputs.loads) for i in (1,2)]
        sums=[sum(n['reaction_fx_n'] for n in result.values())+applied[0],sum(n['reaction_fy_n'] for n in result.values())+applied[1]]
        moment=sum(result[n.name]['reaction_mz_nm']+n.x_m*result[n.name]['reaction_fy_n']-n.y_m*result[n.name]['reaction_fx_n'] for n in inputs.nodes)+sum(mz+names[name].x_m*fy-names[name].y_m*fx for name,fx,fy,mz in inputs.loads)
        force_scales=[max(1.,sum(abs(load[axis]) for load in inputs.loads)) for axis in (1,2)]
        moment_scale=max(1.,sum(abs(mz)+abs(names[name].x_m*fy)+abs(names[name].y_m*fx) for name,fx,fy,mz in inputs.loads))
        checks={'finite_results':True,'force_equilibrium':all(abs(value)<=1e-7*scale for value,scale in zip(sums,force_scales)),'moment_equilibrium':abs(moment)<=1e-7*moment_scale}
        return dict(base,status='PASS' if all(checks.values()) else 'BLOCK',reasons=[] if all(checks.values()) else ['EQUILIBRIUM_FAILED'],results={'nodes':result},checks=checks,solver='PyniteFEA',solver_version=importlib.metadata.version('PyniteFEA'),assumptions=['LINEAR_ELASTIC_SMALL_DISPLACEMENTS','STRAIGHT_PRISMATIC_MEMBERS','NODAL_LOADS_SINGLE_COMBINATION','NO_SELF_WEIGHT_PDELTA_BUCKLING_PLASTICITY_OR_SHEAR_DEFORMATION','TRUSS_AXIAL_ONLY' if inputs.kind=='truss' else 'RIGID_FRAME_JOINTS','OUT_OF_PLANE_AUXILIARIES_NOT_ACTUAL_PROPERTIES','EVIDENCE_REFERENCES_NOT_INDEPENDENTLY_VERIFIED'])
    except ImportError:return dict(base,reasons=['PYNITE_DEPENDENCY_UNAVAILABLE'])
    except Exception as exc:return dict(base,reasons=['SOLVER_FAILED_OR_UNSTABLE'],solver_error_type=type(exc).__name__)
