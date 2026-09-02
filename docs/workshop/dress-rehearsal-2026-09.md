# Dress rehearsal report, September 2026

Status: executed on `main` at `004bad8` (`workshop-v1.2.0`) in a clean Linux
container. Steps: reset, doctor, full Rehearsal run, five human merges, payoff
app, factory unit tests, Control Center boot.

## Verdict

The fallback path is solid. Every deterministic piece the workshop leans on ran
green, end to end, in under a minute of wall-clock.

What could not be tested is the part with the most variance on the day: Live
mode with real agent CLIs and GitHub writes, attendee laptops, the venue
network, and the Control Center clicked through in a browser rather than
curled. Those are where the risk lives, and the plan below spends its effort
there.

## What was executed, and what happened

| Step | Result | Detail |
| --- | --- | --- |
| `./setup_demo.sh --scenario recipe-rebrand` | PASS | 9.5 s. Creates venv, restores demo-app to the mobile baseline, repoints `factory-baseline`, writes fresh state. |
| `./factory/factory doctor` | PASS | 13 checks, 0 warnings. Charter approved, baseline verified at the mobile commit, ports free, 4 gates configured. |
| `factory run --mock --scenario recipe-rebrand --once` | PASS | 3.6 s. Supervisor dispatches #1 and #2 in parallel, QA commits protected tests, verify, Code Review approves, both park at In Review for human merge. Correct Standard-profile behaviour. |
| `factory merge N --mock --yes` ×5 with re-runs between | PASS | ~10 s total. Waves unlock exactly as taught: #1/#2, then #3, then #4, then #5. All five reach Done. |
| Ticket #3 retry path | PASS | Deterministic: attempt 1 fails verification, retry 1 of 2 with gate output fed back, attempt 2 passes. |
| Payoff app after run | PASS | Home renders TableStory / Cookbook / recipes; `/?mode=tv` applies the `tv` class and rails; `/api/rails` serves recipe ids. |
| Demo-app gates (venv pytest plus `node --test`) | PASS | Green at baseline. |
| Factory unit tests (414) | PASS | Green under `.factory/venv/bin/python`. Under system `python3` without pytest, 8 QA tests fail spuriously. Environment, not code. |
| `./factory/factory control-center` | PASS | Boots, serves HTTP 200 on 5050 with Rehearsal option, Current phase, Next safe action. Not browser-clicked (headless container). |
| Live mode (real adapter plus GitHub) | NOT RUN | No credentials in the environment. Must be rehearsed personally. |

## Two things found that would have hurt on the day

### 1. The CLI says "Deadlock" when nothing is deadlocked

After a Rehearsal wave, `factory run --once` prints
`Deadlock: #3 waits for [1, 2], #4 waits for [3], #5 waits for [4]`. The
tickets are simply waiting for the human to merge #1 and #2. The Control Center
says "NEEDS YOU — new dispatch is paused" instead, which is correct.

Rule: never run the CLI on the projector during the merge blocks. The fix is
one line at `factory/orchestrator.py:4589`: exclude tickets whose only unmet
dependencies are In Review, and print "Waiting for human merge: #1, #2".

### 2. Rehearsal merges are real commits on the current branch, and reset does not rewind them

A full Rehearsal adds about 16 commits (`test(#N)`, `factory(#N)`,
`Merge ticket #N`) to whatever branch is checked out. `setup_demo.sh` restores
the files and adds a "reset to mobile baseline" commit on top; it never rewinds
history. Harmless in a disposable clone; embarrassing if you rehearse on the
branch you show in the room and someone opens `git log`.

Rule: rehearse in a throwaway clone.

## Live-day risk register, ranked by likelihood × damage

