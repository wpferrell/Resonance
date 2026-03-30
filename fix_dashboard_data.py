# Run from C:\Users\Shadow\Documents\Resonance with .venv active
# python fix_dashboard_data.py

content = open('resonance/dashboard.py', 'r', encoding='utf-8').read()

# Replace the _get_dashboard_data function to use _latest_result instead of DB
old = '''async def _get_dashboard_data():
    await _graph.connect()
    await _loop_obj.connect()
    profile = await _engine.build_profile(limit=200)
    await _graph.close()
    await _loop_obj.close()'''

new = '''async def _get_dashboard_data():
    # Use latest pushed result instead of querying DB directly
    pass'''

# Actually let's do a full replacement of the function with a simpler version
# that just uses the latest pushed result

old2 = '''async def _get_dashboard_data():
    await _graph.connect()
    await _loop_obj.connect()
    profile = await _engine.build_profile(limit=200)
    await _graph.close()
    await _loop_obj.close()

    emotion_map = {'''

new2 = '''def _get_dashboard_data_sync():
    """Build dashboard data from latest pushed result. No DB connection needed."""

    emotion_map = {'''

if old2 in content:
    content = content.replace(old2, new2)
    print('Step 1: replaced async function with sync')
else:
    print('WARNING: step 1 pattern not found')

# Fix the return statement - remove await references
content = content.replace(
    "    dominant = profile.emotional_tendency.lower() if hasattr(profile, 'emotional_tendency') else \"neutral\"",
    "    dominant = _latest_result.primary_emotion if _latest_result else \"neutral\""
)

content = content.replace(
    "    mood_pct = int((getattr(profile, 'baseline_valence', 0) + 1) / 2 * 100)",
    "    mood_pct = int((_latest_result.valence + 1) / 2 * 100) if _latest_result else 50"
)

content = content.replace(
    "    energy_pct = int(getattr(profile, 'baseline_arousal', 0.3) * 100)",
    "    energy_pct = int(_latest_result.arousal * 100) if _latest_result else 30"
)

content = content.replace(
    "    trend = getattr(profile, 'current_trend', 'stable')",
    "    trend = 'stable'"
)

print('Step 2: removed profile references')

# Fix the state route to call sync version
content = content.replace(
    "        data = _run_async(_get_dashboard_data())",
    "        data = _get_dashboard_data_sync()"
)
print('Step 3: updated route to use sync function')

# Fix start() to not create DB objects
old3 = '''    _graph = TemporalGraph()
    _loop_obj = ReinforcementLoop()
    _engine = ProfileEngine(_graph, _loop_obj)

    def _run():'''

new3 = '''    def _run():'''

if old3 in content:
    content = content.replace(old3, new3)
    print('Step 4: removed DB initialization from start()')
else:
    print('WARNING: step 4 pattern not found')

# Remove unused imports
content = content.replace(
    'from .temporal_graph import TemporalGraph\nfrom .reinforcement import ReinforcementLoop\nfrom .profile import ProfileEngine\n',
    ''
)
print('Step 5: removed unused imports')

open('resonance/dashboard.py', 'w', encoding='utf-8').write(content)
print('Done.')
