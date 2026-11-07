# Selene packaged performance harness

Shipping is the acceptance build. Development adds Unreal's CSV profiler for diagnosis. This installed UE 5.8 has **no Mac Test configuration**; do not select Test or expect a Shipping CSV-profiler file. No PerfReportTool/CsvTools dependency is used. Python 3.9+ and its standard library suffice.

This implementation has been compiled, not performance-certified. No game was packaged or launched during implementation. A successful compile or synthetic test does not prove 60 fps. Collect Shipping evidence on the intended M3 Max with Metal SM6/Lumen before making that claim.

## Route contract

Place and save `ASelenePerfRoute` actors in the cooked map. Python class path: `/Script/Selene.SelenePerfRoute`. Set `route_name`; set `segments` to `SelenePerfSegment` structs with `tag`, `category`, `start_distance`, `end_distance`; edit the `Route` spline component's points. Distances are spline arc length in centimeters. Points describe **ground-contact feet positions**. The runner adds the possessed character's scaled capsule half-height, keeps the capsule upright, and uses the character's own camera offsets. Layout schema v2 uses terrain height for 2D points and absolute floor/feet elevation for 3D points. Keep these names stable for the external authoring script.

Each route name must be unique. Segment `category` is `exterior`, `doorway`, or `interior`; tags identify individual spans (e.g. `doorway_workshop_entry`). Segments must have unique, nonempty tags, positive lengths, fit within the spline, and not overlap. Boundaries are start-inclusive/end-exclusive except the final route endpoint. Gaps are logged as `unsegmented` and included in whole-run statistics. Every declared segment must receive measured frames in the cold lap AND each warm lap; an undersized/skipped segment fails capture. Make route actors initially loaded (for World Partition, use a non-spatially loaded actor), and include the map in cooking. The harness waits for ordinary streaming to settle at startup; it does not preload all route content.

`USelenePerfRouteSubsystem` is a **UWorldSubsystem**, created only in a Game world with `-PerfRoute=`. One map is launched per process, so world ownership avoids stale route/pawn references across travel and excludes Editor/PIE worlds. Begin play, a possessed pawn, a usable viewport, and initial streaming readiness are required within 60 seconds.

## Capture options and lifecycle

| Argument | Default | Meaning |
|---|---|---|
| `-PerfRoute=TownWalk` | required | RouteName to find |
| `-PerfCam=3P` | 3P | 3P or 1P |
| `-PerfHour=12` | 12 | Hour in [0,24), then pause time |
| `-PerfTimeFlow=60` | absent | Set time speed and unpause after setting the hour |
| `-PerfLaps=3` | 3 | Warm laps, in addition to one cold lap |
| `-PerfWarmup=15` | 15 seconds | Discarded moving warm-up |
| `-PerfSpeed=150` | 150 cm/s | Kinematic spline travel speed |
| `-PerfOut=/absolute/path` | ProjectSaved/Perf | Output directory |

After begin play the subsystem executes `selene.Camera 3p|1p`, `tod.set <hour>`, `tod.pause 1`; time-flow additionally executes `tod.speed <speed>` and `tod.pause 0`. It then verifies possession of `ASeleneCharacter`, the requested camera mode, and the world time-of-day actor's hour, paused state and (when flowing) speed before warm-up or measurement. Any dispatch warning or state mismatch records `configuration_error`, aborts with a nonzero status, and makes the report INVALID. Successful verification records `configuration_verified=true`. Registered commands must themselves be available in Shipping (not stripped/cheat-only).

Movement and look input are ignored, and the pawn movement component is stopped and deactivated. The pawn is positioned without sweep via `SetActorLocationAndRotation` with upright yaw along the world-space spline tangent. `view_keys` (`distance`, world-cm `look_at_target`, `use_look_at`) independently drive control rotation from the character eye. Keys are ordered by distance; look-at targets interpolate linearly, mixed tangent/look-at keys blend rotations, and no keys uses a 2.5 m look-ahead chord, low-pass filtered over a 2 m triangular distance window, with pitch clamped to ±25°. Filtering in distance space is deterministic across frame rates and lap resets; explicit look-at keys keep precedence. The builder emits endpoint keys for layout `look_at`, including R1 toward the tower and R3 back over town. Existing camera-mode offsets are preserved. Custom pawn ticks/physics that override its transform or camera require integration inspection.

