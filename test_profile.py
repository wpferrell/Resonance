# test_profile.py
import asyncio
from resonance.temporal_graph import TemporalGraph
from resonance.reinforcement import ReinforcementLoop
from resonance.profile import ProfileEngine


async def main():
    # Connect to existing data from previous tests
    graph = TemporalGraph()
    await graph.connect()

    loop = ReinforcementLoop()
    await loop.connect()

    engine = ProfileEngine(graph, loop)

    print("=== Profile Engine Test ===")
    print("Building emotional profile from stored data...")
    print()

    profile = await engine.build_profile(limit=200)

    print(f"Emotional tendency:    {profile.emotional_tendency}")
    print(f"Baseline valence:      {profile.baseline_valence:+.3f}")
    print(f"Baseline arousal:      {profile.baseline_arousal:+.3f}")
    print(f"Current trend:         {profile.current_trend}")
    print(f"WoT stability:         {profile.wot_stability}")
    print(f"Hyperarousal tendency: {profile.hyperarousal_tendency}")
    print(f"Hypoarousal tendency:  {profile.hypoarousal_tendency}")
    print(f"Regulation style:      {profile.regulation_style}")
    print(f"Reappraisal ratio:     {profile.reappraisal_ratio:.1%}")
    print(f"Suppression ratio:     {profile.suppression_ratio:.1%}")
    print(f"Wise mind ratio:       {profile.wise_mind_ratio:.1%}")
    print(f"Total corrections:     {profile.total_corrections}")
    print(f"Most corrected:        {profile.most_corrected_emotion}")
    print(f"Model reliability:     {profile.model_reliability}")
    print(f"Total nodes:           {profile.total_nodes}")
    print(f"Sessions tracked:      {profile.sessions_tracked}")
    print(f"Profile confidence:    {profile.profile_confidence}")
    print()
    print("--- Plain English Summary ---")
    print(engine.summarise(profile))
    print()
    print("✅ Profile engine working.")

    await graph.close()
    await loop.close()


asyncio.run(main())