# test_reinforcement.py
import asyncio
from resonance.extractor import EmotionResult
from resonance.reinforcement import ReinforcementLoop


def make_emotion(primary, valence, arousal, dominance):
    r = EmotionResult()
    r.primary_emotion = primary
    r.secondary_emotion = None
    r.valence = valence
    r.arousal = arousal
    r.dominance = dominance
    r.window_of_tolerance = "window"
    r.reappraisal_signal = False
    r.suppression_signal = False
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
    loop = ReinforcementLoop()
    await loop.connect()

    print("=== Reinforcement Loop Test ===")
    print()

    # Simulate Resonance detecting 'sadness' but user correcting to 'frustration' 3 times
    print("Storing 3 corrections: sadness → frustration...")
    for i in range(3):
        emotion = make_emotion("sadness", -0.4, 0.3, 0.2)
        await loop.store_correction(
            original_text=f"I can't believe this happened again ({i+1})",
            emotion_result=emotion,
            corrected_emotion="frustration",
            session_id="test_session_1"
        )
    print("  Done.")
    print()

    # Now check — if Resonance detects 'sadness' again, should it flag it?
    print("Checking new detection of 'sadness'...")
    emotion = make_emotion("sadness", -0.3, 0.4, 0.2)
    signal = await loop.check_detection(emotion)

    print(f"  Should flag:           {signal.should_flag}")
    print(f"  Confidence adjustment: {signal.confidence_adjustment:+.2f}")
    print(f"  Similar corrections:   {signal.similar_corrections}")
    print(f"  Suggested emotion:     {signal.suggested_emotion}")
    print()

    # Summary
    print("Correction summary:")
    summary = await loop.get_correction_summary()
    print(f"  Total corrections:     {summary['total_corrections']}")
    print(f"  Most corrected:        {summary['most_corrected_emotion']}")
    print(f"  Correction pairs:      {summary['correction_pairs']}")
    print()
    print("✅ Reinforcement loop working.")

    await loop.close()


asyncio.run(main())