Flow: moving warm-up (discarded) → teleport to start + camera cut + 2 seconds stationary/discarded → COLD lap (lap 0) → repeat teleport/cut/2-second discard + warm laps 1..N. **COLD means first recorded traversal after warm-up, not a cleared shader, streaming, Metal, or OS cache.** Streaming/PSO work occurring on measured traversals is included. There is no cache-deletion operation.

Capture runs at the global begin-frame delegate. Each row describes the preceding begin-to-begin real interval, attributed to the pawn distance used for that frame. A monotonic clock avoids game-delta clamping/time dilation/fixed-step settings concealing a hitch. World-paused or headless benchmarks are not supported. Route movement uses that real elapsed time at constant cm/s, clamping only at the endpoint. Rows are buffered in preallocated memory; disk serialization occurs after the last measured frame. Reservation uses a 1000 fps upper estimate with a 10-million-row cap; exhaustion fails explicitly.

Files use `<UTC timestamp + unique suffix>_<route>_<cam>_<hour>`:

- `.frames.csv`: `frame_index,lap,segment_tag,delta_ms,game_thread_ms,render_thread_ms,gpu_ms,is_discarded`. Lap -1 is warm-up, lap 0 cold, 1..N warm. Discarded rows remain auditable but do not enter metrics.
- `.meta.json`: build/engine/map, viewport pixels/window mode, RHI, command line, route declarations, requested settings, all available `sg.*`, Lumen/VSM/Nanite/ray tracing/dynamic-resolution CVars and screen percentage/AA/vsync/max-FPS controls, warnings, counts, timer availability and completion/error state. These are CVar snapshots, not proof of per-view post-process overrides or dynamic internal resolution; a secondary percentage of 0 is Unreal's automatic choice, not zero rendered pixels.
- `.profile.csv`: Development only, started before the cold lap's settling interval and stopped after all measured laps. CSV boundary events mark BEGIN/END lap and segment plus SETTLE. Its discarded intervals must not be used for acceptance. The `EndCapture()` shared future is polled on later engine frames; the process does not exit until asynchronous writing completes and a nonempty profile exists.

Missing/duplicate/invalid routes, empty captures, zero-frame segments, lost possession, write failures and invalid options set metadata `status=error` and `error`, emit an error, and exit nonzero. Initial `running`/`finishing` metadata also makes interrupted or truncated captures fail closed. If the destination itself is unwritable, metadata cannot be persisted there; low-level output and process status are the fallback.

Mac caveat: `FMacPlatformMisc` inherits generic `RequestExitWithStatus`, whose implementation **ignores the return code** in this install. After calling that API, the harness uses `std::_Exit(nonzero)` on Mac failures, after closing its files and waiting for any active CSV capture. Successful runs use graceful Unreal exit. World destruction before normal completion is an exceptional abort: it marks incomplete metadata and exits nonzero; the external watchdog also treats missing/incomplete files as failures.

## Shipping timer evidence (installed engine source)

Source paths below are relative to `/Users/Shared/Epic Games/UE_5.8/Engine/`.

| Column | Source and Shipping availability |
|---|---|
| `delta_ms` | Our `FPlatformTime::Seconds()` begin-to-begin interval. Authoritative for acceptance, including waits/throttling. This is engine frame pacing, not hardware display scanout/PresentMon. |
| `game_thread_ms` | `Source/Runtime/RenderCore/Public/RenderTimer.h:17` exports `GGameThreadTime`; `Source/Runtime/Engine/Private/UnrealClient.cpp:1829-1861` updates it without a Shipping/STATS guard, subtracting thread wait accounting. |
| `render_thread_ms` | `RenderTimer.h:8` exports `GRenderThreadTime`; `Source/Runtime/SlateRHIRenderer/Private/SlateRHIRenderer.cpp:1323-1370` updates it unconditionally around present, subtracting idle (or selecting critical-path accounting according to its CVar). |
| `gpu_ms` | `Source/Runtime/RHI/Public/DynamicRHI.h:1250` exports `RHIGetGPUFrameCycles`; `Source/Runtime/RHI/Private/GPUProfiler.cpp:2132-2148` updates frame busy time outside HAS_GPU_STATS, and `:2265-2284` provides its atomic accessor. Metal populates command-buffer timestamps at `Source/Runtime/Apple/MetalRHI/Private/MetalSubmission.cpp:660-694`, outside the breadcrumb guard, using hardware counter samples or `GPUStartTime`/`GPUEndTime`. |

