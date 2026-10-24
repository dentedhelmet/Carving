"""Make a timed, self-contained edit from the untouched source assets.

Run with the Kokoro-enabled Python described in README.md. Original photos and
videos remain in ../assets. Narration is synthetic, not a clone of the maker.
"""
from pathlib import Path
import concurrent.futures
import json
import subprocess

import numpy as np
import soundfile as sf
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'assets'
ASSETS = ROOT / 'assets'
CACHE = Path('/workspace/.cache/tiki-tts')
ASSETS.mkdir(exist_ok=True)
SCENES = json.loads((ROOT / 'storyboard.json').read_text())
TARGET = 84.0
RATE = 24000

def run(args):
    subprocess.run(args, check=True)

def duration(path):
    return len(sf.read(path)[0]) / RATE

def make_narration():
    from kokoro_onnx import Kokoro
    import onnxruntime as ort
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(CACHE / 'kokoro-v1.0.onnx'), sess_options=options, providers=['CPUExecutionProvider'])
    model = Kokoro.from_session(session, str(CACHE / 'voices-v1.0.bin'))
    for scene in SCENES:
        for i, text in enumerate(scene['lines']):
            name = f"voice-{scene['id']}-{i}.wav"
            target = ASSETS / name
            if not target.exists():
                samples, sr = model.create(text, voice='am_michael', speed=1.03, lang='en-us')
                assert sr == RATE
                sf.write(target, samples, sr)
            print(f'{name}: {duration(target):.2f}s', flush=True)

def make_timeline():
    voice_total = sum(duration(ASSETS / f"voice-{s['id']}-{i}.wav") for s in SCENES for i in range(len(s['lines'])))
    gaps = sum((len(s['lines']) - 1) * .12 + .85 for s in SCENES)
    if voice_total + gaps > TARGET:
        factor = voice_total / (TARGET - gaps)
        assert factor < 1.25, 'Rewrite the script instead of rushing the narration'
        for s in SCENES:
            for i in range(len(s['lines'])):
                target = ASSETS / f"voice-{s['id']}-{i}.wav"
                temp = target.with_suffix('.fit.wav')
                run(['ffmpeg','-v','error','-y','-i',str(target),'-af',f'atempo={factor:.8f}','-ar',str(RATE),str(temp)])
                temp.replace(target)
        voice_total = sum(duration(ASSETS / f"voice-{s['id']}-{i}.wav") for s in SCENES for i in range(len(s['lines'])))
    extra = max(0, (TARGET - voice_total - gaps) / len(SCENES))
    cursor = 0.0
    lines = []
    mix = np.zeros(round(TARGET * RATE), dtype=np.float32)
    for s in SCENES:
        s['start'] = round(cursor, 6)
        voice_cursor = cursor + .45
        for i, text in enumerate(s['lines']):
            path = ASSETS / f"voice-{s['id']}-{i}.wav"
            samples, sr = sf.read(path, dtype='float32')
            start = round(voice_cursor * RATE)
            mix[start:start+len(samples)] += samples
            end = voice_cursor + len(samples) / sr
            lines.append({'text':text,'start':round(voice_cursor,6),'end':round(end,6)})
            voice_cursor = end + .12
        s['duration'] = round(voice_cursor - cursor - .12 + .4 + extra, 6)
        s['visual_duration'] = s['duration'] + (.4 if s is not SCENES[-1] else 0)
        s['media'] = f"assets/{s['id']}.{'jpg' if 'photo' in s else 'mp4'}"
        cursor += s['duration']
    assert abs(cursor-TARGET) < .025, cursor
    sf.write(ASSETS / 'narration.wav', mix, RATE)
    run(['ffmpeg','-v','error','-y','-i',str(ASSETS/'narration.wav'),'-af','loudnorm=I=-17:TP=-1.5:LRA=9','-c:a','aac','-b:a','192k',str(ASSETS/'narration.m4a')])
    for i,line in enumerate(lines):
        next_start = lines[i+1]['start'] if i+1 < len(lines) else TARGET-.65
        line['end'] = round(min(line['end']+.55,next_start-.08),6)
    (ROOT/'timeline.json').write_text(json.dumps({'duration':TARGET,'scenes':SCENES,'captions':lines},indent=2))
    def stamp(t):
        ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);sec,ms=divmod(ms,1000)
        return f'{h:02}:{m:02}:{sec:02},{ms:03}'
    (ROOT/'captions.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(l['start'])} --> {stamp(l['end'])}\n{l['text']}" for i,l in enumerate(lines))+'\n')
    (ROOT/'narration.txt').write_text('\n\n'.join(' '.join(s['lines']) for s in SCENES)+'\n')

def make_picture(s):
    target = ROOT/s['media']
    if 'photo' in s:
        image=ImageOps.exif_transpose(Image.open(SOURCE/s['photo'])).convert('RGB')
        image.thumbnail((1800,2400))
        image.save(target,quality=94)
        return
    # Re-encode only the chosen excerpt, preserving the entire portrait frame.
    # Playback changes keep demonstrations within this short overview.
    speed=s['source_duration']/s['visual_duration']
    vf=f'setpts=(PTS-STARTPTS)/{speed:.8f},scale=900:1600:force_original_aspect_ratio=decrease,pad=900:1600:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30'
    run(['ffmpeg','-v','error','-y','-threads','2','-ss',str(s['offset']),'-i',str(SOURCE/s['video']),'-t',str(s['source_duration']),'-an','-vf',vf,'-t',str(s['visual_duration']),'-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-threads','2','-movflags','+faststart',str(target)])
    print(f"Prepared {s['id']}: {s['duration']:.2f}s", flush=True)

if __name__ == '__main__':
    make_narration()
    make_timeline()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(make_picture, SCENES))
    print('Prepared 84-second edit.',flush=True)
