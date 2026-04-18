import os
import runpy
os.environ['MAM_AUTOPILOT'] = '1'
print('MAM_AUTOPILOT=', os.environ['MAM_AUTOPILOT'])
runpy.run_path('MaM_EAT_run copy.py', run_name='__main__')
