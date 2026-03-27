import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "resonance"))

from extractor import Extractor, EmotionResult
from storage import Storage

TEST_MESSAGES = [
    ("happy",      "I am so happy today, everything feels amazing and wonderful!"),
    ("sad",        "I can't stop crying. Everything feels hopeless and I'm devastated."),
    ("angry",      "I am furious. This is completely outrageous and I am seething."),
    ("suppress",   "I'm fine, don't worry about me. It's nothing, no big deal."),
    ("guilt",      "I let everyone down. It was all my fault. I'm ashamed of myself."),
]

USER_ID = "test_user"
SESSION_ID = "step4_test"


def run():
    print("\n" + "="*60)
    print("RESONANCE — Step 4 Pipeline Test")
    print("="*60)

    extractor = Extractor()
    store = Storage()

    print("\n✓ Extractor and Storage initialised\n")

    print("-"*60)
    print("PART 1: Running 5 sentences through extractor → storage")
    print("-"*60)

    saved_ids = []

    for label, text in TEST_MESSAGES:
        print(f"\n[{label.upper()}]")
        print(f"  Input : {text}")
        result = extractor.extract(text)
        print(f"  Primary   : {result.primary_emotion}")
        print(f"  Secondary : {result.secondary_emotion}")
        print(f"  VAD       : valence={result.valence:+.2f}  arousal={result.arousal:.2f}  dominance={result.dominance:.2f}")
        print(f"  WoT       : {result.window_of_tolerance} [{result.wot_triggered_by}]")
        print(f"  Suppress  : {result.suppression_signal}   Reappraise: {result.reappraisal_signal}")
        print(f"  Guilt     : {result.guilt_type}")
        print(f"  Confidence: {result.confidence:.2f}   Alexithymia: {result.alexithymia_flag}")
        record_id = store.save(
            result=result,
            user_id=USER_ID,
            session_id=SESSION_ID,
            topic=label,
        )
        saved_ids.append(record_id)
        print(f"  Saved → {record_id}")

    print("\n" + "-"*60)
    print("PART 2: Reading back current state for test_user")
    print("-"*60)

    state = store.get_current_state(USER_ID)
    if isinstance(state, list) and len(state) > 0:
        state = state[0]
    if state:
        print(f"\n  Last emotion : {state.get('primary_emotion')} / {state.get('secondary_emotion')}")
        print(f"  VAD          : valence={state.get('valence'):+.2f}  arousal={state.get('arousal'):.2f}")
        print(f"  WoT          : {state.get('window_of_tolerance')}")
        print(f"  Last updated : {state.get('last_updated')}")
    else:
        print("  WARNING: No current state found.")

    print("\n" + "-"*60)
    print("PART 3: Reading back recent history (last 10)")
    print("-"*60)

    history = store.get_recent(USER_ID, limit=10)
    if isinstance(history, list) and len(history) > 0 and isinstance(history[0], list):
        history = history[0]
    print(f"\n  Records found: {len(history)}")
    for i, record in enumerate(history):
        print(f"  [{i+1}] {record.get('primary_emotion'):12}  topic={record.get('topic'):10}  confidence={record.get('confidence'):.2f}")

    print("\n" + "="*60)
    if len(history) >= 5 and state:
        print("✓ STEP 4 PASSED — full pipeline working end to end.")
    else:
        print("✗ STEP 4 INCOMPLETE — check warnings above.")
    print("="*60 + "\n")

    store.close()


if __name__ == "__main__":
    run()