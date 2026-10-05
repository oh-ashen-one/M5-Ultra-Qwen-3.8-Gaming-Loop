# Unity installation readiness — 2026-10-05

**Later verified update:** the owner installed Unity **6000.6.4f1 ARM64** and an active local license. Actual import/C# compile/Metal render and Qwen image recognition now pass. See [post-reboot qualification](../diagnostics/unity-2026-10-04/README.md) for current state and remaining SSH CLI/Pipeline distinctions. The original installation record below is historical.

The owner approved official Unity Hub and a compatible stable LTS Apple Silicon editor on the M5, with minimal native macOS components. **Hub is installed/open; the editor is not installed and license activation is pending. Game generation remains held.** No subscription, purchase, credentials, agreement acceptance or security override was performed.

[Installation evidence](UNITY-INSTALL-EVIDENCE.json) records the actual application, package assessment and final resident-model snapshot.

## Verified selection and actual state

| Component | Verified state |
| --- | --- |
| M5 | Apple M5 Ultra / Mac17,15, 256 GB / 80 GPU, macOS 27.0.1; Qwen remains loaded and idle |
| Hub | **3.22.2**, stable Apple Silicon `arm64`, actual location `/Applications/Unity Hub.app`; opened successfully and an actual visible Hub window was observed |
| Hub verification | Official SHA-512 and 166,530,334-byte size matched; app signature/deep validation and Gatekeeper assessment passed as **Notarized Developer ID**; disk image has no Software License Agreement prompt |
| Selected editor | **Unity 6.3 LTS 6000.3.25f1**, changeset `e1dba0a9aba4`, released September 24, 2026; official macOS ARM64 package downloaded on M5 |
| Editor verification | Official MD5 and 5,186,642,467-byte size matched; Apple-issued Unity Developer ID Installer signature valid. Gatekeeper package assessment returned **rejected / Unnotarized Developer ID**, so no manual install was attempted |
| Installer privilege | Official package metadata declares `auth="Root"`; the current remote session has no passwordless administrator authorization |
| Optional modules | None installed/selected. Base native macOS/Mono support is the initial target; no Android, iOS, Windows, WebGL, dedicated-server, IDE or IL2CPP module |
| Rosetta | No existing Rosetta installation receipt was found. Unity's editor requirements list Rosetta 2 even for Apple Silicon; check/resolve with the owner before editor qualification rather than silently installing or accepting Apple's license |
| Hub CLI | Read-only deprecated `-- --headless help --errors` did not return within 45 seconds. No editor-install command was executed; use the supported visible Hub workflow for user-controlled sign-in/approval |

Hub installer SHA-256: `5a2212142c0ee33d4493e710c0aa913853ac9f5120714f279e0dbd624d843eaf`.

Editor package SHA-256: `a1f94dff7106242ff2bf648edc0b039bfc5f5160b6115e9d9de8a52113b8d744`.

The [official Hub manifest](https://public-cdn.cloud.unity3d.com/hub/prod/latest-mac.yml), [editor release and ARM64 installer](https://unity.com/releases/editor/whats-new/6000.3.25f1), and [Unity support policy](https://unity.com/releases/unity-6/support) support the selected versions. The latest manifest can change; the above versions/hashes describe this dated installation.

## Compatibility checked before runtime

The M5 exceeds the published hardware and macOS minimums in the [Unity 6.3 requirements](https://docs.unity3d.com/6000.3/Documentation/Manual/system-requirements.html). Functional compatibility on this actual newer macOS still needs licensed execution. Native C# compilation and automation use the editor's supported `-batchmode`, `-projectPath`, `-executeMethod`, explicit log and exit-status path; [CLI reference](https://docs.unity3d.com/6000.3/Documentation/Manual/EditorCommandLineArguments.html).

For the pending diagnostic, import the original Blender FBX through Unity's native [Model Importer](https://docs.unity3d.com/6000.3/Documentation/Manual/FBXImporter-Model.html). GLB needs an explicitly selected compatible importer. Perform import/compile without graphics, then initialize actual Metal rendering in a separate serial capture stage under shared admission. A `-nographics` run cannot produce rendered evidence. The Built-in pipeline can provide a minimal native diagnostic without extra package installation; choosing it for a fixture does not finalize the game's render pipeline. Qualify any later URP/HDRP choice separately.

No Unity import, C# compile, rendered frame, game build or Unity-to-Qwen vision round-trip is claimed yet. Blender/MCP/framework pins remain separate candidates; Hub installation does not qualify them.

## Owner steps in Screen Sharing

1. Open the installed **Unity Hub** on the M5 and choose **Sign in**. Enter credentials only in Unity's own window/browser and allow its callback to return to Hub. No credentials belong in chat.
2. Review any presented agreement yourself. The decision is whether to accept the [Unity Terms of Service](https://unity.com/legal/terms-of-service) and applicable [Editor Software Terms](https://unity.com/legal/editor-terms-of-service/software); this execution lead has accepted neither. License terms/eligibility and any Apple Rosetta agreement remain the owner's decision.
3. In **Settings → Licenses**, confirm an appropriate existing/eligible license is active. Hub may activate an eligible existing license upon sign-in; use Unity's [license-management instructions](https://docs.unity.com/en-us/hub/manage-license). Do not purchase a plan or assume Personal eligibility.
4. Use **Installs → Install Editor → Unity 6.3 LTS 6000.3.25f1 → Apple Silicon**, with optional modules unchecked. Follow the [supported Hub install flow](https://docs.unity.com/en-us/hub/add-editor) and handle administrator/permission prompts locally. Do not weaken security controls if installation remains rejected; report the exact prompt. The ordinary Hub default editor location would be `/Applications/Unity/Hub/Editor/6000.3.25f1/Unity.app`; that location is **not currently installed**.
5. Report that sign-in/license and editor installation are complete, or the precise remaining UI blocker. Then resume only the already authorized disposable Unity import/compile/render and fresh Qwen image recognition check.

Official installers are staged privately on the M5; their operational paths and private logs are excluded from Git. Hub remains open for the owner. The Qwen resident supervisor and other workloads are preserved; no authentication store, firewall, Screen Sharing or model configuration was changed.
