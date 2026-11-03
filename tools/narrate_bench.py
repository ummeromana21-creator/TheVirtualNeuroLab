"""Muse Spark narration for the Taste Bench: one or two plain sentences per recorded run.

Spark only DESCRIBES the recorded numbers. It never sees or changes the simulation, the rules or the scores;
its words are saved next to the numbers they describe, with the model name and time, and the page labels them.

Run once on your Mac, from the fly-lab-skeleton folder (needs your Meta API key, same as the original lab):
    pip3 install openai
    export META_API_KEY='...'            # or keep it in "Fly Brain/.env" and run from there
    python3 tools/narrate_bench.py
Writes experiments/bench_narration.json. If the key or network is missing, nothing is written and the page simply
shows no narration.
"""
import json, os, sys, time, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(HERE, '..', 'experiments')
for envf in (os.path.join(HERE, '..', '.env'), os.path.expanduser('~/Desktop/Fly Brain/.env')):
    if os.path.exists(envf) and not os.environ.get('META_API_KEY'):
        for line in open(envf):
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
key = os.environ.get('META_API_KEY', '')
if not key or key.startswith('your_'):
    sys.exit('No META_API_KEY found; nothing written.')
from openai import OpenAI
client = OpenAI(api_key=key, base_url=os.environ.get('META_BASE_URL', 'https://api.meta.ai/v1'))
model = os.environ.get('META_MODEL', 'muse-spark-1.3')
bench = json.load(open(os.path.join(EXP, 'bench.json')))
SYSTEM = ("You narrate a recorded simulation of a fruit fly brain for a general audience, in 1-2 short sentences, "
          "plain words, no jargon, no exclamation marks. Use ONLY the numbers given. Do not add facts, causes, "
          "comparisons or claims about real flies. 'Tongue out' means the tongue motor neuron MN9 fired 10 or more "
          "times per second.")
out = dict(model=model, made=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
           note='Written by Muse Spark from the recorded numbers only; it does not affect any result.', lines={})
for name, r in bench['runs'].items():
    s, b, w = (int(x[1:]) for x in name.split('_'))
    if s == b == w == 0:
        continue
    facts = (f"Tastes switched on: sugar {s}, bitter {b}, water {w} (signals per second; 0 = off). "
             f"Tongue motor neuron MN9 fired {r['mn9']} times per second. "
             f"{len(r['idx'])} of 139,255 neurons fired. Verdict: {'tongue out' if r['mn9'] >= 10 else 'tongue stays in'}.")
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(model=model, max_tokens=90, temperature=0.3,
                                                  messages=[{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': facts}])
            out['lines'][name] = resp.choices[0].message.content.strip()
            print(name, '->', out['lines'][name]); break
        except Exception as e:
            print(name, 'retry', attempt, repr(e)[:120]); time.sleep(2)
json.dump(out, open(os.path.join(EXP, 'bench_narration.json'), 'w'), indent=1, ensure_ascii=False)
print('written', len(out['lines']), 'lines')
