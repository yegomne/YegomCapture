import os
try:
    from PIL import Image
    import sys
    
    img_path = r"C:\Users\User\.gemini\antigravity\brain\4eb3c25d-ce65-4051-ab2d-49d50076d905\capture_app_icon_1774601720843.png"
    out_path = r"e:\캡쳐프로그램\icon.ico"
    
    if os.path.exists(img_path):
        img = Image.open(img_path)
        img.save(out_path, format="ICO", sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
        print(f"Successfully converted to {out_path}")
    else:
        print("Image not found.")
except Exception as e:
    print(f"Error: {e}")
