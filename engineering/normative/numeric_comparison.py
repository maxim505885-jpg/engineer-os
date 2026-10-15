"""Bounded arithmetic only. This module verifies neither a norm nor a fact."""
from decimal import Decimal, InvalidOperation, localcontext

# Explicit SI dimensions; unsupported units are rejected, never guessed.
UNITS={
    'm':('length','1'),'mm':('length','0.001'),'cm':('length','0.01'),
    'N':('force','1'),'kN':('force','1000'),
    'Pa':('pressure','1'),'kPa':('pressure','1000'),'MPa':('pressure','1000000'),
    'm2':('area','1'),'mm2':('area','0.000001'),
    '1':('dimensionless','1'),
}


def compare_quantity(*,actual,actual_unit,limit,limit_unit,operator):
    base=dict(scope='ARITHMETIC_ONLY',acceptance_granted=False,engineering_verified=False,
              status='BLOCK',satisfied=None,reasons=[])
    if any(not isinstance(u,str) or u not in UNITS for u in (actual_unit,limit_unit)):
        return dict(base,reasons=['UNSUPPORTED_UNIT'])
    if UNITS[actual_unit][0]!=UNITS[limit_unit][0]:
        return dict(base,reasons=['DIMENSION_MISMATCH'])
    if not isinstance(operator,str) or operator not in ('<=','<','>=','>','=='):
        return dict(base,reasons=['UNSUPPORTED_COMPARISON'])
    try:
        numbers=[]
        for value,unit in ((actual,actual_unit),(limit,limit_unit)):
            if not isinstance(value,str) or not value.strip() or len(value)>80:
                raise ValueError('bounded decimal string required')
            n=Decimal(value)
            if not n.is_finite() or abs(n.adjusted())>30 or len(n.as_tuple().digits)>40:
                raise ValueError('unsupported decimal range')
            with localcontext() as ctx:
                ctx.prec=80
                numbers.append(n*Decimal(UNITS[unit][1]))
        a,b=numbers
    except (InvalidOperation,ValueError):
        return dict(base,reasons=['INVALID_NUMBER'])
    satisfied={'<=':a<=b,'<':a<b,'>=':a>=b,'>':a>b,'==':a==b}[operator]
    return dict(base,status='UNCERTAINTY',satisfied=satisfied,actual_si=str(a),limit_si=str(b),
                dimension=UNITS[actual_unit][0],operator=operator,
                reasons=['INPUT_TRUTH_NOT_VERIFIED','NORMATIVE_APPLICABILITY_NOT_VERIFIED'])
