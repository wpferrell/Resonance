from resonance import Resonance
r = Resonance(user_id='test')
r.start_panel()
import time
time.sleep(2)
r.process('I feel anxious')
print('Panel running at http://localhost:7731')
print('Press Ctrl+C to stop')
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