All three diagnostic timers are compiled in Shipping here. Zero-cycle/uninitialized samples are written **empty**, and metadata counts valid measured samples. The profiler is asynchronous: CPU/RT/GPU values are latest available snapshots, may lag or repeat, and must not be interpreted as three synchronized components of the row's delta. Their medians/p99 are diagnostic only. No smoothing via `FStatUnitData` or dependency on `stat unit` is used; Unreal's own raw timer conversion can be compared at `Source/Runtime/Engine/Private/UnrealClient.cpp:385-410`.

`Source/Runtime/Core/Public/ProfilingDebugging/CsvProfilerConfig.h:9-10,29-31` defaults CSV out of Shipping; `CsvProfiler.h:519-529` documents BeginCapture/EndCapture and the file-write completion future. `Config/BaseEngine.ini:3999-4008` lists the installed Mac DebugGame/Development/Shipping configurations, with no Test. Exit-code evidence: `Core/Public/Mac/MacPlatformMisc.h:24-42`, `Core/Public/Apple/ApplePlatformMisc.h:42`, and `Core/Private/GenericPlatform/GenericPlatformMisc.cpp:1167-1172` (all under `Source/Runtime/`).

## Step 0 spike decision

**The AutomatedPerfTesting runtime lifecycle can be launched from a plain shell without BuildGraph, but is not a suitable drop-in for this spline/Shipping harness. Use its lifecycle ideas, not a module dependency.**

`Plugins/Experimental/Gauntlet/Source/Gauntlet/Private/GauntletModule.cpp:189-235` parses `-gauntlet=` and instantiates controllers inside the running game. A separately enabled/configured AutomatedPerfTesting + Gauntlet setup could launch an `AutomatedSequencePerfTest` controller directly and select its configured map/sequence combo using `-AutomatedPerfTest.SequencePerfTest.MapSequenceName=...`; BuildGraph is external orchestration, not required for that runtime dispatch. No such plugin/project configuration is modified here.

`Plugins/Performance/AutomatedPerfTesting/Source/AutomatedPerfTesting/Private/AutomatedSequencePerfTest.cpp:44-103` waits for the correct world/streaming, creates a Level Sequence player, scrubs it, and delays startup; `:153-190` starts capture and binds sequence/camera-cut callbacks; `:201-229` stops profiling on sequence completion. Its base controller's `AutomatedPerfTestControllerBase.cpp:170-235` uses BeginCapture/EndCapture, and `:385-417` waits for the CSV completion event before exiting. These are reusable patterns.

Direct reuse would require Gauntlet/plugin enablement, configured map/Level Sequence assets, and that controller's game-mode/test orchestration. It does not implement our reflected spline actor contract, possessed-pawn walk, segment accounting, cold/warm lap policy, or Shipping-safe acceptance log, and CSV remains unavailable in Shipping. Missing BuildGraph orchestration and absent CsvTools do not prevent the custom runtime+shell+stdlib workflow.

## Build and package (operator steps; not executed here)

From the project root, compile either target:

```bash
UE='/Users/Shared/Epic Games/UE_5.8'
"$UE/Engine/Build/BatchFiles/Mac/Build.sh" SeleneEditor Mac Development -Project="$PWD/Selene.uproject" -WaitMutex
"$UE/Engine/Build/BatchFiles/Mac/Build.sh" Selene Mac Shipping -Project="$PWD/Selene.uproject" -WaitMutex
```

Package the authored `/Game/Selene/Maps/Town` map. Keep Shipping and Development archives separate:

