# test_temporal.py
import asyncio
from resonance.extractor import EmotionResult
from resonance.comparison import compare
from resonance.temporal_graph import TemporalGraph


def make_emotion(valence, arousal, dominance, primary="neutral", wot="window", reappraisal=False, suppression=False):
    r = EmotionResult()
    r.valence = valence
    r.arousal = arousal
    r.dominance = dominance
    r.primary_emotion = primary
    r.secondary_emotion = None
    r.window_of_tolerance = wot
    r.reappraisal_signal = reappraisal
    r.suppression_signal = suppression
    r.wise_mind_signal = "reasonable_mind"
    r.guilt_type = None
    r.confidence = 0.85
    r.alexithymia_flag = False
    r.modality = "text"
    r.raw_nrc_scores = {}
    r.raw_empath_scores = {}
    r.wot_triggered_by = []
    return r


async def main():
    graph = TemporalGraph()
    await graph.connect()

    print("=== Temporal Graph Test ===")
    print("Adding 5 emotion nodes...")

    emotions = [
        make_emotion(0.4,  0.2, 0.6, "joy",     reappraisal=True),
        make_emotion(0.1,  0.5, 0.4, "anxiety",  wot="hyperarousal"),
        make_emotion(-0.2, 0.7, 0.3, "anger",    wot="hyperarousal", suppression=True),
        make_emotion(0.0,  0.4, 0.4, "neutral",  reappraisal=True),
        make_emotion(0.3,  0.3, 0.5, "joy",      reappraisal=True),
    ]

    history = []
    for i, emotion in enumerate(emotions):
        comparison = compare(emotion, history)
        node_id = await graph.add_node(emotion, comparison, session_id="test_session_1")
        print(f"  Node {i+1} added — {emotion.primary_emotion} (valence {emotion.valence:+.1f})")
        history.append(emotion)

    print()
    print("Analysing patterns...")
    patterns = await graph.get_patterns(limit=100)

    print(f"Total nodes:          {patterns.total_nodes}")
    print(f"Dominant emotion:     {patterns.dominant_emotion}")
    print(f"Average valence:      {patterns.average_valence:+.3f}")
    print(f"Average arousal:      {patterns.average_arousal:+.3f}")
    print(f"Valence trend:        {patterns.valence_trend}")
    print(f"Hyperarousal count:   {patterns.hyperarousal_count}")
    print(f"Hypoarousal count:    {patterns.hypoarousal_count}")
    print(f"Reappraisal ratio:    {patterns.reappraisal_ratio:.1%}")
    print(f"Suppression ratio:    {patterns.suppression_ratio:.1%}")
    print(f"Spike count:          {patterns.spike_count}")
    print(f"Wise mind ratio:      {patterns.wise_mind_ratio:.1%}")
    print(f"Sessions tracked:     {patterns.sessions_tracked}")
    print()
    print("✅ Temporal graph working.")

    await graph.close()


asyncio.run(main())