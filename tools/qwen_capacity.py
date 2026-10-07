"""Opt-in, measured Qwen-only capacity trial; never manages another workload."""
import ctypes
import datetime
import json
from pathlib import Path
import re
import subprocess
import time

GIB = 1024**3
MIB = 1024**2
POLICY = 'simultaneous-capacity-trial-v2'
# Explicit trial allowances, not claimed physical crash thresholds:
# observed model footprint139.7GiB ->140; measured Unreal peak30.7 ->40.
# OS16 follows the official safe tier's maximum reserve; request8 and
# sampling/exit8 are extra allowances. Existing other-app memory is already
# deducted from available; reserve only Unreal's remaining envelope growth.
MODEL_RESIDENT_GIB = 140
LOAD_TRANSIENT_GIB = 8
UNREAL_ENVELOPE_GIB = 40
OS_RESERVE_GIB = 16
REQUEST_TRANSIENT_GIB = 8
EXIT_ALLOWANCE_GIB = 8
COMPRESSION_RULE = dict(window_seconds=30, persistence_seconds=10,
    growth_or_churn_gib=2, swapout_mib=64, low_budget_margin_gib=8, settling_seconds=30)


def assess(sample, baseline, phase='steady'):
    if phase not in ('load','settle','steady'):
        raise ValueError('Explicit load, settle or steady phase required')
    unreal = sample['unreal_bytes']/GIB
    growth = max(0, UNREAL_ENVELOPE_GIB-unreal)
    reserve = OS_RESERVE_GIB+REQUEST_TRANSIENT_GIB+EXIT_ALLOWANCE_GIB+growth
    remaining_load=max(0,MODEL_RESIDENT_GIB+LOAD_TRANSIENT_GIB-sample['qwen_bytes']/GIB) if phase=='load' else 0
    required = reserve + remaining_load
    swap_growth = max(0,sample['swap_bytes']-baseline['swap_bytes'])/MIB
    compression_growth = max(0,sample['compressed_bytes']-baseline['compressed_bytes'])/GIB
    failures=[]
    if sample['available_bytes']/GIB < required:failures.append('measured-capacity-budget')
    if unreal > UNREAL_ENVELOPE_GIB:failures.append('unreal-exceeds-measured-trial-envelope')
    if sample['qwen_bytes']/GIB > 192:failures.append('qwen-footprint-above192GiB')
    if swap_growth > 512:failures.append('swap-growth-above512MiB')
    if sample['pressure_level'] != 1:failures.append('OS-memory-pressure')
    if sample.get('thermal_warning') is not None and sample['thermal_warning'] > 0:
        failures.append('OS-thermal-warning')
    return dict(policy=POLICY,phase=phase,available_gib=sample['available_bytes']/GIB,
        qwen_footprint_gib=sample['qwen_bytes']/GIB,unreal_footprint_gib=unreal,
        unreal_future_growth_gib=growth,os_reserve_gib=OS_RESERVE_GIB,
        request_transient_gib=REQUEST_TRANSIENT_GIB,exit_allowance_gib=EXIT_ALLOWANCE_GIB,
        model_load_budget_gib=MODEL_RESIDENT_GIB+LOAD_TRANSIENT_GIB if phase=='load' else 0,
        remaining_model_load_gib=remaining_load,
        required_available_gib=required,swap_growth_mib=swap_growth,
        compression_growth_gib=compression_growth,pressure_level=sample['pressure_level'],
        failure=failures,passed=not failures,model_quality_changed=False)


class CompressionWatch:
    """Distinguish retained compressed pages from sustained reclamation stress.

    The thresholds are explicit trial heuristics, not Apple limits. Immediate
    headroom, pressure, swap and thermal checks remain independent in assess().
    Keep the rolling window across phase transitions; only the descriptive
    phase baseline changes, so settling cannot hide ongoing churn.
    """
    def __init__(self):
        self.history=[];self.phase=None;self.phase_baseline=0;self.stressed_since=None

    def observe(self, sample, budget, at):
        rule=COMPRESSION_RULE
        if self.phase != budget['phase']:
            self.phase=budget['phase'];self.phase_baseline=sample['compressed_bytes']
        if self.history and at-self.history[-1][0]>10:
            self.history=[];self.stressed_since=None
        self.history.append((at,dict(sample)))
        while len(self.history)>1 and self.history[1][0] <= at-rule['window_seconds']:
            self.history.pop(0)
        then,first=self.history[0];elapsed=at-then
        def delta(key,unit):return max(0,sample.get(key,0)-first.get(key,0))/unit
        growth=delta('compressed_bytes',GIB)
        compressed=delta('compression_bytes',GIB);decompressed=delta('decompression_bytes',GIB)
        swapout=delta('swapout_bytes',MIB)
        margin=budget['available_gib']-budget['required_available_gib']
        reclaiming=growth>rule['growth_or_churn_gib'] or min(compressed,decompressed)>rule['growth_or_churn_gib']
        corroborated=swapout>rule['swapout_mib'] or margin<rule['low_budget_margin_gib']
        stressed=elapsed>=rule['window_seconds'] and reclaiming and corroborated
        if stressed:
            if self.stressed_since is None:self.stressed_since=at
        else:self.stressed_since=None
        duration=0 if self.stressed_since is None else at-self.stressed_since
        return dict(phase=self.phase,phase_growth_gib=max(0,sample['compressed_bytes']-self.phase_baseline)/GIB,
            window_seconds=round(elapsed,3),window_growth_gib=growth,
            window_compressed_gib=compressed,window_decompressed_gib=decompressed,
            window_swapout_mib=swapout,budget_margin_gib=margin,
            corroborated_reclamation_stress=stressed,persistence_seconds=round(duration,3),
            failure=stressed and duration>=rule['persistence_seconds'])


