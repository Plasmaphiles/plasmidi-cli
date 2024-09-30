__all__ = ['to_plasma']

__ID_LIST = {
	'Drum': range(9, 17),
	'Bass': range(32, 40),
	'Pads': range(80, 104),
	#Everything else is Keys
}

#Generate reverse instrument list for fast lookup.
__INSTR_LIST = {}
for i in __ID_LIST:
	for k in __ID_LIST[i]:
		__INSTR_LIST[k] = i

"""
Convert a midi instrument ID to an appropriate Plasma instrument counterpart
"""
def to_plasma(instrument_id: int) -> str:
	global __INSTR_LIST
	return __INSTR_LIST.get(instrument_id, 'Keys')