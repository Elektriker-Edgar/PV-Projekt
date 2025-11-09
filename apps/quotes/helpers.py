from decimal import Decimal


def infer_inverter_class_key(power_kw: Decimal) -> str:
    value = Decimal(str(power_kw or 0))
    if value <= Decimal('1.5'):
        return '1kva'
    if value <= Decimal('3.5'):
        return '3kva'
    if value <= Decimal('6.5'):
        return '5kva'
    return '10kva'


def inverter_label_from_power(power_kw: Decimal) -> str:
    key = infer_inverter_class_key(power_kw)
    return {
        '1kva': 'bis 1 kVA',
        '3kva': 'bis 3 kVA',
        '5kva': 'bis 5 kVA',
        '10kva': 'über 5 kVA',
    }.get(key, 'kVA')