```bash
UE='/Users/Shared/Epic Games/UE_5.8'
"$UE/Engine/Build/BatchFiles/RunUAT.sh" BuildCookRun \
  -project="$PWD/Selene.uproject" -noP4 -platform=Mac -clientconfig=Shipping \
  -build -ubtargs="-noEntitlements" -cook -map=/Game/Selene/Maps/Town -stage -pak -package -archive \
  -archivedirectory="$PWD/Packaged/Shipping" -unattended

"$UE/Engine/Build/BatchFiles/RunUAT.sh" BuildCookRun \
  -project="$PWD/Selene.uproject" -noP4 -platform=Mac -clientconfig=Development \
  -build -ubtargs="-noEntitlements" -cook -map=/Game/Selene/Maps/Town -stage -pak -package -archive \
  -archivedirectory="$PWD/Packaged/Development" -unattended
```

Find the staged `.app` under the archive's Mac directory; do not benchmark the uncooked `Binaries/Mac` compile output. Both package commands disable entitlements at build time because the matrix writes to explicit checkout paths. The matrix inspects `codesign -d --entitlements :- APP.app` before creating output or launching a process, and refuses sandboxed apps or unreadable signatures. UBT's `Source/Programs/UnrealBuildTool/Platform/Apple/AppleExports.cs:27-35` reads `-noEntitlements`; `ProjectFiles/Xcode/XcodeProject.cs:1981,2856` omits entitlements accordingly. AutomationTool's `AutomationUtils/ProjectParams.cs:1057,2499-2500` exposes `-ubtargs`; `Scripts/BuildProjectCommand.Automation.cs:130-145` forwards it into the build agenda. `AppleToolChain.cs:853,1418` carries the option into post-build sync. Verify the resulting signature's entitlements when using a custom signing workflow.

## Packaged Mac Saved location

For an ordinary installed/non-sandboxed Shipping Selene build, the default is:

```text
~/Library/Application Support/Epic/Selene/Saved/Perf/
```

`Core/Private/Apple/ApplePlatformProcess.cpp:38-63` chooses the user's Application Support directory and appends `Epic/`; `Core/Private/Misc/Paths.cpp:450-468` appends the project name when saving to the user directory, and `:85-114,485-494` appends `Saved/`. `Core/Private/Misc/App.cpp:212-243` defaults desktop Shipping to installed mode and also detects staged `Engine/Build/InstalledProjectBuild.txt`; `Paths.cpp:183-191` selects the user directory for installed builds. Prefix these paths with `Source/Runtime/`.

A staged Development build carrying that installed-project marker uses the same user location. Development without the marker can use `<ProjectDir>/Saved/`; `-SaveToUserDir` forces the user location. App Sandbox may redirect the Application Support lookup beneath `~/Library/Containers/<bundle-id>/Data/Library/Application Support/Epic/Selene/Saved/`. `-UserDir`/`-NotInstalled`/saved-dir overrides can also change it. The metadata records resolved `saved_dir` and `frame_log`; explicit absolute `-PerfOut` is preferred and is always used by the matrix script.

## Run the matrix

Close/idle Blender, builds, other games and GPU workloads. Keep power mode, power supply, display resolution/refresh, thermal state, and presentation settings consistent. The script prints this reminder. It launches the bundle executable directly (no `open`, editor, or live session) so arguments, waiting, and exit status are reliable.

```bash
Tools/Perf/run_matrix.sh "$PWD/Packaged/Shipping/Mac/Selene.app" /Game/Selene/Maps/Town R1 R2 R3 \
  --res-x 1920 --res-y 1080 --build Shipping --nosound

Tools/Perf/run_matrix.sh "$PWD/Packaged/Development/Mac/Selene.app" /Game/Selene/Maps/Town R1 \
  --res-x 1920 --res-y 1080 --build Development --nosound
```

Adjust actual bundle names. For each route there are 9 fresh-process runs: cameras 3P/1P × hours 12/17.5/19/22 plus one 3P/noon flowing-time run (speed 60 by default). Each uses fullscreen with explicit ResX/ResY. The harness records the actual viewport size; verify it matches the intended test pixels on Retina displays. Audio stays enabled unless `--nosound` is supplied. Vsync and `t.MaxFPS` are recorded, not silently changed; a 60 Hz cap will prevent demonstrating 120 fps headroom.

