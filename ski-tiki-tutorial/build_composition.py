"""Build the editable HyperFrames HTML from the measured narration timeline."""
from pathlib import Path
import html
import json

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / 'timeline.json').read_text())
scenes = data['scenes']
esc = html.escape
parts=[]
for i,s in enumerate(scenes):
    attributes=f'id="media-{s["id"]}" class="clip media" data-start="{s["start"]:.6f}" data-duration="{s["visual_duration"]:.6f}" data-track-index="{i%2}"'
    if 'photo' in s:
        media=f'<img {attributes} src="{s["media"]}" alt="{esc(s["title"])}">'
    else:
        media=f'<video {attributes} src="{s["media"]}" muted playsinline preload="auto"></video>'
    count='THE SHORT VERSION' if i==0 else ('MADE BY HAND' if i==len(scenes)-1 else f'STEP {i:02d} OF 07')
    parts.append(f'''<section id="scene-{s['id']}" class="scene {'first' if i==0 else ''}" style="z-index:{i+1}" aria-label="{esc(s['title'])}">
      <div class="scene-content">
        <div class="masthead" data-layout-allow-overlap><span>THE LODGE WORKSHOP</span><span class="edition">SKI / TIKI</span></div>
        <header class="heading" data-layout-allow-overlap><p class="eyebrow">{esc(s['number'])}</p><h1>{esc(s['title'])}</h1></header>
        <div class="stage" data-layout-allow-overflow>
          <div class="matte-note left" data-layout-ignore>CARVED WITH CHARACTER</div>
          {media}
          <div class="matte-note right" data-layout-ignore>{count}</div>
        </div>
        <p class="note" data-layout-allow-overlap>{esc(s['note'])}</p>
        <div class="caption-space" aria-hidden="true"></div>
        <footer data-layout-allow-overlap><span>ONE LOG. A LOT OF ATTITUDE.</span><span>{i+1:02d} / 09</span></footer>
      </div>
    </section>''')
captions=[]
for i,c in enumerate(data['captions']):
    captions.append(f'<div id="caption-{i}" class="clip caption" data-start="{c["start"]:.6f}" data-duration="{c["end"]-c["start"]:.6f}" data-track-index="8"><p>{esc(c["text"])}</p></div>')
