// Disposable acceptance obstacle, never a shipped asset or source of gameplay success.
// Uses the same ordinary input in open/walled runs; never moves actors or changes HP.
using System.Linq;
using UnityEngine;

[DefaultExecutionOrder(-31500)]
public class LoopCombatFixture : MonoBehaviour
{
    bool made;
    GameObject nearCover;
    void Update()
    {
        if(LoopInput.Replay==null || LoopInput.Elapsed<7f) return;
        if(LoopInput.Replay.fixture=="combat-near-cover") {
            // Place real near-origin cover at the ordinary shot edge, before the
            // independent aim observer and gameplay Update. A camera may safely
            // evade a static edge during the old 0.15s setup delay; that no longer
            // exercises a blocked shot. Never move the camera, rivals or HP.
            if(!LoopInput.Pressed(KeyCode.Mouse0))return;
            var camera=Camera.main;if(camera==null) throw new System.Exception("Near cover requires a real camera");
            if(nearCover==null) {
                nearCover=GameObject.CreatePrimitive(PrimitiveType.Cube);nearCover.name="CombatNearCover";
                var shade=new Material(Shader.Find("Standard"));shade.color=new Color(.30f,.35f,.40f);
                nearCover.GetComponent<Renderer>().sharedMaterial=shade;
            }
            var cover=nearCover;
            // A visible cover edge crosses the center ray while the scene remains
            // readable beside it. Still overlaps the former 0.85 m cast origin.
            cover.transform.position=camera.transform.position+camera.transform.forward*.70f+camera.transform.right*.39f;
            cover.transform.rotation=camera.transform.rotation;
            cover.transform.localScale=new Vector3(.8f,1.6f,.06f);
            Physics.SyncTransforms();return;
        }
        if(made)return;
        if(LoopInput.Replay.fixture!="combat-wall")return;
        var rival=Object.FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None)
            .FirstOrDefault(m=>m.GetType().Name=="RivalAgent");
        var actor=LoopSignals.Player;
        if(rival==null || actor==null) throw new System.Exception("Wall fixture requires real combatants");
        var delta=actor.position-rival.transform.position;delta.y=0;
        if(delta.magnitude<1f) throw new System.Exception("Wall fixture requires room between combatants");
        var wall=GameObject.CreatePrimitive(PrimitiveType.Cube);wall.name="CombatValidationWall";
        var center=(actor.position+rival.transform.position)*.5f;center.y=1.5f;
        wall.transform.position=center;wall.transform.rotation=Quaternion.LookRotation(delta.normalized,Vector3.up);
        wall.transform.localScale=new Vector3(8f,3f,.25f);
        var material=new Material(Shader.Find("Standard"));material.color=new Color(.25f,.30f,.35f);
        wall.GetComponent<Renderer>().sharedMaterial=material;
        Physics.SyncTransforms();made=true;
    }
}
