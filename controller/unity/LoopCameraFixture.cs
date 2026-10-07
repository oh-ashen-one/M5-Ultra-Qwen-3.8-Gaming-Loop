// Disposable diagnostic wall. Never moves actors/cameras or changes shipped source.
using UnityEngine;

public class LoopCameraFixture : MonoBehaviour
{
    public static Collider Wall;
    public static string Phase="ordinary";
    int previous=-1;
    void Update() {
        float t=LoopInput.Elapsed;int phase=t<4?0:t<8?1:t<12?2:t<16?3:4;
        if(phase==previous)return;previous=phase;
        if(phase==0 || phase==4) {
            if(Wall!=null)Wall.gameObject.SetActive(false);
            Phase=phase==0?"ordinary":"restored";return;
        }
        Transform target;Vector3 offset;
        if(!LoopCameraObservation.Rig(out target,out offset))throw new System.Exception("Camera diagnostic requires the actual Follow rig");
        var dir=(Quaternion.Euler(0,target.eulerAngles.y,0)*offset).normalized;
        var horizontal=new Vector3(dir.x,0,dir.z).normalized;
        float distance=phase==1?.65f:phase==2?3f:offset.magnitude-.65f;
        var point=target.position+Vector3.up*1.25f+dir*distance;
        if(Wall==null) {
            var wall=GameObject.CreatePrimitive(PrimitiveType.Cube);wall.name="CameraClearanceWall";
            Wall=wall.GetComponent<Collider>();
            var mat=new Material(Shader.Find("Standard"));mat.color=new Color(.32f,.37f,.43f);
            wall.GetComponent<Renderer>().sharedMaterial=mat;
        }
        Wall.gameObject.SetActive(true);Wall.transform.position=new Vector3(point.x,target.position.y+2.6f,point.z)+horizontal*.05f;
        Wall.transform.rotation=Quaternion.LookRotation(horizontal,Vector3.up);Wall.transform.localScale=new Vector3(12,6,.1f);
        Phase=phase==1?"near":phase==2?"middle":"endpoint";
        Physics.SyncTransforms();
    }
}