| # | Risk | When | Mitigation |
| --- | --- | --- | --- |
| 1 HIGH | A third of the room fails preflight (wrong Python, no `project` scope, unauthenticated CLI, corporate proxy). | 0:25 | Prereq email three days out with the six verify commands and a reply-required "all green" line. One helper per 8. Hard cap: at 0:50 anyone still red moves to Rehearsal and stays there. Say this as policy, not apology. |
| 2 HIGH | Real agents take 5–15 min per step in Live; the room drifts while waiting. | 1:05, 2:20 | Never wait on screen. Facilitator repo has every state pre-staged (QA Review ticket, REQUEST_CHANGES ticket, merge-ready ticket, finished app). Teach from staged state. |
| 3 HIGH | Venue Wi-Fi collapses or blocks GitHub or provider APIs. | any | Rehearsal is zero-network. Decide in advance: if network is dead at 0:25, the whole session runs Rehearsal. Second laptop with Rehearsal preloaded, tethered to a phone. |
| 4 MED | Product Review artifact comes back already strong; nobody finds a vague claim. | 1:05 | Use the prepared revision request (Escape/Backspace plus focus restore). The point is the mechanism. |
| 5 MED | Attendee's agent produces a bad slice or a huge diff; their ticket blocks. | 2:20 | That is the recovery drill. Pull it on screen (with permission) and run the four questions. |
| 6 MED | Overrun squeezes the merge block; the manager never sees a human merge. | 2:40 | Protect the merge block. If 10 min late at 2:00, do QA classification as a room exercise and skip per-pair test approval. |
| 7 MED | "Isn't this just Copilot Workspace / Devin / Codex Cloud?" | 0:10 | Answer with the layer slide: those are inner harness plus some compute. Ask what evidence they show at merge time and who is accountable. |
| 8 LOW | A quote or stat on a slide is challenged. | any | Only put on slides what you have personally read at source. Conference numbers came via recaps; verify or replace with your own team's data. |

## How to make it yours: the anti-slop pass

A script written by someone else and read aloud will sound like a script. The
content structure is sound; the voice has to be the facilitator's. What makes a
workshop feel generated is not the ideas, it's the delivery texture: smooth
aphorisms, borrowed numbers, no scars.

1. Rewrite every SAY block in your own words, out loud, once. Keep the beat (failure, mechanism, evidence, decision). Throw away the phrasing.
2. Replace the cold-open PR with one from your own team. A real PR your engineers argued about, names blurred.
3. Replace the conference stats with your numbers. How many agent-authored PRs did your team merge last quarter? How long did review take?
4. Tell one real story per act. Two sentences each, no moral attached.
5. Never claim what you can't show within thirty seconds.
6. Let the room fail on purpose. Do not smooth over the failure lab and recovery drill to save time. Lumpy is credible; polished is suspicious.
7. Cut the quotable lines. Keep at most two, only if they come out naturally.
8. End with the manager's question, not a slogan: "If we ran this on our repos, which decision in our current process would get smaller?" Then stop talking.

## Rehearsal protocol, seven days out

| Day | Do | Exit criterion |
| --- | --- | --- |
| D-7 | Full Rehearsal solo in a throwaway clone, Control Center only, following the script block by block with a timer. | Every block within ±3 min. You've seen "NEEDS YOU" and the #3 retry with your own eyes. |
| D-5 | Full Live run on a disposable GitHub repo with your real adapter: connect, contract, preflight, PRD, four experts, tickets, one cycle, run, review, merge. | Screenshots captured for the PR slide, a real broken preflight, and the REQUEST_CHANGES ticket. Real minutes per agent step noted. |
| D-3 | A colleague plays attendee on their laptop, cold, from the prerequisite email only. You do not touch their keyboard. | They reach a passing preflight in ≤ 20 min, or you now know which prerequisite line is unclear. Fix the email. |
| D-2 | Deliver blocks 0:00–0:25 to that same colleague, in your rewritten words, no notes. | They can repeat the agent-vs-factory distinction back unprompted. |
| D-1 | Freeze. `doctor` green on the projector laptop; tags pushed; staged states verified; second laptop with Rehearsal preloaded; tabs open; phone tether tested. Print the Factory Canvas. | No changes to the factory checkout after this point. |
| Day | Arrive 60 min early. Venue network test against GitHub and your provider. `doctor` again. | Decision made by 0:00: Live or Rehearsal for the room. Say it once. |

## What the manager will actually be judging

Not whether the agents were impressive. Whether the room was in control of what
the agents did, whether the facilitator was in control of the room, and whether
anyone left with a decision they could take back to their team. The script is
built to produce exactly those three things: every attendee performs a merge
they can defend, repairs a failure by changing its cause, and leaves with a
filled-in canvas for their own case. Protect those three moments over
everything else.
