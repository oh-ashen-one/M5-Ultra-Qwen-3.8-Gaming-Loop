# Continuing the existing queue after a capacity yield

The HUD controller now keeps its existing run and ownership locks while waiting for admission. It checks every thirty seconds, reports `capacity-wait`, and records the stage to resume. Waiting is not gameplay execution or measured mission progress. No separate driver, schedule or resource owner is created.

Every recheck enforces the existing STOP, memory/swap, desktop, disk and fixed October 8 deadline guards. It observes renderer identities and the resident coordinator's admission records, and checks the existing resident model's health and identity without inference. It never changes another workload, increases renderer limits, deletes another owner's records or restarts the model service. Admission must be available before either native testing or the fresh critic starts.

The two completed current-source HUD cases are hash-pinned and reused. The interrupted no-handoff evidence remains preserved. After admission, the same queue continues the unfinished no-handoff case, ten regressions and fresh local scoped review. Genuine test failures remain failures.

If capacity changes during a new native invocation, the existing engine adapter first cleans up only its recorded process group. The controller preserves unsealed partial artifacts in a separate interruption record before another admitted attempt. Completed or sealed evidence is never replaced. One native case permits at most three such interruptions; other resource faults and interrupted inference require diagnosis rather than automatic retries. The absolute project cap still ends all waiting and work.

304 CPU tests pass on both hosts. New tests cover visible yielding with the same owner, retained history/deadline, STOP and resource guards before another probe, preservation of partial native artifacts, and rejection of completed-evidence replay. Native HUD qualification is still separate from these controller checks.
