import resonance.dashboard as d
from resonance.temporal_graph import TemporalGraph
from resonance.reinforcement import ReinforcementLoop
from resonance.profile import ProfileEngine

d._graph = TemporalGraph()
d._loop_obj = ReinforcementLoop()
d._engine = ProfileEngine(d._graph, d._loop_obj)

try:
    result = d._run_async(d._get_dashboard_data())
    print('OK:', result)
except Exception as e:
    import traceback
    traceback.print_exc()
    print('ERROR:', e)
