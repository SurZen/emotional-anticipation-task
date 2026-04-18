import os
import urllib.request

urls = [
    'https://storage.googleapis.com/mediapipe-assets/face_landmarker.task',
    'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker.task',
    'https://storage.googleapis.com/mediapipe/face_landmarker/face_landmarker.task',
]
out = os.path.join(os.path.dirname(__file__), 'face_landmarker.task')
print('Output path:', out)
for u in urls:
    try:
        print('Trying', u)
        urllib.request.urlretrieve(u, out)
        print('DL_OK', u)
        break
    except Exception as e:
        print('DL_FAIL', u, str(e))

if not os.path.exists(out):
    print('NO_FILE')
else:
    st = os.stat(out)
    print('FILE', out, st.st_size)
