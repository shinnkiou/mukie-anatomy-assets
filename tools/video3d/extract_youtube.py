#!/usr/bin/env python3
"""Free-first YouTube research extractor: captions -> transcript -> key frames."""
from pathlib import Path
import argparse, json, re, subprocess, sys

KEYWORDS=['Blender','ブレンダー','MCP','プロンプト','生成','モデル','モデリング','リグ','リギング','アニメ','アニメーション','マテリアル','テクスチャ','レンダー','エラー','修正','設定','インストール']

def run(cmd,cwd=None,allow_fail=False):
    p=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True)
    if p.returncode and not allow_fail: raise RuntimeError(f"command failed {p.returncode}: {' '.join(map(str,cmd))}\n{p.stderr[-4000:]}")
    return p

def ensure_tools():
    for module,pkg in [('yt_dlp','yt-dlp'),('imageio_ffmpeg','imageio-ffmpeg'),('PIL','pillow')]:
        try: __import__(module)
        except Exception: run([sys.executable,'-m','pip','install','--user',pkg])

def ts(s):
    m=int(s//60); return f'{m:02d}:{s-m*60:05.2f}'

def parse_json3(path):
    d=json.loads(Path(path).read_text(encoding='utf-8')); out=[]; last=''
    for ev in d.get('events',[]):
        if 'segs' not in ev: continue
        text=re.sub(r'\s+',' ',''.join(x.get('utf8','') for x in ev['segs']).replace('\n',' ')).strip()
        if not text or text==last: continue
        start=ev.get('tStartMs',0)/1000; dur=ev.get('dDurationMs',0)/1000
        out.append({'start_sec':start,'end_sec':start+dur,'timestamp':ts(start),'text':text}); last=text
    return out

def select_events(rows,max_frames):
    selected=[]
    for r in rows:
        hits=[k for k in KEYWORDS if k.lower() in r['text'].lower()]
        if not hits: continue
        score=min(5,len(hits))
        if selected and r['start_sec']-selected[-1]['row']['start_sec']<20:
            if score>selected[-1]['score']: selected[-1]={'score':score,'row':r,'keywords':hits}
        else: selected.append({'score':score,'row':r,'keywords':hits})
    if len(selected)>max_frames:
        ids=[round(i*(len(selected)-1)/(max_frames-1)) for i in range(max_frames)]
        selected=[selected[i] for i in sorted(set(ids))]
    return selected

def contact_sheet(files,dest):
    from PIL import Image,ImageDraw
    cards=[]
    for p in files:
        im=Image.open(p).convert('RGB'); im.thumbnail((480,270)); c=Image.new('RGB',(500,310),'white'); c.paste(im,((500-im.width)//2,8)); ImageDraw.Draw(c).text((12,285),p.stem,fill='black'); cards.append(c)
    out=Image.new('RGB',(1000,310*max(1,(len(cards)+1)//2)),(225,225,225))
    for i,c in enumerate(cards): out.paste(c,((i%2)*500,(i//2)*310))
    out.save(dest,quality=90)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('url'); ap.add_argument('--out',default='video3d_output'); ap.add_argument('--max-frames',type=int,default=12); ap.add_argument('--video-format',default='134'); a=ap.parse_args()
    ensure_tools(); out=Path(a.out).resolve(); out.mkdir(parents=True,exist_ok=True); errors=[]
    try:
        p=run([sys.executable,'-m','yt_dlp','--js-runtimes','node','--skip-download','--write-info-json','--write-auto-subs','--sub-langs','ja-orig,ja','--sub-format','json3','-o','%(id)s.%(ext)s',a.url],cwd=out,allow_fail=True)
        (out/'yt_caption.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
        info_files=list(out.glob('*.info.json'))
        if not info_files: raise RuntimeError('VIDEO_INFO_NOT_FOUND')
        info=json.loads(info_files[0].read_text(encoding='utf-8')); vid=info.get('id')
        caps=list(out.glob(f'{vid}.ja-orig.json3')) or list(out.glob(f'{vid}.ja*.json3'))
        if not caps: raise RuntimeError('JAPANESE_CAPTION_NOT_FOUND')
        rows=parse_json3(caps[0]); events=select_events(rows,a.max_frames)
        (out/'TRANSCRIPT_RAW.txt').write_text('\n'.join(r['text'] for r in rows),encoding='utf-8')
        (out/'TRANSCRIPT_TIMESTAMPED.txt').write_text('\n'.join(f"[{r['timestamp']}] {r['text']}" for r in rows),encoding='utf-8')
        (out/'TRANSCRIPT_STRUCTURED.json').write_text(json.dumps({'video':{'id':vid,'title':info.get('title'),'duration':info.get('duration'),'channel':info.get('channel'),'upload_date':info.get('upload_date')},'transcript':rows,'screenshot_candidates':events},ensure_ascii=False,indent=2),encoding='utf-8')
        video=out/f'{vid}_preview.mp4'; p=run([sys.executable,'-m','yt_dlp','--js-runtimes','node','-f',a.video_format,'-o',str(video),a.url],cwd=out,allow_fail=True); (out/'yt_video.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
        if video.exists():
            import imageio_ffmpeg
            ff=imageio_ffmpeg.get_ffmpeg_exe(); sd=out/'screenshots'; sd.mkdir(exist_ok=True); files=[]; index=[]
            for i,e in enumerate(events,1):
                sec=e['row']['start_sec']; name=f'{i:02d}_{int(sec//60):02d}m{int(sec%60):02d}s.jpg'; dest=sd/name
                q=run([ff,'-hide_banner','-loglevel','error','-ss',str(sec),'-i',str(video),'-frames:v','1','-q:v','2',str(dest),'-y'],allow_fail=True)
                if dest.exists() and dest.stat().st_size>1000: files.append(dest); index.append({'timestamp_sec':sec,'timestamp_text':ts(sec),'reason':e['keywords'],'transcript_excerpt':e['row']['text'],'filename':name})
                else: errors.append({'stage':'screenshot','time':sec,'stderr':q.stderr[-800:]})
            (sd/'SCREENSHOT_INDEX.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
            if files: contact_sheet(files,sd/'CONTACT_SHEET.jpg')
        else: errors.append({'stage':'video_download','message':'caption outputs completed; preview unavailable'})
    except Exception as e: errors.append({'stage':'pipeline','message':str(e)})
    (out/'ERROR_REPORT.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(out),'errors':len(errors)},ensure_ascii=False)); return 0 if not errors else 2

if __name__=='__main__': raise SystemExit(main())
