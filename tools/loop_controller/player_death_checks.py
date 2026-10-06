"""External zero-health boundary diagnostics; no fabricated objective completion."""
import math
import struct

CASES = {
    'courier-pickup': (7.4, 'F', {'courierStage': 0, 'routeStage': 0}),
    'courier-delivery': (14.3, 'F', {'courierStage': 1, 'routeStage': 0}),
    'dead-drop': (32.50206129914633, 'F', {'courierStage': 2, 'routeStage': 1}),
    'relay-final': (59.6, 'F', {'routeStage': 2, 'relayCount': 2, 'relayComplete': False}),
    'interception-receipt': (60.15, '', {'relayComplete': True, 'interceptionActive': True, 'spawned': 0}),
    'interception-final': (75.4, 'Mouse0', {'interceptionActive': True, 'stopped': 2, 'spawned': 3}),
}


def death_probe(original, case):
    at, key, _ = CASES[case]
    # Reach the stage via the identical ordinary-input prefix. Only the declared
    # health injection differs at the action edge; never set a chapter outcome.
    prefix = [dict(start=s['start'], end=min(s['end'], at + .15), keys=list(s['keys']))
        for s in original['steps'] if s['start'] <= at + .001]
    reset = at + 3.5
    extra = [(at+.45, at+2.0, ['W','D']), (at+.5, at+.6, ['Mouse0']),
        (at+.65, at+.75, ['E']), (at+.85, at+.95, ['F']),
        (at+1.0, at+1.1, ['Mouse0']), (at+1.5, at+1.6, ['Mouse0']),
        (reset, reset+.3, ['R']), (reset+1.5, reset+2.5, ['W'])]
    return dict(id='player-death-'+case, fixture='player-death', death_case=case,
        death_at=at, death_key=key, coverage='mission-core', duration=at+7,
        steps=prefix + [dict(start=a, end=b, keys=k) for a,b,k in extra],
        captures=[3.2, at+.25, at+2.5, reset+.5, reset+3])


def inspect_player_death(rows, injection, case):
    at, key, expected = CASES[case]
    # Scenario.death_at and LoopInput.Elapsed are Unity float32, serialized into
    # JSON doubles. Compare the same representable boundary, not a stricter
    # Python decimal (e.g.59.6 becomes59.599998474121094 in the player).
    native_at = struct.unpack('f', struct.pack('f', at))[0]
    before = injection.get('before', {})
    failures = []
    setup_failures = []
    if (injection.get('caseName') != case or injection.get('healthBefore', 0) <= 0
            or injection.get('healthAfter') != 0 or injection.get('restarts') != 0
            or not native_at <= injection.get('time', -1) <= at+.12
            or (key and key not in injection.get('keys', []))):
        setup_failures.append('declared-live-health-injection-not-established')
    if any(before.get(k) != v for k,v in expected.items()):
        setup_failures.append('ordinary-input-chapter-precondition-not-established')
    reset = at + 3.5
    dead = [r for r in rows if at+.2 <= r.get('time', 0) <= reset-.1 and r.get('restarts') == 0]
    if len(dead) < 10:
        failures.append('missing-zero-health-window')
    else:
        if any(r.get('health') != 0 for r in dead):
            failures.append('health-revived-before-R-reset')
        if any(r.get('shots') != injection.get('shots') for r in dead):
            failures.append('player-can-fire-while-dead')
        if any(r.get('mode') != injection.get('mode') for r in dead):
            failures.append('vehicle-entry-or-exit-while-dead')
        for name in ('player', 'vehicle'):
            initial = dead[0].get(name)
            if not initial or any(not r.get(name) for r in dead):
                failures.append('missing-'+name+'-position')
            elif max(math.hypot(r[name][0]-initial[0], r[name][2]-initial[2]) for r in dead) > .15:
                failures.append(name+'-moves-under-dead-input')
        for row in dead:
            state = row.get('playerDeath') or {}
            if (state.get('courierStage') == 2 and before.get('courierStage') != 2
                    or state.get('carrying') and not before.get('carrying')
                    or state.get('routeComplete') and not before.get('routeComplete')
                    or state.get('relayComplete') and not before.get('relayComplete')
                    or state.get('interceptionComplete') and not before.get('interceptionComplete')
                    or state.get('routeStage', 0) > before.get('routeStage', 0)
                    or state.get('relayCount', 0) > before.get('relayCount', 0)
                    or state.get('stopped', 0) > before.get('stopped', 0)
                    or state.get('spawned', 0) > before.get('spawned', 0)):
                failures.append('objective-progression-after-zero-health')
            board = next((p for p in row.get('routeChapter', {}).get('hudPanels', []) if p.get('name') == 'MissionBoard'), {})
            text = board.get('text', '').lower()
            if not board.get('visible') or not any(x in text for x in ('dead','died','health depleted','health lost','failed')) or not any(x in text for x in ('reset','retry')):
                failures.append('death-failure-and-reset-not-visible')
    after = [r for r in rows if reset+.4 <= r.get('time', 0) <= reset+1.2 and r.get('restarts') == 1]
    if len(after) < 4:
        failures.append('ordinary-R-reset-not-established')
    else:
        for row in after:
            state = row.get('playerDeath') or {}
            if (row.get('health') != 100 or row.get('mode') != 'foot' or row.get('shots') != 0
                    or row.get('hits') != 0 or row.get('mission') != 'active'
                    or state.get('courierStage') != 0 or state.get('carrying')
                    or state.get('routeStage') != 0 or state.get('routeComplete')
                    or state.get('relayActive') or state.get('relayComplete') or state.get('relayFailed')
                    or state.get('relayCount') != 0 or state.get('interceptionActive')
                    or state.get('interceptionComplete') or state.get('interceptionFailed')
                    or any(state.get(k) != 0 for k in ('stopped','spawned','escaped'))):
                failures.append('whole-reset-state-not-restored')
        moved = [r for r in rows if reset+2.7 <= r.get('time',0) <= reset+3.3 and r.get('restarts') == 1]
        if not moved or max(math.hypot(r['player'][0]-after[0]['player'][0], r['player'][2]-after[0]['player'][2]) for r in moved) < 1.5:
            failures.append('walking-not-restored-after-reset')
    return dict(case=case, passed=not failures and not setup_failures, setup_passed=not setup_failures,
        failure=sorted(set(setup_failures+failures)), injection_time=injection.get('time'),
        prior_chapter_state=before, zero_health_samples=len(dead), reset_samples=len(after),
        intervention='External declared one-time health=0 injection; progression and controls remain ordinary game code.',
        native_natural_damage_death_proven=False, final_game_accepted=False)
