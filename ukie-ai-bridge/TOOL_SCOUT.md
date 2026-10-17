# UKIE AI LAB — Tool Scout / One-click Install Contract

Status: P0.1 foundation

## Goal

Allow AI to continuously accumulate useful research-tool candidates while keeping installation authorization simple for the human operator.

The human experience is intentionally one click:

`Tool candidates -> [許可して全てインストール] -> frozen approval manifest -> resolver -> verification -> install/ready`

A second Base44 approval is not required if the resolver remains inside the already-approved tool identity, publisher/source policy, and version policy.

## Approval is not arbitrary code execution

The one-click approval grants only the tools present in a frozen `ukie_install_approval_v1` manifest. It does not grant:

- arbitrary shell
- arbitrary PowerShell
- arbitrary EXE execution
- registry writes
- arbitrary delete paths
- whole-PC file access

The Windows Bridge has its own reviewed `TOOL_POLICY`. An AI-added Base44 candidate that is absent from that policy may be displayed and researched, but it cannot be resolved or installed by the Bridge until a reviewed Bridge update adds policy for it.

## Two-manifest model

To preserve one-click UX without allowing post-approval source swapping:

1. **Approval manifest** — frozen at the exact human click. Contains tool identity, approved official origin, publisher, requested version policy, and privilege flags. Its canonical JSON SHA-256 is stored.
2. **Resolved manifest** — generated later by Toolchain Resolver. Contains exact version/download/package ID and hashes. It must cryptographically bind to the approval-manifest SHA-256 and satisfy the hard Bridge policy.

No second Base44 click is needed for normal resolution. The operation pauses only if resolution would require a policy or permission escalation, such as an unapproved source, driver, purchase, account login, or additional Windows privilege outside the approved envelope.

## Detect before install

Before downloading anything the Bridge checks, in order:

1. PATH
2. Program Files / Program Files (x86)
3. LocalAppData
4. known application locations
5. configured research drive (`UKIE_RESEARCH_DRIVE`)

It does not recursively scan the entire C: drive in P0.1.

Already-working installations are registered and reused instead of reinstalled.

## Current candidate families

- Blender 4.2.23 pinned for BP3D production
- Research Python / uv
- SQLite tools
- 7-Zip
- Git
- Everything
- FFmpeg
- Microsoft Sysinternals
- x64dbg
- Ghidra
- RenderDoc

Candidate presence in Base44 is not equivalent to installability. The Bridge policy remains the execution gate.

## Current P0.1 boundary

Implemented:

- Base44 ToolCandidate / InstallBatch / CapabilityRegistry entities
- one-click approval UI
- canonical manifest SHA-256 freeze
- bounded local tool discovery
- approval-manifest validation
- resolved-manifest binding validation
- CI tests

Not implemented yet:

- downloader
- installer execution
- WinGet adapter
- UAC handoff
- rollback/uninstall adapter
- automatic tool capability verification after install

The UI must not claim `INSTALLED` or `READY` until the Windows worker actually verifies the corresponding capability.
