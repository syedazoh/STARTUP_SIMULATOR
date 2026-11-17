"""Package the synthetic screen recording as phone-compatible public media."""
from pathlib import Path
import json,shutil,subprocess,textwrap
ROOT=Path(__file__).resolve().parents[2]
WORK=Path('/tmp/startup-walkthrough')
source=WORK/'quick-start.webm'
if not source.exists():raise SystemExit('Run record.py against a fresh localhost fixture first.')
mp4=WORK/'quick-start.mp4'
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(source),'-an','-r','20','-c:v','libx264','-preset','fast','-crf','28','-profile:v','main','-pix_fmt','yuv420p','-movflags','+faststart',str(mp4)],check=True)
duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(mp4)],text=True))
chapters=json.loads((WORK/'chapters.json').read_text())
def stamp(seconds):
 ms=round(seconds*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
 return f'{h:02}:{m:02}:{s:02}.{ms:03}'
vtt=['WEBVTT','']
for i,chapter in enumerate(chapters):
 end=chapters[i+1]['start'] if i+1<len(chapters) else duration
 vtt.extend([str(i+1),f"{stamp(chapter['start'])} --> {stamp(end)} line:75% position:50% size:90%",textwrap.fill(chapter['caption'],width=70),''])
(WORK/'quick-start.vtt').write_text('\n'.join(vtt),encoding='utf-8')
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss','5','-i',str(mp4),'-frames:v','1','-q:v','3',str(WORK/'quick-start-poster.jpg')],check=True)
for folder in [ROOT/'frontend/public/media',ROOT/'web/public/media']:
 folder.mkdir(parents=True,exist_ok=True)
 folder.chmod(0o755)
 for filename in ['quick-start.mp4','quick-start.vtt','quick-start-poster.jpg']:
  target=folder/filename
  shutil.copyfile(WORK/filename,target)
  target.chmod(0o644)
print(f'Packaged {duration:.1f}s captioned MP4, {mp4.stat().st_size/1024/1024:.2f} MiB, in both app public/media folders.')