`--out` must name a fresh directory. Defaults: `Tools/Perf/runs/<UTC-id>/run-0001/...`, reports beneath that matrix directory. Each launch saves process output, full argv, duration, return code, and artifact list. The watchdog is calculated separately for each route from `Design/Blockout/layout.json` (override with `--layout` or explicit `--route-length-cm` for a custom map):

`ceil(60 + 1.10 * (warmup_seconds + (warm_laps + 1) * (route_length_cm / speed_cm_s + 2)) + 120)`.

This includes the 60-second startup allowance, cold plus warm traversal/settling, 10% scheduling slack, and 120 seconds for completion and disk I/O. At 150 cm/s, 3 warm laps and 15 seconds warm-up, R2 gets 4,346 seconds. `--timeout` may increase this value; shorter overrides are rejected. The selected value is saved in `launch.json`. The watchdog terminates hung runs and retains the failure. Remaining runs still execute; the final script status is nonzero if any launch/capture/performance check fails. An interrupted matrix retains per-run launch records even if no final report is created.

Raw files are copied to a new archive directory (never overwritten), default:

```text
/Users/nicknetraganti/Desktop/Developer Stuff/game-asset-workflow/evidence/selene-perf/<run-id>/
```

Use `--archive "$PWD/Tools/Perf/evidence/<unique-id>"` to keep evidence in this checkout. This default external path is only used when an operator actually runs the summarizer/matrix; implementation tests explicitly use temporary directories inside Tools/Perf.

## Standalone summary and interpretation

```bash
python3 Tools/Perf/summarize.py /path/*.frames.csv \
  --profiler /path/*.profile.csv --build Development \
  --reports "$PWD/Tools/Perf/reports" --archive "$PWD/Tools/Perf/evidence/example-run"
python3 Tools/Perf/test_summarize.py
```

Omit `--profiler` for Shipping. Adjacent matching `.meta.json` files with literal `configuration_verified: true` are required, so a missing segment declaration or truncated/incomplete capture cannot produce PASS. Optional Development CSV files are preserved and hashed as opaque diagnostic inputs; their arbitrary profiler columns never substitute for frame logs. Launch manifests and process logs are archived too when supplied by the matrix.

Outputs are `<reports>/<UTC date>-<build>.md` and `.json`; if already present, a unique run-id suffix preserves the earlier report. Every individual run, warm lap, declared segment, category rollup and cold result is retained. Category metrics pool the constituent frames, not segment averages; per-segment acceptance remains mandatory. SHA256 covers every archived raw file, including metadata and optional profiles. Missing raw inputs fail the report.

Metrics: average FPS = 1000/mean(frame ms); 1%-low FPS = 1000/mean(slowest ceil(1% of frames)); p99 uses nearest rank; slow-frame percentage counts `>16.7 ms`; hitch count counts `>33.3 ms`. GT/RT/GPU median and p99 exclude empty samples and include valid-sample counts in JSON. Gap to 120 = max(0, p99 - 8.33) milliseconds.

Acceptance requires complete valid data, warm p99 ≤16.7 ms, and zero warm hitches >33.3 ms. This is checked per run, lap, and segment, preventing a short slow segment/lap from being hidden by pooling. Cold timing is reported separately and does not gate warm performance, but missing cold coverage is a capture failure. Overall Shipping PASS requires every individual run to pass. Development results are labeled DIAGNOSTIC_PASS/DIAGNOSTIC_FAIL and are never Shipping proof. Any metadata warning or configuration error/warning flag makes the run and aggregate report INVALID, regardless of frame timings. Invalid report rows cannot display PASS.

## Verification and remaining integration work

The checked-in source changes add only `RenderCore`, `RHI`, and `Json` module dependencies. `build-editor-console.log`, `build-shipping-console.log`, and `test-output.log` in this directory retain local verification output; generated build artifacts are not source changes. Unreal/Xcode may also create their normal user-level build caches/trace files even when `-Log` points inside the checkout.

