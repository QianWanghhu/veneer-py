
APPLY_FUNCTION_INIT='''
import RiverSystem.Functions.FunctionUsage as FunctionUsage
import TIME.Tools.Reflection.ReflectedItem as ReflectedItem

orig_fn_names = %s
orig_fns = [scenario.Network.FunctionManager.Functions.Where(lambda f: f.Name==ofn).FirstOrDefault() for ofn in orig_fn_names]
for i,fn in enumerate(orig_fns):
  if fn is None:
    raise Exception('Unknown function: '+orig_fn_names[i])
functions = orig_fns[::-1]
'''

APPLY_FUNCTION_LOOP='''
ignoreExceptions=True
assert target is not None
ignoreExceptions=False

if not len(functions):
    functions = orig_fns[::-1]
try:
  target = target%s

  ri = ReflectedItem.NewItem('%s',target)

  existing_usage = scenario.Network.FunctionManager.GetFunctionUsage(ri)
  if existing_usage is not None:
    scenario.Network.FunctionManager.RemoveUsage(ri)

  fn = functions.pop()
  usage = FunctionUsage()
  usage.ReflectedItem = ri

  fn.Usages.Add(usage)
  result["success"] += 1
except:
  result["fail"] += 1
  raise
'''

CLEAR_FUNCTION_LOOP='''
import TIME.Tools.Reflection.ReflectedItem as ReflectedItem

try:
  target = target%s
  ri = ReflectedItem.NewItem('%s',target)
  existing_usage = scenario.Network.FunctionManager.GetFunctionUsage(ri)
  if existing_usage is not None:
    scenario.Network.FunctionManager.RemoveUsage(ri)
  result["success"] += 1
except:
  result["fail"] += 1
  raise
'''

CLEAR_TIMESERIES_LOOP='''
import TIME.Tools.Reflection.ReflectedItem as ReflectedItem

target = %s__init__.__self__
nested = '%s'.split('.')
prop = nested[-1]
for n in nested[:-1]:
  target = getattr(target,n)
ri = ReflectedItem.NewItem(prop,target)
dm = scenario.Network.DataManager
if dm.IsUsed(ri):
  dm.RemoveUsage(ri)
'''

BUILD_PVR_LOOKUP='''
pvt_lookup = {}
for pvr in scenario.ProjectViewTable():
  if not pvr.ObjectReference in pvt_lookup:
    pvt_lookup[pvr.ObjectReference] = []
  pvt_lookup[pvr.ObjectReference].append(pvr)

'''

ENUM_PVRS='''
ignoreExceptions=False
pvrs = pvt_lookup.get(target.__init__.__self__,[])
pvrs = [(str(pvr),str(pvr.ElementRecorder.__class__),pvr.ElementName,[a.KeyString for a in pvr.ElementRecorder.RecordableAttributes]) for pvr in pvrs if System.String.IsNullOrEmpty('%s') or pvr.ElementName.StartsWith('%s')]
if len(pvrs):result.append(pvrs)
'''

CREATED_MODELLED_VARIABLE='''
ignoreExceptions=False
if not len(names): names = orig_names[::-1]
pvrs = pvt_lookup.get(target.__init__.__self__,[])
element_name = '%s'
attribute_name = '%s'
pvrs = [pvr for pvr in pvrs if System.String.IsNullOrEmpty(attribute_name) or pvr.ElementName.StartsWith(element_name)]
match=None
var_name = names.pop()

if len(pvrs)==1:
    # Nested
    #print('Found one PVR')
    match = pvrs[0]
elif len(pvrs)>1:
    matches = [pvr for pvr in pvrs if pvr.ElementName==element_name]
    if len(matches): match=matches[0]
name_exists = scenario.Network.FunctionManager.Variables.Any(lambda v: v.Name==var_name)
if match and valid_identifier(var_name) and not name_exists:
    mv = ModelledVariable()
    try:
      mv.AttributeRecordingStateName = attribute_name
    except:
      from TIME.ScenarioManagement import RecordableItemTransitionUtil
      strings = match.ElementRecorder.RecordableItems.Select(lambda ri: RecordableItemTransitionUtil.GetLegacyKeyString(ri)).ToList()

      matching_item = match.ElementRecorder.RecordableItems.FirstOrDefault(lambda ri : RecordableItemTransitionUtil.GetLegacyKeyString(ri).endswith(attribute_name))

      if matching_item is None:
        mv.AssignedRecordableItemKey = RecordableItemTransitionUtil.GetKeyForDisplayName(match,attribute_name)
      else:
        mv.AssignedRecordableItemKey = matching_item.Key
    assert match.ElementRecorder
    mv.ProjectViewRow = match
    mv.Name = var_name
    mv.DateRange = scenario.Network.FunctionManager.DateRanges[0]
    try:
      mv.Reset()
      scenario.Network.FunctionManager.Variables.Add(mv)
      result['created'].append(mv.Name)
    except Exception as e:
      result['failed'].append(var_name + ' ' + e.message + ' on ' + str(match))
else:
    result['failed'].append(var_name)
'''

VALID_IDENTIFIER_FN='''
def valid_identifier(nm):
  from System.Text import RegularExpressions

  if not nm:
    return False
  if len(nm) < 2:
    return False
  if nm[0] != '$':
    return False

  return RegularExpressions.Regex("[_A-Za-z][_a-zA-Z0-9]*$").IsMatch(nm[1:])
'''

FIND_MODELLED_VARIABLE_TARGETS='''
ignoreExceptions=False
pvrs = pvt_lookup.get(target.__init__.__self__,[])
#pvrs = [pvr for pvr in pvrs if System.String.IsNullOrEmpty(attribute_name) or pvr.ElementName.StartsWith(element_name)]

for pvr in pvrs:
  if not pvr.ElementName in result:
    result[pvr.ElementName] = []
  for attr in pvr.ElementRecorder.RecordableAttributes:
    result[pvr.ElementName].append(attr.KeyString)
'''


GET_TIME_PERIODS='''
from RiverSystem.Management.ExpressionBuilder import DateRangeListUtility
result = DateRangeListUtility.DateRanges().Select(lambda dr: dr.Name)
'''