"""Independent pin interruption/reset evidence from ordinary driving inputs."""
from .counter_exfil_checks import chapter,values
from .counter_exfil_success_checks import physical_pins,NAMES

def inspect_contact_release(rows,events,release_at=115,reset_at=123):
    failures=[];qualified=[]
    for row in rows:
        if row.get('restarts')==0 and 99<=row['time']<release_at:
            pins=physical_pins(rows,events,row)
            if pins:qualified.append((row,pins))
    if not qualified:failures.append('actual-continuously-obstructed-pin-before-release-missing')
    release=None
    for row,pins in reversed(qualified):
        for pin in pins:
            exits=[e for e in events if e.get('entityId')==pin['entity_id'] and e.get('otherIsVehicle')
                and e.get('kind')=='exit' and release_at<=e['time']<reset_at]
            for event in exits:
                reentry=min([e['time'] for e in events if e.get('entityId')==pin['entity_id'] and e.get('otherIsVehicle')
                    and e.get('kind') in ('enter','stay') and e.get('contacts') and e['time']>event['time']]+[reset_at])
                after=[r for r in rows if event['time']+1e-4<r['time']<min(reentry,reset_at)
                    and r.get('restarts')==0]
                if len(after)<2 or after[0]['time']-event['time']>.15:continue
                actors=[next((a for a in r.get('counterExfil',{}).get('actors',[]) if a['entityId']==pin['entity_id']),None) for r in after]
                if any(a is None or not a.get('alive') for a in actors):continue
                if any(values(a.get('state')).get('hold',999)!=0 or any(c.get('vehicle') for c in a.get('contacts',[])) for a in actors):
                    failures.append('pin-credit-survives-real-contact-separation')
                if any(p['entity_id']==pin['entity_id'] for r in after for p in physical_pins(rows,events,r)):
                    failures.append('external-pin-proof-survives-real-contact-separation')
                release=dict(actor=pin['name'],qualified_time=row['time'],qualified=pin,
                    actual_collision_exit=event['time'],first_sample=after[0]['time'],separated_samples=len(after),
                    last_separated_sample=after[-1]['time'],reentry=reentry if reentry<reset_at else None)
                break
            if release:break
        if release:break
    if release is None:failures.append('qualified-pin-then-ordinary-contact-interruption-not-established')
    active=[r for r in rows if r.get('restarts')==0 and chapter(r).get('Active')]
    if not active or any(chapter(r).get('Complete') or chapter(r).get('KilledCount')!=0 for r in active):
        failures.append('unearned-completion-or-kill-credit-during-contact-negative')
    reset=[r for r in rows if reset_at+.4<=r['time']<=reset_at+1.2 and r.get('restarts')==1]
    if len(reset)<4 or any(not chapter(r).get('Dormant') or r.get('counterExfil',{}).get('actors')
            or any(chapter(r).get(k) for k in ('Armed','Active','Complete','Failed','KilledCount','EscapedCount','ActiveTime')) for r in reset):
        failures.append('contact-negative-R-reset-not-established')
    return dict(passed=not failures,failure=sorted(set(failures)),release=release,
        physical_pin_samples=len(qualified),reset_samples=len(reset),
        scope='Actual pin, ordinary reverse departure, immediate credit loss and R cleanup only',final_game_accepted=False)
