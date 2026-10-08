using System.Collections.Generic;
using UnityEngine;

namespace ChicagoGame { public sealed class PlayerPresentation : MonoBehaviour { Transform body, visual; Animation anim; string idleClip, walkClip, jogClip, aimClip, baseClip; float aimWeight, lastShot=-999f; Vector3 lastPos; bool posValid, upperActive, wasDead, wasVehicle; int lastRestarts=int.MinValue;

public static void Install(GameObject body){ if(body==null)return; Transform v=FindVisual(body.transform); if(v==null)return; Animation a=v.GetComponent<Animation>(); if(a==null)a=v.gameObject.AddComponent<Animation>(); a.playAutomatically=false; a.cullingType=AnimationCullingType.AlwaysAnimate; PlayerPresentation p=body.GetComponent<PlayerPresentation>(); if(p==null)p=body.AddComponent<PlayerPresentation>(); p.body=body.transform; p.visual=v; p.anim=a; p.Prepare(); FinishSurfaces(p.visual); }

static void FinishSurfaces(Transform root){
 if(root==null)return;
 var rs=root.GetComponentsInChildren<Renderer>(true);
 if(rs==null)return;
 var clones=new Dictionary<Material,Material>();
 for(int r=0;r<rs.Length;++r){
  var rd=rs[r]; if(rd==null)continue;
  var ms=rd.sharedMaterials; if(ms==null)continue;
  bool ch=false;
  for(int i=0;i<ms.Length;++i){
   var m=ms[i]; if(m==null)continue;
   string s=Strip(m.name);
   if(s!="jacketcharcoal"&&s!="jackethighlight"&&s!="jeansdarkblue"&&s!="jeansseam")continue;
   Material c;
   if(!clones.TryGetValue(m,out c)){
    c=new Material(m); c.name=m.name;
    Color col;
    if(s=="jacketcharcoal")col=new Color(0.46f,0.44f,0.4f,1f);
    else if(s=="jackethighlight")col=new Color(0.42f,0.42f,0.46f,1f);
    else if(s=="jeansdarkblue")col=new Color(0.40f,0.46f,0.62f,1f);
    else col=new Color(0.44f,0.50f,0.64f,1f);
    c.color=col;
    clones[m]=c;
   }
   if(ms[i]!=c){ms[i]=c;ch=true;}
  }
  if(ch)rd.sharedMaterials=ms;
 }
}

static Transform FindVisual(Transform r){ if(r==null)return null; var t=r.Find("PlayerVisual"); if(t!=null)return t; for(int i=0;i<r.childCount;++i){ var c=FindVisual(r.GetChild(i)); if(c!=null)return c; } return null; }

static Transform FindDescendant(Transform r,string w){ if(r==null)return null; if(Strip(r.name)==Strip(w))return r; for(int i=0;i<r.childCount;++i){ var c=FindDescendant(r.GetChild(i),w); if(c!=null)return c; } return null; }

void OnEnable(){ baseClip=null; posValid=false; aimWeight=0f; upperActive=false; lastShot=-999f; lastRestarts=LoopSignals.Restarts; wasDead=anim!=null&&DeathAuthority.IsDead; wasVehicle=false; if(anim!=null){ ReleaseUpper(); anim.enabled=!wasDead; } }

void Prepare(){ if(anim==null)return; anim.Stop(); anim.playAutomatically=false; lastRestarts=LoopSignals.Restarts; var loaded=Resources.LoadAll<AnimationClip>("Generated/player/scene"); if(loaded==null)return; var names=new List<string>(); foreach(var o in loaded){ var c=o as AnimationClip; if(c==null||c.length<0.1f||c.name.StartsWith("__preview__"))continue; c.legacy=true; c.wrapMode=c.name=="Board"?WrapMode.Once:WrapMode.Loop; if(anim.GetClip(c.name)==null)anim.AddClip(c,c.name);var st=anim[c.name];if(st!=null)st.wrapMode=c.wrapMode; if(!names.Contains(c.name))names.Add(c.name); } idleClip=Resolve(names,"Idle"); walkClip=Resolve(names,"Walk"); jogClip=Resolve(names,"Jog"); aimClip=Resolve(names,"Aim"); ConfigureLower(idleClip); ConfigureLower(walkClip); ConfigureLower(jogClip); ConfigureUpper(); }

static string Resolve(List<string> names,params string[] wanted){ for(int w=0;w<wanted.Length;++w){ var want=Strip(wanted[w]); for(int i=0;i<names.Count;++i)if(Strip(names[i])==want)return names[i]; } return null; }

static string Strip(string s){ return string.IsNullOrEmpty(s)?"":s.Replace("_","").Replace("-","").Replace(" ","").ToLowerInvariant(); }

void ConfigureLower(string n){ if(string.IsNullOrEmpty(n))return; var s=anim[n]; if(s==null)return; s.layer=0; s.weight=1f; s.enabled=false; }

void ConfigureUpper(){ if(string.IsNullOrEmpty(aimClip))return; var s=anim[aimClip]; if(s==null)return; s.layer=1; s.weight=0f; s.enabled=false; s.speed=1f;  Transform spine=FindDescendant(visual,"pivot_spine"); if(spine==null&&body!=null)spine=FindDescendant(body,"pivot_spine"); if(spine!=null)s.AddMixingTransform(spine,true); }

void ReleaseUpper(){ aimWeight=0f; upperActive=false; if(anim==null||string.IsNullOrEmpty(aimClip))return; var s=anim[aimClip]; if(s!=null){ s.weight=0f; s.enabled=false; } }

void FadeBase(string n){ if(anim==null||string.IsNullOrEmpty(n))return; var s=anim[n]; if(s==null)return; s.layer=0; if(!anim.IsPlaying(n)||!s.enabled||s.weight<=0.001f){ s.time=0f; anim.CrossFade(n,0.16f,PlayMode.StopSameLayer); } }

void Update(){ if(anim==null)return; bool dead=DeathAuthority.IsDead; string mode=LoopSignals.Mode; bool vehicle=false; if(!string.IsNullOrEmpty(mode)) vehicle=mode.IndexOf("Veh",System.StringComparison.OrdinalIgnoreCase)>=0||mode.IndexOf("Drive",System.StringComparison.OrdinalIgnoreCase)>=0||mode.IndexOf("Car",System.StringComparison.OrdinalIgnoreCase)>=0;
 if(LoopSignals.Restarts!=lastRestarts){ lastRestarts=LoopSignals.Restarts; anim.Stop(); baseClip=null; posValid=false; lastShot=-999f; ReleaseUpper(); if(!dead&&!vehicle)anim.enabled=true; }
 if(dead){ if(!wasDead){ wasDead=true; baseClip=null; posValid=false; lastShot=-999f; ReleaseUpper(); } anim.enabled=false; return; }
 if(wasDead){ wasDead=false; baseClip=null; posValid=false; lastShot=-999f; ReleaseUpper(); anim.enabled=true; }
 if(vehicle){ if(!wasVehicle){ wasVehicle=true; anim.Stop(); baseClip=null; posValid=false; lastShot=-999f; ReleaseUpper(); } anim.enabled=false; return; }
 if(wasVehicle){ wasVehicle=false; baseClip=null; posValid=false; lastShot=-999f; ReleaseUpper(); anim.enabled=true; }
 if(visual==null||!visual.gameObject.activeInHierarchy){ if(baseClip!=null||upperActive||posValid){ baseClip=null; posValid=false; ReleaseUpper(); } lastShot=-999f; return; }
 if(!anim.enabled)anim.enabled=true; if(body==null){ posValid=false; return; }
 Vector3 pos=body.position; float dt=Time.deltaTime,speed=0f; if(posValid&&dt>0.0001f){ Vector2 d=new Vector2(pos.x-lastPos.x,pos.z-lastPos.z); speed=d.magnitude/dt; if(speed>18f)speed=0f; } lastPos=pos; posValid=true;
 if(LoopInput.Pressed(KeyCode.Mouse0))lastShot=Time.time; bool aiming=LoopInput.Held(KeyCode.Mouse1)||Time.time-lastShot<0.45f; bool moving=speed>0.35f; bool shift=LoopInput.Held(KeyCode.LeftShift);
 string wantBase=moving?(shift&&!string.IsNullOrEmpty(jogClip)?jogClip:(!string.IsNullOrEmpty(walkClip)?walkClip:idleClip)):idleClip;
 if(!string.IsNullOrEmpty(wantBase)){ var wantState=anim[wantBase]; if(wantState!=null&&(wantBase!=baseClip||!anim.IsPlaying(wantBase)||(dt>0f&&(!wantState.enabled||wantState.weight<=0.001f)))){ FadeBase(wantBase); baseClip=wantBase; } }
 float cycle=moving?Mathf.Clamp(speed/3.2f,0.55f,1.45f):1f; if(baseClip==jogClip)cycle*=0.78f; if(cycle<0.45f)cycle=0.45f;
 if(!string.IsNullOrEmpty(baseClip)){ var bs=anim[baseClip]; if(bs!=null){ bs.layer=0; if(Mathf.Abs(bs.speed-cycle)>0.001f)bs.speed=cycle; } }
 if(string.IsNullOrEmpty(aimClip))return; aimWeight=Mathf.MoveTowards(aimWeight,aiming?1f:0f,dt*4.5f); var us=anim[aimClip]; if(us==null)return; us.layer=1; if(aiming||aimWeight>0f){ if(!upperActive||!us.enabled){ us.time=0f; us.speed=moving?cycle:1f; anim.Play(aimClip,PlayMode.StopSameLayer); upperActive=true; } us.weight=aimWeight; float uSpeed=moving?cycle:1f; if(Mathf.Abs(us.speed-uSpeed)>0.001f)us.speed=uSpeed; } else { us.weight=0f; if(us.enabled)us.enabled=false; upperActive=false; } }
}}
