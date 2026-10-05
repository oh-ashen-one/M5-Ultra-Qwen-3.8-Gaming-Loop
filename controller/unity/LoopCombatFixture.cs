// Disposable acceptance obstacle, never a shipped asset or source of gameplay success.
// Uses the same ordinary input in open/walled runs; never moves actors or changes HP.
using System.Linq;
using UnityEngine;

public class LoopCombatFixture : MonoBehaviour
{
    bool made;
    void Update()
    {
        if(made || LoopInput.Replay==null || LoopInput.Elapsed<7f) return;
        if(LoopInput.Replay.fixture=="combat-near-cover") {
            var camera=Camera.main;if(camera==null) throw new System.Exception("Near cover requires a real camera");
            var cover=GameObject.CreatePrimitive(PrimitiveType.Cube);cover.name="CombatNearCover";
            cover.transform.position=camera.transform.position+camera.transform.forward*.35f;
            cover.transform.rotation=camera.transform.rotation;
            cover.transform.localScale=new Vector3(3f,3f,.25f);
            var shade=new Material(Shader.Find("Standard"));shade.color=new Color(.30f,.35f,.40f);
            cover.GetComponent<Renderer>().sharedMaterial=shade;
            Physics.SyncTransforms();made=true;return;
        }
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
