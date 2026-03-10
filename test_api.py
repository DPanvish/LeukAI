"""Test the v2 model with real images from each class."""
import requests, json, os, glob

BASE = 'http://localhost:8000'

# Login
login = requests.post(f'{BASE}/api/auth/login', 
                       json={'username': 'admin', 'password': 'admin123'})
token = login.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}
print("Logged in successfully\n")

# Test one image from each class
test_dir = 'E:/Leukemia/dataset/test'
classes = ['Benign', 'Early Pre-B', 'Pre-B', 'Pro-B']

print(f"{'Class':<15} {'Predicted':<15} {'Confidence':>10} {'Correct':>8}")
print("-" * 55)

correct = 0
total = 0

for cls in classes:
    folder = os.path.join(test_dir, cls)
    images = glob.glob(os.path.join(folder, '*'))[:5]  # test 5 from each
    
    for img_path in images:
        fname = os.path.basename(img_path)
        with open(img_path, 'rb') as f:
            resp = requests.post(
                f'{BASE}/api/predict/upload',
                headers=headers,
                files={'file': (fname, f, 'image/png')},
                data={'patient_name': f'Test-{cls}', 'patient_id': f'TEST-{total+1}'}
            )
        
        if resp.status_code == 200:
            result = resp.json()
            pred = result['classification']
            conf = result['confidence'] * 100
            is_correct = pred == cls
            correct += int(is_correct)
            mark = 'YES' if is_correct else 'NO'
            print(f"{cls:<15} {pred:<15} {conf:>9.1f}% {mark:>8}")
        else:
            print(f"{cls:<15} ERROR {resp.status_code}")
        
        total += 1

print("-" * 55)
print(f"\nTest Accuracy: {correct}/{total} = {100*correct/total:.1f}%")