class Usage(ctypes.Structure):
    _fields_=[('uuid',ctypes.c_ubyte*16)]+[(name,ctypes.c_uint64) for name in
        ('user','system','idle','interrupt','pageins','wired','resident','footprint','start','exit')]


class Budget:
    def __init__(self, journal=None):
        import psutil
        self.psutil=psutil
        self.lib=ctypes.CDLL('/usr/lib/libproc.dylib',use_errno=True)
        self.lib.proc_pid_rusage.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_void_p]
        self.pid=None;self.pid_start=None;self.journal=Path(journal) if journal else None
        self.baseline=self.sample()
        self.compression=CompressionWatch()
        self.latest=None;self.last_at=0

    def set_owned_pid(self,pid):
        self.pid=int(pid);self.pid_start=self.psutil.Process(self.pid).create_time()
        self.last_at=0

    def footprint(self,pid):
        value=Usage()
        if self.lib.proc_pid_rusage(pid,0,ctypes.byref(value)) != 0:
            raise RuntimeError('Cannot measure required process physical footprint')
        return value.footprint

    def sample(self):
        vm=subprocess.check_output(['/usr/bin/vm_stat'],text=True,timeout=5)
        page=int(re.search(r'page size of (\d+) bytes',vm).group(1))
        compressed=int(re.search(r'Pages occupied by compressor:\s+(\d+)',vm).group(1))*page
        counters={key:int(re.search(label+r':\s+(\d+)',vm).group(1))*page for key,label in
            (('compression_bytes','Compressions'),('decompression_bytes','Decompressions'),('swapout_bytes','Swapouts'))}
        pressure=int(subprocess.check_output(['/usr/sbin/sysctl','-n',
            'kern.memorystatus_vm_pressure_level'],text=True,timeout=5).strip())
        unreal=[]
        for process in self.psutil.process_iter(['pid','name','create_time']):
            if (process.info.get('name') or '').startswith('UnrealEditor'):
                try:
                    size=self.footprint(process.pid)
                    if process.is_running():unreal.append(dict(pid=process.pid,
                        start=process.info['create_time'],footprint_bytes=size))
                except (self.psutil.NoSuchProcess,ProcessLookupError):continue
                except RuntimeError:
                    if not process.is_running():continue
                    raise
        qwen=0
        if self.pid is not None:
            owned=self.psutil.Process(self.pid)
            if abs(owned.create_time()-self.pid_start)>.01:
                raise RuntimeError('Owned Qwen process identity changed')
            qwen=self.footprint(self.pid)
        return dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            available_bytes=self.psutil.virtual_memory().available,
            swap_bytes=self.psutil.swap_memory().used,compressed_bytes=compressed,
            pressure_level=pressure,unreal_bytes=sum(x['footprint_bytes'] for x in unreal),
            unreal=unreal,qwen_bytes=qwen,**counters)

    def observe(self,phase='steady',thermal_warning=None):
        # Fast source/tool guard calls may share a <=1second observation.
        if self.latest and time.monotonic()-self.last_at<1 and self.latest['phase']==phase:
            result=dict(self.latest)
            if thermal_warning is not None and thermal_warning>0:
                result['failure']=list(set(result['failure']+['OS-thermal-warning']));result['passed']=False
            return result
        sample=self.sample();sample['thermal_warning']=thermal_warning
        result=assess(sample,self.baseline,phase);result.update(utc=sample['utc'],sample=sample)
        compression=self.compression.observe(sample,result,time.monotonic())
        result['compression_watch']=compression
        if compression['failure']:
            result['failure'].append('sustained-compression-with-reclamation-stress');result['passed']=False
        self.latest=result;self.last_at=time.monotonic()
        if self.journal:
            self.journal.parent.mkdir(parents=True,exist_ok=True)
            with self.journal.open('a') as stream:stream.write(json.dumps(result)+'\n')
        return result
