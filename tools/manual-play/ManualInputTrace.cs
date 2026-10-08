// Cloud-authored standalone presentation/diagnostic infrastructure; original material, MIT.
using System;
using System.IO;
using System.Collections.Generic;
using UnityEngine;
public sealed class ManualInputTrace : MonoBehaviour {
 [Serializable] public class Row {
  public float time,health; public bool focused,replay,dead; public int shots,restarts;
  public string[] held,pressed; public float[] position,mouse;
 }
 string output; float next,started;
 readonly KeyCode[] keys = {KeyCode.W,KeyCode.A,KeyCode.S,KeyCode.D,KeyCode.R,KeyCode.E,KeyCode.F,KeyCode.Mouse0,KeyCode.Mouse1};
 [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)] static void Install() {
  var a=Environment.GetCommandLineArgs(); int i=Array.IndexOf(a,"--manual-input-log");
  if(i<0 || i+1>=a.Length) return;
  var go=new GameObject("Temporary manual-input diagnostic");
  var t=go.AddComponent<ManualInputTrace>(); t.output=a[i+1]; t.started=Time.realtimeSinceStartup;
 }
 void Update() {
  if(output==null || Time.realtimeSinceStartup-started>180) return;
  var held=new List<string>(); var pressed=new List<string>();
  foreach(var k in keys) { if(Input.GetKey(k))held.Add(k.ToString()); if(Input.GetKeyDown(k))pressed.Add(k.ToString()); }
  if(Time.realtimeSinceStartup<next && pressed.Count==0) return;
  next=Time.realtimeSinceStartup+.2f;
  var p=LoopSignals.Player; var m=Input.mousePosition;
  var row=new Row {time=Time.realtimeSinceStartup,focused=Application.isFocused,replay=LoopInput.Replay!=null,
   held=held.ToArray(),pressed=pressed.ToArray(),health=LoopSignals.Health,shots=LoopSignals.Shots,restarts=LoopSignals.Restarts,
   dead=ChicagoGame.DeathAuthority.IsDead,position=p==null?new float[0]:new[]{p.position.x,p.position.y,p.position.z},mouse=new[]{m.x,m.y}};
  File.AppendAllText(output,JsonUtility.ToJson(row)+"\n");
 }
}
