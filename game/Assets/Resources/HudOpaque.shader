Shader "Chicago/HudOpaque"
{
    Properties
    {
        _Color("Color", Color) = (.06, .07, .085, 1)
    }
    SubShader
    {
        Tags { "Queue" = "2999" }
        Pass
        {
            ZTest Always
            ZWrite Off
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            float4 _Color;

            struct appdata
            {
                float4 vertex : POSITION;
            };

            struct v2f
            {
                float4 pos : SV_POSITION;
            };

            v2f vert(appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                return fixed4(_Color.rgb, 1);
            }
            ENDCG
        }
    }
}