"""Owner's absolute project cap and private milestone evidence outbox."""
import datetime as dt
import time
from .core import Halt, atomic, now, read_json, sha

FIRST_BUILD_UTC='2026-10-05T06:33:12+00:00'
HARD_CAP_UTC='2026-10-08T06:33:12+00:00'
HARD_CAP_EPOCH=dt.datetime.fromisoformat(HARD_CAP_UTC).timestamp()


def apply_authorized_cap(store,config):
    if time.time()>=HARD_CAP_EPOCH:raise Halt('Three-day project cap reached; no new work authorized')
    old=store.get('overall_deadline_epoch')
    if store.get('three_day_cap') is None:store.set(superseded_overall_deadline_epoch=old)
    # Never change attempts, failure streaks, diagnosis flags or accepted-progress times.
    config['wall_hours']=(HARD_CAP_EPOCH-store.get('started_epoch'))/3600
    store.set(overall_deadline_epoch=HARD_CAP_EPOCH,
        three_day_cap={'first_substantive_build_utc':FIRST_BUILD_UTC,'hard_stop_utc':HARD_CAP_UTC,
            'user_authorized':True,'automatic_extension':False,'individual_retry_protections':'unchanged'},
        screenshot_policy={'at_each_meaningful_milestone':True,'route':'private Library via parent',
            'include':['actual frames','what works','visible problems','next step'],
            'parent_oversight_minutes':10,'duplicate_schedule':False})
    store.event('owner-authorized-three-day-cap',previous_deadline_epoch=old,
                hard_cap_utc=HARD_CAP_UTC,retry_counters_changed=False,plan_pivot=False)
    atomic(store.root/'private-config.json',config)


def deadline_guard(store,current=None):
    current=time.time() if current is None else current
    if store.get('overall_deadline_epoch',HARD_CAP_EPOCH)>HARD_CAP_EPOCH:
        raise Halt('Configured deadline exceeds the owner hard cap')
    if current>=min(HARD_CAP_EPOCH,store.get('overall_deadline_epoch',HARD_CAP_EPOCH)):
        raise Halt('Three-day project cap reached; stop new work and preserve delivery')


def queue_milestone(store,kind,task,bundle,gate,frames,times,review=None):
    """Persist actual rendered artifacts; parent supplies private Library IDs."""
    ident=bundle.name+'--'+kind
    path=store.root/'milestones/outbox'/(ident+'.json')
    old=read_json(path) if path.exists() else {}
    records=[{'path':str(f.relative_to(store.root)),
        'capture_time_utc':dt.datetime.fromtimestamp(f.stat().st_mtime,dt.timezone.utc).isoformat(),
        'replay_seconds':times.get(f.name),'sha256':sha(f.read_bytes())} for f in frames]
    if not records:return None
    value={'milestone_id':ident,'created_utc':old.get('created_utc',now()),'updated_utc':now(),
        'kind':kind,'task':task['id'],'candidate':gate.get('candidate_commit'),
        'build_id':gate.get('build_id'),'native_passed':bool(gate.get('passed')),
        'baseline_regressions':gate.get('regressions','pending'),
        'what_works':gate.get('scoped_facts',{}),
        'visible_problems':review.get('fixes',[]) if review else ['Fresh visual review pending; native PASS is not visual-quality acceptance.'],
        'visual_review':review.get('verdict') if review else 'pending',
        'next_step':store.get('next_task') if kind=='accepted-feature' else 'Continue the current scoped repair or fresh visual review.',
        'actual_native_only':True,'frames':records,'user_can_redirect':True,
        'delivery_status':old.get('delivery_status','pending-parent-private-upload'),
        'library_files':old.get('library_files',[]),'public_upload':False}
    atomic(path,value)
    store.set(latest_milestone_update=str(path.relative_to(store.root)))
    store.event('milestone-screenshots-ready',milestone_id=ident,frames=len(records),
                delivery_status=value['delivery_status'],private_route=True)
    return value


def preserve_closeout(runner,reason,deadline_reached):
    store=runner.store
    value={'closed_utc':now(),'reason':reason,'hard_cap_utc':HARD_CAP_UTC,
        'deadline_reached':deadline_reached,'new_work_allowed':False,
        'saved_candidate':store.get('source_checkpoint'),
        'best_verified_playable_checkpoint':store.get('last_playable_checkpoint'),
        'latest_evidence':store.get('latest_evidence'),
        'latest_milestone_update':store.get('latest_milestone_update'),
        'accepted_subfeatures':list(store.get('accepted_subfeatures',{})),
        'accepted_queue_features':list(store.get('accepted_queue_features',{})),
        'final_game_accepted':False,'quality_statement':'Scoped tests do not establish final appearance, audio or overall game quality.',
        'remaining_task':store.get('current_task'),'next_task':store.get('next_task'),
        'failure_streak':store.get('failure_streak'),'task_failures':store.get('task_failures'),
        'artifacts_preserved':'Existing immutable evidence bundles, source commits and local provenance remain in place.'}
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    atomic(store.root/'closeouts'/(stamp+'.json'),value)
    atomic(store.root/'FINAL-HANDOFF.json',value)
    store.set(closeout=value);store.event('honest-delivery-closeout',**value)
    return value
