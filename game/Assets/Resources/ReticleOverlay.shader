Shader "Hidden/ReticleOverlay"
{
    Properties
    {
        _Color("Color", Color) = (1, 1, 1, 1)
    }

    SubShader
    {
        Tags { "RenderType"="Overlay" "IgnoreProjector"="True" }

        Pass
        {
            // Supported ShaderLab overlay states only:
            // visible above scene depth, no depth writes, no culling, no blending.
            ZTest Always
            ZWrite Off
            Cull Off
            Blend Off
            ColorMask RGBA
            Lighting Off

            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 2.0

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

            float4 frag(v2f i) : SV_Target
            {
                return _Color;
            }
            ENDCG
        }
    }

    FallBack Off
}