"""Independent observations of fixed mission objectives and real pickup/delivery input."""
import math


def xz(point):
    return [point[0], point[2]]


def actor_child(obj):
    return obj.get('playerChild',False) or obj.get('vehicleChild',False)


def inspect_mission_anchors(rows):
    failures = []
    samples = []
    for row in rows:
        objects = {o['name']: o for o in row.get('missionObjects', [])}
        if objects:
            samples.append((row, objects))
    if not samples:
        return {'passed': False, 'failure': ['mission-object-observations-missing']}
    first, initial = samples[0]
    for name in ('Parcel', 'DropPad', 'Beacon'):
        if name not in initial:
            failures.append('initial-' + name + '-missing')
        elif actor_child(initial[name]):
            failures.append('initial-' + name + '-follows-player')
    carried = next((r['time'] for r, obj in samples if actor_child(obj.get('Parcel', {}))), None)
    for row, objects in samples:
        for name in ('DropPad', 'Beacon', 'Parcel'):
            obj = objects.get(name)
            if name == 'Parcel' and carried is not None and row['time'] >= carried and (not obj or actor_child(obj)):
                continue
            if not obj or name not in initial:
                failures.append(name + '-observation-missing')
                continue
            coords=xz if name=='Parcel' else lambda p:p
            if actor_child(obj) or math.dist(coords(obj['position']), coords(initial[name]['position'])) > .05:
                failures.append(name + '-world-anchor-moved')
    before_pickup = [(r, obj) for r, obj in samples if carried is None or r['time'] < carried]
    away = None
    returned = None
    if 'Parcel' in initial and first.get('player'):
        start_distance = math.dist(xz(first['player']), xz(initial['Parcel']['position']))
        for row, obj in before_pickup:
            if not row.get('player') or 'Parcel' not in obj:
                continue
            distance = math.dist(xz(row['player']), xz(obj['Parcel']['position']))
            if away is None and distance >= start_distance + 1:
                away = row['time']
            elif away is not None and row['time'] > away and distance <= 1.5:
                returned = row['time']
                break
    if away is None or returned is None:
        failures.append('walk-away-and-return-before-pickup-unverified')
    pickup_rows = [r for r, _ in samples if carried is not None and 0 <= carried-r['time'] <= .35]
    if carried is None or not any('F' in r.get('keys', []) for r in pickup_rows):
        failures.append('normal-input-pickup-unverified')
    completed = next((r for r, _ in samples if r.get('mission') == 'complete'), None)
    delivery_rows = [r for r, _ in samples if completed and 0 <= completed['time']-r['time'] <= .35]
    if (not completed or carried is None or completed['time'] <= carried
            or not any(r.get('mode') == 'vehicle' and 'F' in r.get('keys', []) for r in delivery_rows)):
        failures.append('normal-input-vehicle-delivery-unverified')
    if completed and 'DropPad' in initial:
        actual = completed.get('vehicle') if completed.get('mode') == 'vehicle' else completed.get('player')
        if not actual or math.dist(xz(actual), xz(initial['DropPad']['position'])) > 2.6:
            failures.append('delivery-not-at-fixed-destination')
    attempts=[];held=False;closest=None
    for row,objects in samples:
        pressed='F' in row.get('keys',[])
        pad=objects.get('DropPad');vehicle=row.get('vehicle')
        if row.get('mode')=='vehicle' and pad and vehicle:
            observation={'time':row['time'],'vehicle':vehicle,'pad':pad['position'],
                'distance_xz_m':math.dist(xz(vehicle),xz(pad['position'])),
                'mission':row.get('mission'),'restarts':row.get('restarts',0),
                'collision_enabled':row.get('vehicleCollisionEnabled'),
                'penetration_m':row.get('vehiclePenetration')}
            if closest is None or observation['distance_xz_m']<closest['distance_xz_m']:closest=observation
            if pressed and not held:attempts.append(observation)
        held=pressed
    return {'passed': not failures, 'failure': sorted(set(failures)), 'away_seconds': away,
            'returned_seconds': returned, 'pickup_seconds': carried,
            'delivery_seconds': completed['time'] if completed else None,
            'sample_count': len(samples), 'scope': 'fixed-world-objectives-and-input-transitions',
            'delivery_input_edges':attempts[-8:],'closest_driving_approach':closest,
            'final_visual_acceptance': False}
