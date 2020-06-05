return null != n && (d.adjusted = n), 
null != e && e < 0 && l && (d.adjusted += Math.abs(e)), 
d[I.EnergyTypes.SOLAR] = t.getDisplayValue(d.adjusted, o, s, l, c), 
d[I.EnergyTypes.BATTERY] = t.getDisplayValue(r, o, s, !1, c), 
a !== P.GridStatuses.ISLANDED && (d[I.EnergyTypes.GRID] = t.getDisplayValue(i, o, s, !1, c)),
 u ? (d[I.EnergyTypes.USAGE] += d[I.EnergyTypes.SOLAR] * (d.adjusted < 0 && !c ? -1 : 1), 
 d[I.EnergyTypes.USAGE] += d[I.EnergyTypes.BATTERY] * (null != r && r < 0 && !c ? -1 : 1), 
 a !== P.GridStatuses.ISLANDED && (d[I.EnergyTypes.USAGE] += d[I.EnergyTypes.GRID] * (null != i && i < 0 && !c ? -1 : 1)), 
 d[I.EnergyTypes.USAGE] = d[I.EnergyTypes.USAGE] < 0 && !c ? 0 : Number((0, C.formatFixedFloat)(d[I.EnergyTypes.USAGE], s))) : d[I.EnergyTypes.USAGE] = t.getDisplayValue(e, o, s, l, c), d