Remaining runtime work: author/cook route assets, integrate the external camera/time commands, package both configurations, confirm camera tracking/viewport/entitlements and valid Metal timer samples, then run the Shipping matrix and inspect the archived per-run evidence. No ≥60 fps claim is made without those measurements.

## Checkpoint 1 shots and collision walk

Rebuild Town with `Tools/Unreal/build_blockout.py` before capture: it now creates
`EW` from `east_west_walk.points` using the existing terrain/paving feet path,
metres-to-cm axis conversion and linear spline authoring. EW has one exterior
`crossing` segment and no view keys. `verify_unreal.py` audits it with R1–R3.

- `-PerfShots=N` (integer 1–60) replaces measured laps with one sequence of
  evenly spaced stops including both endpoints. N=1 captures the start only.
  Laps are ignored. After moving warm-up, each stop uses normal pawn placement
  and view aiming, settles for 1.5 real seconds, then requests a PNG without UI.
  It waits for a nonempty file (20-second timeout) before advancing. No frame
  CSV or CSV profiler capture is produced. Metadata has `mode: "shots"`.
  `<PerfOut>/shots/<Route>_<Cam>_<NN>.png` uses indices 01 through N;
  `<Route>_<Cam>.manifest.json` alongside them records index, distance_cm,
  world_location (capsule centre, world cm), rotation (control/view rotation,
  degrees), actor_rotation, filename (relative to the manifest) and segment_tag.
  Existing shot filenames cause an error rather than accepting stale evidence.
  The summarizer ignores inputs whose adjacent metadata has `mode: "shots"`;
  shots alone cannot produce a performance PASS.
- `-PerfDrive=1` replaces measured laps with one collision-driven walk. After
  moving warm-up it resets to the start once, enables CharacterMovement in
  walking mode, selects Walk pace and sets MaxWalkSpeed to `-PerfSpeed`
  (default 150 cm/s). It supplies horizontal movement input toward the nearest
  spline distance plus 250 cm; no teleport occurs during the walk. Completion
  is horizontal distance within 50 cm of the endpoint. Metadata has
  `mode: "drive"`, game-time `walk_seconds`, actual 3D `path_length_cm`,
  `route_length_cm` and `average_speed_cm_s`. Less than 100 cm net spline
  progress over any rolling eight real seconds fails with `stuck_location`
  and an error. Frame CSV is diagnostic/discarded; drive runs do not supply
  cold/warm performance evidence or start the CSV profiler.

The two modes are mutually exclusive; invalid values fail explicitly. Without
these flags the existing cold/warm traversal and output contract is unchanged.

```bash
Tools/Perf/capture_checkpoint1.sh
```

This launches the Development `UnrealEditor` in `-game`, windowed 1920×1080,
without sound, once per job in sequence: R1×6, R2×12, R3×3 shots, each in 3P
then 1P, followed by EW in 3P at 150 cm/s. All jobs use noon and 10 seconds
warm-up. Set `ENGINE` to override `/Users/Shared/Epic Games/UE_5.8`.
Outputs share a fresh `Saved/Checkpoint1/<UTC timestamp>-<pid>/`: PNGs and
manifests in `shots/`, unique metadata per run, EW frame CSV, and per-job
engine/process logs and exit codes. Expected total: 42 PNGs.

Per-job watchdogs derive route length from the same terrain-aware Python
geometry as the builder. Shots allow 60 seconds startup, 110% of warm-up plus
route-length/speed plus 21.5 seconds per shot, then 120 seconds exit margin.
EW allows 60 seconds startup, 150% of warm-up plus route-length/speed, and
120 seconds exit margin (roughly 11 minutes for a 5.5-minute walk). A timed-out
process receives TERM then KILL after five seconds. Jobs continue after a
failure; the script exits nonzero if any process or artifact validation fails.
Its final summary lists shot counts per route/camera and EW game time as m:ss
versus the expected 5–6 minutes; an out-of-range completed walk also fails validation. Screenshot delivery under `-game`, actual camera framing and
collision navigation must be checked by running the controller's capture;
compilation and Python checks alone do not establish runtime success.
