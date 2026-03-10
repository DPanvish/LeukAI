"""Quick test of Grad-CAM heatmap."""
import requests, os, sys

BASE = 'http://localhost:8000'

# Login
login = requests.post(f'{BASE}/api/auth/login', 
                       json={'username': 'admin', 'password': 'admin123'})
token = login.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Pick a test image
test_img = r'E:\Leukemia\dataset\test\Pro-B\Snap_019.jpg'
if not os.path.exists(test_img):
    # Try finding any image
    import glob
    imgs = glob.glob(r'E:\Leukemia\dataset\test\*\*')
    test_img = imgs[0] if imgs else None
    
if not test_img:
    print("No test image found!")
    sys.exit(1)

print(f"Testing with: {test_img}")

with open(test_img, 'rb') as f:
    resp = requests.post(
        f'{BASE}/api/predict/upload',
        headers=headers,
        files={'file': (os.path.basename(test_img), f, 'image/png')},
        data={'patient_name': 'GradCAM-Test', 'patient_id': 'GC-001'}
    )

if resp.status_code == 200:
    result = resp.json()
    print(f"Classification: {result['classification']}")
    print(f"Confidence: {result['confidence']*100:.1f}%")
    
    # Check heatmap - decode and analyze
    import base64
    heatmap_bytes = base64.b64decode(result['heatmap_base64'])
    
    # Save for inspection
    with open('test_heatmap.png', 'wb') as f:
        f.write(heatmap_bytes)
    print(f"Heatmap saved to test_heatmap.png ({len(heatmap_bytes)} bytes)")
    
    # Analyze pixel variance
    from PIL import Image
    import io
    import numpy as np
    img = Image.open(io.BytesIO(heatmap_bytes))
    arr = np.array(img)
    
    # Check if heatmap has actual variation
    print(f"Heatmap shape: {arr.shape}")
    print(f"Pixel value range: min={arr.min()}, max={arr.max()}")
    print(f"Pixel std: R={arr[:,:,0].std():.2f} G={arr[:,:,1].std():.2f} B={arr[:,:,2].std():.2f}")
    
    # Check if there are actual hot/warm regions
    # A good heatmap should have varied colors (reds, yellows, greens, blues)
    # A flat one would have low std
    total_std = arr.astype(float).std()
    print(f"Total pixel std: {total_std:.2f}")
    if total_std > 30:
        print("RESULT: Heatmap has GOOD variation - Grad-CAM is working!")
    else:
        print("RESULT: Heatmap appears FLAT - Grad-CAM may not be working")
        
    print(f"\nRecord ID: {result['id']}")
else:
    print(f"ERROR: {resp.status_code}")
    print(resp.text)
