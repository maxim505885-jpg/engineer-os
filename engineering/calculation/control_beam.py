"""Qualified narrow benchmark: linear Euler-Bernoulli simply supported UDL beam."""
from dataclasses import asdict,dataclass
import hashlib
import importlib.metadata
import json
import math
import re


@dataclass(frozen=True)
class BeamInput:
    length_m:float
    elastic_modulus_pa:float
    inertia_m4:float
    area_m2:float
    load_n_m:float
    source_sha256:str
    evidence_ids:tuple[str,...]
    units:str='N_m_Pa'


def calculate_beam(inputs):
    base=dict(status='BLOCK',scope='SIMPLY_SUPPORTED_UDL_LINEAR_BENCHMARK',
              data_class='CALCULATED',acceptance_granted=False,
              actual_structure_verified=False,normative_verification='NOT_RUN')
    if not isinstance(inputs,BeamInput):return dict(base,reasons=['TYPED_BEAM_INPUT_REQUIRED'])
    values=(inputs.length_m,inputs.elastic_modulus_pa,inputs.inertia_m4,inputs.area_m2)
    if any(type(x) not in (int,float) or not math.isfinite(x) or not 0<x<=1e15 for x in values):
        return dict(base,reasons=['POSITIVE_FINITE_GEOMETRY_AND_MATERIAL_REQUIRED'])
    if type(inputs.load_n_m) not in (int,float) or not math.isfinite(inputs.load_n_m) or not 0<=inputs.load_n_m<=1e12:
        return dict(base,reasons=['FINITE_NONNEGATIVE_LOAD_REQUIRED'])
    if inputs.units!='N_m_Pa':return dict(base,reasons=['EXPLICIT_SI_UNITS_REQUIRED'])
    if (not isinstance(inputs.source_sha256,str) or not re.fullmatch('[0-9a-f]{64}',inputs.source_sha256)
            or not isinstance(inputs.evidence_ids,tuple) or not 1<=len(inputs.evidence_ids)<=100
            or any(not isinstance(x,str) or not x.strip() or len(x)>200 for x in inputs.evidence_ids)
            or len(set(inputs.evidence_ids))!=len(inputs.evidence_ids)):
        return dict(base,reasons=['SOURCE_AND_EVIDENCE_REFERENCES_REQUIRED'])
    raw=json.dumps(asdict(inputs),sort_keys=True,allow_nan=False,separators=(',',':'))
    base.update(source_sha256=inputs.source_sha256,evidence_ids=list(inputs.evidence_ids),
                input_sha256=hashlib.sha256(raw.encode()).hexdigest(),inputs=asdict(inputs))
    try:
        from Pynite import FEModel3D
        model=FEModel3D();L=inputs.length_m;E=inputs.elastic_modulus_pa;I=inputs.inertia_m4;q=inputs.load_n_m
        model.add_node('left',0,0,0);model.add_node('right',L,0,0)
        # G/nu, Iy/J are inactive for this fully restrained out-of-plane model.
        # They are numerical auxiliaries, not inferred actual material/section data.
        model.add_material('benchmark',E,E/(2*1.3),0.3,0)
        model.add_section('benchmark',inputs.area_m2,I,I,I)
        model.add_member('beam','left','right','benchmark','benchmark')
        model.def_support('left',True,True,True,True,True,False)
        model.def_support('right',False,True,True,True,True,False)
        model.add_member_dist_load('beam','Fy',-q,-q,case='service')
        model.add_load_combo('service',{'service':1.0})
        model.analyze_linear(check_stability=True)
        member=model.members['beam']
        results=dict(reaction_left_n=float(model.nodes['left'].RxnFY['service']),
                     reaction_right_n=float(model.nodes['right'].RxnFY['service']),
                     midspan_moment_nm=float(member.moment('Mz',L/2,'service')),
                     midspan_deflection_m=float(member.deflection('dy',L/2,'service')),
                     left_shear_n=float(member.shear('Fy',0,'service')))
        expected=dict(reaction_left_n=q*L/2,reaction_right_n=q*L/2,
                      midspan_moment_nm=q*L**2/8,midspan_deflection_m=5*q*L**4/(384*E*I),
                      left_shear_n=q*L/2)
        checks={k:math.isfinite(v) and math.isclose(abs(v),expected[k],rel_tol=1e-7,abs_tol=1e-10)
                for k,v in results.items()}
        checks['vertical_equilibrium']=math.isclose(results['reaction_left_n']+results['reaction_right_n'],q*L,rel_tol=1e-7,abs_tol=1e-10)
        checks['downward_deflection']=results['midspan_deflection_m']<=0
        return dict(base,status='PASS' if all(checks.values()) else 'BLOCK',
                    solver='PyniteFEA',solver_version=importlib.metadata.version('PyniteFEA'),
                    results=results,analytic_reference=expected,checks=checks,
                    reasons=[] if all(checks.values()) else ['ANALYTICAL_BENCHMARK_MISMATCH'],
                    assumptions=['LINEAR_ELASTIC_SMALL_DISPLACEMENT','CONSTANT_E_AND_IZ',
                        'SIMPLY_SUPPORTED_XY_PLANE','UDL_DOWNWARD_GLOBAL_Y',
                        'NO_SELF_WEIGHT_OR_SHEAR_DEFORMATION','AUXILIARY_G_NU_IY_J_NOT_ACTUAL_PROPERTIES',
                        'EVIDENCE_REFERENCES_NOT_INDEPENDENTLY_VERIFIED'])
    except ImportError:return dict(base,reasons=['PYNITE_DEPENDENCY_UNAVAILABLE'])
    except Exception:return dict(base,reasons=['CONTROL_BEAM_SOLVER_FAILED'])