markup='\n'.join(parts)
caption_markup='\n'.join(captions)
script=f'''const SCENES = {json.dumps(scenes)};
const CAPTIONS = {json.dumps(data['captions'])};
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{paused:true}});
SCENES.forEach((s,i) => {{
  const id = '#scene-' + s.id;
  const t=s.start;
  // The crossfade is the scene handoff; there are no earlier exit tweens.
  if(i>0) {{
    tl.to('#scene-'+SCENES[i-1].id,{{opacity:0,duration:.4,ease:'sine.inOut'}},t);
    tl.fromTo(id,{{opacity:0}},{{opacity:1,duration:.4,ease:'sine.inOut'}},t);
  }}
  tl.from(id+' .masthead',{{y:-8,opacity:0,duration:.42,ease:'power2.out'}},t+.12);
  tl.from(id+' .eyebrow',{{x:-20,opacity:0,duration:.45,ease:'power3.out'}},t+.18);
  tl.from(id+' h1',{{y:22,opacity:0,duration:.62,ease:'back.out(1.08)'}},t+.24);
  tl.from(id+' .stage',{{y:12,opacity:i===0?1:0,duration:.48,ease:'sine.out'}},t+.1);
  tl.from(id+' .note',{{x:16,opacity:0,duration:.5,ease:'power2.out'}},t+.3);
  tl.from(id+' footer',{{opacity:0,duration:.45,ease:'sine.out'}},t+.4);
  if(s.photo) {{
    // A slow push on a still keeps the opening and final reveal alive.
    tl.fromTo('#media-'+s.id,{{scale:1}},{{scale:1.045,duration:s.visual_duration,ease:'none'}},t);
  }}
}});
CAPTIONS.forEach((c,i)=>{{
  tl.from('#caption-'+i,{{y:8,opacity:0,duration:.2,ease:'power2.out'}},c.start);
  tl.set('#caption-'+i,{{opacity:0}},c.end);
}});
tl.from('#progress',{{scaleX:0,duration:84,ease:'none',transformOrigin:'left center'}},0);
// Only the final scene fades out, leaving a clean cream end frame.
tl.to('#scene-reveal',{{opacity:0,duration:.6,ease:'sine.inOut'}},83.4);
window.__timelines['ski-tiki']=tl;
tl.seek(0);
'''
document=f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1080, height=1920">
  <title>Carve a Ski Tiki — The Lodge Workshop</title>
  <script src="assets/gsap.min.js"></script>
  <style>
    @font-face{{font-family:'Bree Serif';font-weight:400;src:url('assets/fonts/BreeSerif-Regular.ttf') format('truetype')}}
    @font-face{{font-family:'IBM Plex Mono';font-weight:400;src:url('assets/fonts/IBMPlexMono-Regular.ttf') format('truetype')}}
    @font-face{{font-family:'IBM Plex Mono';font-weight:600;src:url('assets/fonts/IBMPlexMono-SemiBold.ttf') format('truetype')}}
    *{{box-sizing:border-box;margin:0;padding:0}}
    html,body{{width:1080px;height:1920px;overflow:hidden;background:#F4EBDD}}
    #root{{position:relative;width:1080px;height:1920px;color:#38271E;font-family:'IBM Plex Mono',monospace;overflow:hidden}}
    .scene{{position:absolute;inset:0;width:1080px;height:1920px;background:#F4EBDD;opacity:0}}
    .scene.first{{opacity:1}}
    .scene-content{{width:100%;height:100%;padding:42px 52px 42px;display:flex;flex-direction:column;gap:18px;box-sizing:border-box}}
    .masthead{{display:flex;justify-content:space-between;align-items:center;flex:0 0 44px;font-size:28px;font-weight:600;letter-spacing:.06em;color:#345447;border-bottom:2px solid #D9C3A4;padding-bottom:10px}}
    .edition{{color:#A84623;letter-spacing:.08em}}
    .heading{{height:182px;flex:0 0 182px;display:flex;flex-direction:column;gap:8px;justify-content:center}}
    .eyebrow{{color:#A84623;font-size:28px;font-weight:600;letter-spacing:.1em}}
    h1{{font-family:'Bree Serif',serif;font-size:84px;font-weight:400;line-height:1.02;letter-spacing:-.025em;max-width:970px}}
    #scene-intro h1{{font-size:100px}}
    #scene-reveal h1{{font-size:104px}}
    .stage{{position:relative;flex:1 1 auto;min-height:0;width:100%;overflow:hidden;background:#D9C3A4;border:2px solid #38271E;border-radius:8px;display:flex;align-items:center;justify-content:center}}
    .media{{display:block;width:100%;height:100%;object-fit:contain;position:absolute;inset:0}}
    .matte-note{{position:absolute;top:50%;font-size:17px;font-weight:600;letter-spacing:.16em;color:#38271E;z-index:3;writing-mode:vertical-rl;transform:translateY(-50%)}}
    .matte-note.left{{left:18px;transform:translateY(-50%) rotate(180deg)}}
    .matte-note.right{{right:18px}}
    .note{{flex:0 0 76px;display:flex;align-items:center;justify-content:center;text-align:center;color:#345447;font-size:28px;line-height:1.3;font-weight:600;max-width:976px}}
    .caption-space{{flex:0 0 150px}}
    footer{{height:36px;flex:0 0 36px;display:flex;align-items:center;justify-content:space-between;font-size:28px;letter-spacing:.03em;font-weight:600;color:#A84623}}
    .caption{{position:absolute;left:62px;right:62px;bottom:94px;height:150px;z-index:30;display:flex;align-items:center;justify-content:center;text-align:center;border-top:2px solid #D9C3A4;padding:15px 18px 4px;color:#38271E;background:#F4EBDD}}
    .caption p{{font-size:36px;line-height:1.28;font-weight:400;max-width:920px}}
    #progress{{position:absolute;left:0;bottom:0;width:1080px;height:8px;background:#A84623;z-index:40}}
  </style>
</head>
<body>
  <div id="root" data-composition-id="ski-tiki" data-start="0" data-duration="84" data-width="1080" data-height="1920" data-fps="30">
    {markup}
    {caption_markup}
    <div id="progress" data-layout-ignore></div>
    <audio id="narration" data-start="0" data-duration="84" data-track-index="12" src="assets/narration.m4a" data-volume="1"></audio>
  </div>
  <script>{script}</script>
</body>
</html>
'''
(ROOT/'index.html').write_text(document)
print('Built 84-second composition with 9 scenes and',len(captions),'timed captions.')
