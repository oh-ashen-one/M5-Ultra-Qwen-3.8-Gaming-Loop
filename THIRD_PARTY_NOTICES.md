# Third-party notices

## Current distribution

Original documentation and the source-integrity validator are covered by [LICENSE](LICENSE). Selected MIT source files/excerpts are distributed under their preserved upstream notices. The [import manifest](reference/IMPORT-MANIFEST.json) records exact commits, files, hashes and modifications, and [reference notes](reference/README.md) describe all integration gaps. **No third-party models, art, audio, fonts, demo scenes or assets are distributed.**

Full upstream license texts are retained alongside each imported component:

- [Ralph diagnostics](reference/vendor/ralph-diagnostics/LICENSE.upstream.txt): copyright 2026 oh-ashen-one.
- [Grindline input excerpt](reference/vendor/grindline-input/LICENSE.upstream.txt): copyright 2026 Hari (@oh-ashen-one); original asset notes retained, assets excluded.
- [Space-salvage verification excerpts](reference/vendor/space-verification/LICENSE.upstream.txt): copyright 2026 Hari (@oh-ashen-one); original asset notes retained, assets excluded.
- [GDQuest camera](reference/vendor/gdquest-camera/LICENSE.upstream.txt): copyright 2023-present GDQuest; imported code is MIT. Full upstream dual-license text retained; CC BY-NC-SA art excluded.
- [Easy Vehicle Physics](reference/vendor/easy-vehicle-physics/LICENSE.upstream.txt): David Shoemaker (2024), Dechode (2021), Baron Wittman (2024); lineage comments retained.

## Research attribution

Prior-loop ideas and static lessons are attributed to the public user repositories in [Prior attempts](docs/PRIOR-ATTEMPTS.md) and [Reuse catalog](docs/REUSE-CATALOG.md): `ralph-loop-playbook`, `slop-of-tsushima-qwen`, `grindline`, and `space-salvage`. Ralph's iterative pattern traces to Geoffrey Huntley and [snarktank/ralph](https://github.com/snarktank/ralph); the playbook also credits [gillworks/red-sands](https://github.com/gillworks/red-sands) for critique lineage and [achimala/TheLongSilence](https://github.com/achimala/TheLongSilence) for capture/metrics patterns. These are attributions, not imported dependencies.

The catalog attributes external tool and gameplay candidates to their respective upstream authors through direct repository links. No endorsement or compatibility certification is implied.

## Component license record

| Material/candidate | Observed license boundary | Current distribution |
| --- | --- | --- |
| Original project documentation | MIT | Included |
| `ralph-loop-playbook` | MIT | Exact stdlib diagnostic script; other material linked only |
| `slop-of-tsushima-qwen` | Repository MIT; inspect asset-specific notices | Links and research summaries only |
| `grindline`, `space-salvage` | Code MIT; separate asset attribution described as CC0 in license texts | Selected input/verification excerpts; no assets |
| OpenCode, Blender MCP, Godot MCP, Unity MCP, LangGraph | MIT in primary repository metadata/license records | Candidates only |
| GDQuest third-person demo | Code/scene/shader resources MIT; textures/models CC BY-NC-SA 4.0 | MIT camera script only; full player reference-only; no demo art |
| Phantom Camera, Road Generator, Questify | MIT | Candidates only |
| Easy Vehicle Physics | MIT code; bundled Kenney demo car has separate CC0 provenance | Vehicle/Wheel/input source only; no demo car/assets |
| LimboAI | MIT code; logo/demo art CC BY 4.0 | Candidate only |
| Godot demo projects | MIT code; audit individual asset notices | Candidate only |
| OpenKCC | MIT | Unity alternative only |
| SanAndreasUnity | MIT code does not license required GTA game data | Excluded production base |
| oMLX 0.6.4 | Apache-2.0 at pinned upstream commit | Machine-local installation only; no upstream runtime code/binaries bundled |
| Qwen3.8-Flash-Next-oQ6e-mtp | Model-card metadata: Qwen Community 1.0 (`license: other`); exact pack license applies | Machine-local model only; no weights bundled |
| Future original Blender outputs and audio | Exact component/provider terms and rights to be reviewed | No production assets included |

## Before any future import

### Machine-local runtime and model

The preparation tools refer to [oMLX 0.6.4](https://github.com/jundot/omlx/tree/1d7826185c5b5b69b38b27cbe57d7597b7551fd7) and the pinned [Qwen3.8 Flash-Next MLX pack](https://huggingface.co/mlx-community/Qwen3.8-Flash-Next-oQ6e-mtp/tree/e171af86f499f1855b0fb71d781105e8dd609610). Their binaries, upstream runtime code and model weights are installed only on the owner's machine and are not distributed in this repository. Their own licenses/terms apply; the project's MIT license does not cover them. Review those exact component terms before any redistribution or packaged release. Original diagnostic scripts and sanitized receipts in this repository are covered by the root MIT license.

### Import requirements

Record the upstream URL, pinned commit/release, exact files, author/copyright notice, full applicable license text, modifications, dependencies, and asset-specific terms. Preserve upstream attribution and notices in the distributed package. Do not apply this project's MIT notice over another component's license.

Unresolved asset/model/service rights block that component's import or redistribution until clarified. In particular, the GDQuest demo's noncommercial/share-alike art must not be treated as MIT art. Custom generated assets still require a documented rights review. No unresolved art/model/service component is bundled.

GTA and related names describe a gameplay reference; this project is not affiliated with Rockstar Games and distributes no Rockstar code or assets.
