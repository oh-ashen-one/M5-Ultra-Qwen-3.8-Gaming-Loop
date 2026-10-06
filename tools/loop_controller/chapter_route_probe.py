"""Bounded ordinary-input composition from measured native car pose; no actor writes."""
import copy
import math
from .core import Halt
from .continuous_checks import scenario

ANCHOR=[50,.14,18]
REVERSE_START=16.
REVERSE_END=20.4
TURN_START=21.4

def courier_prefix(activation):
    return [copy.deepcopy(s) for s in activation['steps'] if s['end']<=14.6 and 'R' not in s['keys']]

def pilot(activation,turn_seconds):
    if not .8<=turn_seconds<=2.5:raise Halt('Bounded steering measurement exceeds authorized interval')
    turn_end=TURN_START+turn_seconds;stop=turn_end+.65
    steps=courier_prefix(activation)+[
        {'start':REVERSE_START,'end':REVERSE_END,'keys':['S']},
        {'start':16.,'end':16.3,'keys':['F']},
        {'start':TURN_START,'end':turn_end,'keys':['W','D']},
        {'start':turn_end,'end':stop,'keys':['W']},
        {'start':stop,'end':stop+.3,'keys':['E']}]
    captures=sorted(set([3.2,7.9,14.,15.2,19.6,turn_end+.1,stop+.5,stop+1.5]))
    return dict(id='chapter-steering-measure',coverage='mission-core',duration=stop+2,steps=steps,captures=captures),stop

def measured_pose(rows,stop):
    settled=[r for r in rows if stop+.5<=r['time']<=stop+1.5]
    if len(settled)<3 or any(r.get('mode')!='foot' or not r.get('grounded') or r.get('restarts',0)!=0 for r in settled):
        raise Halt('Native pilot did not stop through the actual E exit')
    row=settled[-1];p=row.get('vehicle');physics=row.get('vehiclePhysics',{})
    yaw=physics.get('yaw');f=physics.get('forward')
    if not p or len(p)!=3 or not f or len(f)!=3 or not isinstance(yaw,(int,float)) or not all(math.isfinite(v) for v in p+f+[yaw]):
        raise Halt('Native car pose is missing or nonfinite')
    if not 2<=p[0]<=22 or not 9.3<=p[2]<=17.8 or not -.2<=p[1]<=.4:
        raise Halt('Native pilot did not reach a grounded clear alley approach')
    drive=[r for r in rows if r['time']>=16 and r.get('mode')=='vehicle']
    if not drive or any(not r.get('vehicleCollisionEnabled') or r.get('vehiclePenetration',999)>.15 for r in drive):
        raise Halt('Preserve actual vehicle collision/penetration failure before route extrapolation')
    error=(90-yaw+180)%360-180
    return dict(position=p,forward=f,yaw=yaw,error_degrees=error,time=row['time'])

def corrected_turn(turn_seconds,error):
    proposed=turn_seconds+error/65.
    if not .8<=proposed<=2.5:raise Halt('Measured steering correction exceeds bounded maneuver')
    return round(proposed,4)

def full_route(activation,turn_seconds,pose):
    if abs(pose['error_degrees'])>3:raise Halt('Require a measured near-east heading before composing the long leg')
    probe,stop=pilot(activation,turn_seconds)
    steps=copy.deepcopy(probe['steps'])
    reenter=stop+1.1;throttle=reenter+.7
    f=pose['forward'];p=pose['position']
    if f[0]<.95:raise Halt('Measured car heading is not eastward')
    distance=(48-p[0])/f[0]
    # Known game acceleration6m/s2, speed cap8m/s. Native proof, not this
    # arithmetic, decides success. The E edge immediately stops the actual car.
    travel=(distance+8*8/(2*6))/8
    arrival=throttle+travel
    steps += [{'start':reenter,'end':reenter+.3,'keys':['E']},
              {'start':throttle,'end':arrival,'keys':['W']},
              {'start':arrival-.5,'end':arrival-.2,'keys':['F']},
              {'start':arrival,'end':arrival+.3,'keys':['E']}]
    predicted_x=p[0]+distance*f[0]-f[2]*1.5
    predicted_z=p[2]+distance*f[2]+f[0]*1.5
    current=arrival+.55
    for amount,pos,neg in [(18-predicted_z,'W','S'),(50-predicted_x,'D','A')]:
        duration=abs(amount)/3.2
        if duration>.04:
            steps.append({'start':current,'end':current+duration,'keys':[pos if amount>0 else neg]})
            current+=duration+.12
    interact=current+.2;reset=interact+1.5
    steps += [{'start':interact,'end':interact+.3,'keys':['F']},
              {'start':reset,'end':reset+.3,'keys':['R']},
              {'start':reset+1,'end':reset+1.3,'keys':['F']}]
    captures=sorted(set(probe['captures']+[throttle+2,arrival-.3,arrival+.4,interact+.6,reset+.6,reset+1.6]))
    return dict(id='east-dead-drop-measured-normal-input',coverage='mission-core',
        duration=reset+2,steps=steps,captures=captures)

def chapter_capture_selection(frames,scenario,rows):
    observed=[]
    for frame in frames:
        index=int(frame.stem.split('-')[-1]);t=scenario['captures'][index]
        row=min(rows,key=lambda r:abs(r['time']-t))
        if abs(row['time']-t)<=.25:observed.append((frame,row))
    active=[p for p in observed if p[1].get('routeChapter',{}).get('stage')==1]
    driving=[p for p in active if p[1].get('mode')=='vehicle' and p[1].get('vehicle')]
    done=[p for p in observed if p[1].get('routeChapter',{}).get('stage')==2]
    result=[]
    if active:result.append(active[0][0])
    if driving:
        result.append(min(driving,key=lambda p:abs(p[1]['vehicle'][0]-22))[0])
        result.append(min(driving,key=lambda p:math.dist([p[1]['vehicle'][0],p[1]['vehicle'][2]],[50,18]))[0])
    if done:
        result.append(done[0][0])
        reset=[p for p in observed if p[1]['time']>done[0][1]['time'] and
            p[1].get('restarts',0)>done[0][1].get('restarts',0) and p[1].get('routeChapter',{}).get('stage')==0]
        if reset:result.append(reset[0][0])
    return sorted(set(result))
