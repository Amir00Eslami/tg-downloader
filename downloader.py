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
# ==================================

def download_file(url, filename='downloaded_file'):
    """دانلود فایل از لینک مستقیم"""
    print(f"\n📥 دانلود در حال شروع...")
    print(f"🔗 لینک: {url[:80]}...")
    
    response = requests.get(url, stream=True, timeout=300)
    total_size = int(response.headers.get('content-length', 0))
    
    if total_size > 0:
        size_mb = total_size / (1024 * 1024)
        print(f"📊 حجم فایل: {size_mb:.1f} مگابایت")
    
    downloaded = 0
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0 and downloaded % (1024*1024) < 8192:
                percent = (downloaded / total_size) * 100
                print(f"📥 دانلود: {percent:.1f}%", flush=True)
    
    print(f"✅ دانلود تموم شد!")
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
    
    # پیام شروع
    await client.send_message('me', f"📁 شروع آپلود فایل: {filename}\n📦 تعداد پارت‌ها: {total}")
    
    for i, part in enumerate(parts):
        size_mb = os.path.getsize(part) / (1024*1024)
        print(f"\n📤 آپلود پارت {i+1}/{total} ({size_mb:.1f} مگ)...")
        
        await client.send_file(
            'me',
            part,
            caption=f"📦 {filename} | پارت {i+1}/{total}"
        )
        print(f"  ✅ پارت {i+1} آپلود شد!")
    
    # پیام پایان
    await client.send_message('me', f"✅ آپلود تموم شد!\n📁 فایل: {filename}\n📦 تعداد پارت‌ها: {total}")
    
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
    print("📤 آپلود به Saved Messages")
    print("=" * 50)
    
    if not DOWNLOAD_URL:
        print("❌ لینک دانلود تعریف نشده!")
        return
    
    if not API_ID or not API_HASH:
        print("❌ API_ID یا API_HASH تعریف نشده!")
        return
    
    # دانلود
    filename = 'downloaded_file'
    
    # تلاش برای گرفتن اسم فایل از لینک
    try:
        name_from_url = DOWNLOAD_URL.split('/')[-1].split('?')[0]
        if name_from_url and '.' in name_from_url:
            filename = name_from_url
    except:
        pass
    
    filename = download_file(DOWNLOAD_URL, filename)
    
    # پارت بندی
    parts = split_file(filename)
    
    # آپلود
    await upload_parts(parts, filename)
    
    # پاک کردن
    cleanup(filename, parts)
    
    print("\n🎉 تموم شد!")

if __name__ == '__main__':
    asyncio.run(main())
