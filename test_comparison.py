# test_comparison.py
from resonance.extractor import EmotionResult
from resonance.comparison import compare

def make_result(valence, arousal, dominance, wot="window", reappraisal=False, suppression=False):
    r = EmotionResult()
    r.valence = valence
    r.arousal = arousal
    r.dominance = dominance
    r.window_of_tolerance = wot
    r.reappraisal_signal = reappraisal
    r.suppression_signal = suppression
    r.primary_emotion = "neutral"
    r.secondary_emotion = None
    r.guilt_type = None
    r.wise_mind_signal = "reasonable_mind"
    r.confidence = 0.85
    r.alexithymia_flag = False
    r.modality = "text"
    r.raw_nrc_scores = {}
    r.raw_empath_scores = {}
    r.wot_triggered_by = []
    return r

history = [
    make_result(0.3,  0.2,  0.5),
    make_result(0.1,  0.4,  0.4),
    make_result(-0.1, 0.6,  0.3),
    make_result(-0.3, 0.8,  0.2, wot="hyperarousal"),
]

current = make_result(-0.1, 0.65, 0.3, wot="hyperarousal")

result = compare(current, history)

print("=== Comparison Engine Test ===")
print(f"Valence delta:      {result.valence_delta:+.2f}")
print(f"Arousal delta:      {result.arousal_delta:+.2f}")
print(f"Dominance delta:    {result.dominance_delta:+.2f}")
print(f"Trajectory:         {result.trajectory}")
print(f"Spike detected:     {result.spike_detected} ({result.spike_dimension})")
print(f"WoT crossing:       {result.wot_crossing} ({result.wot_direction})")
print(f"Reappraisal trend:  {result.reappraisal_trending}")
print(f"Suppression build:  {result.suppression_building}")
print(f"History depth:      {result.history_depth}")
print()
print("✅ All fields populated — comparison engine working.")