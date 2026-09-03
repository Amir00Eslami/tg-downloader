import os
import sys
import math
import asyncio
import requests
from telethon import TelegramClient
from telethon.sessions import StringSession

# ============ تنظیمات ============
API_ID = int(os.environ.get('API_ID', '0'))
API_HASH = os.environ.get('API_HASH', '')
DOWNLOAD_URL = os.environ.get('DOWNLOAD_URL', '')
CHUNK_SIZE = 50 * 1024 * 1024  # 50 مگابایت
MAX_RETRIES = 5
# ==================================

def download_file(url, filename='downloaded_file'):
    """دانلود فایل از لینک مستقیم با retry"""
    print(f"\n📥 دانلود در حال شروع...")
    print(f"🔗 لینک: {url[:100]}...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"\n🔄 تلاش {attempt}/{MAX_RETRIES}...")
            
            response = requests.get(url, stream=True, headers=headers, timeout=(30, 600))
            total_size = int(response.headers.get('content-length', 0))
            
            if total_size > 0:
                size_mb = total_size / (1024 * 1024)
                print(f"📊 حجم فایل: {size_mb:.1f} مگابایت")
            
            downloaded = 0
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0 and downloaded % (5*1024*1024) < 65536:
                            percent = (downloaded / total_size) * 100
                            mb = downloaded / (1024*1024)
                            print(f"📥 {percent:.1f}% ({mb:.0f} مگ)", flush=True)
            
            final_size = os.path.getsize(filename)
            if total_size > 0 and final_size < total_size * 0.99:
                print(f"⚠️ فایل ناقص دانلود شد! ({final_size}/{total_size})")
                if attempt < MAX_RETRIES:
                    continue
            
            print(f"✅ دانلود تموم شد! ({final_size / (1024*1024):.1f} مگ)")
            return filename
            
        except Exception as e:
            print(f"❌ خطا: {e}")
            if attempt < MAX_RETRIES:
                print(f"⏳ ۱۰ ثانیه صبر کن...")
                import time
                time.sleep(10)
            else:
                print(f"❌ تمام تلاش‌ها تموم شد!")
                raise
    
    return filename

def split_file(filename):
    """پارت بندی فایل"""
    file_size = os.path.getsize(filename)
    total_parts = math.ceil(file_size / CHUNK_SIZE)
    
    print(f"\n📦 پارت بندی فایل...")
    print(f"📊 حجم کل: {file_size / (1024*1024):.1f} مگابایت")
    print(f"📦 تعداد پارت‌ها: {total_parts}")
    
    parts = []
    with open(filename, 'rb') as f:
        for i in range(total_parts):
            part_name = f"part_{i+1:03d}"
            data = f.read(CHUNK_SIZE)
            with open(part_name, 'wb') as pf:
                pf.write(data)
            parts.append(part_name)
            size_mb = len(data) / (1024*1024)
            print(f"  ✅ پارت {i+1}/{total_parts}: {size_mb:.1f} مگ")
    
    return parts

async def upload_parts(parts, filename):
    """آپلود پارت‌ها به Saved Messages"""
    print(f"\n📤 آپلود به Saved Messages...")
    
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.start()
    
    total = len(parts)
    
    await client.send_message('me', f"📁 شروع آپلود: {filename}\n📦 تعداد پارت‌ها: {total}")
    
    for i, part in enumerate(parts):
        size_mb = os.path.getsize(part) / (1024*1024)
        print(f"\n📤 آپلود پارت {i+1}/{total} ({size_mb:.1f} مگ)...")
        
        await client.send_file(
            'me',
            part,
            caption=f"📦 {filename} | پارت {i+1}/{total}"
        )
        print(f"  ✅ پارت {i+1} آپلود شد!")
    
    await client.send_message('me', f"✅ آپلود تموم شد!\n📁 {filename}\n📦 {total} پارت")
    
    print(f"\n🎉 همه پارت‌ها آپلود شد!")
    await client.disconnect()

def cleanup(filename, parts):
    """پاک کردن فایل‌های موقت"""
    print(f"\n🧹 پاک کردن فایل‌های موقت...")
    if os.path.exists(filename):
        os.remove(filename)
    for part in parts:
        if os.path.exists(part):
            os.remove(part)
    print("✅ تمیز شد!")

async def main():
    print("=" * 50)
    print("🚀 دانلودر و آپلودر تلگرام")
    print("📁 پارت بندی خودکار 50 مگابایتی")
    print("=" * 50)
    
    if not DOWNLOAD_URL:
        print("❌ لینک دانلود تعریف نشده!")
        return
    
    if not API_ID or not API_HASH:
        print("❌ API_ID یا API_HASH تعریف نشده!")
        return
    
    filename = 'downloaded_file'
    try:
        name_from_url = DOWNLOAD_URL.split('/')[-1].split('?')[0]
        if name_from_url and '.' in name_from_url:
            filename = name_from_url
    except:
        pass
    
    filename = download_file(DOWNLOAD_URL, filename)
    parts = split_file(filename)
    await upload_parts(parts, filename)
    cleanup(filename, parts)
    
    print("\n🎉 تموم شد!")

if __name__ == '__main__':
    asyncio.run(main())
