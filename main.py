"""
🔥 OpenSea Mint Monitor Bot v2.0 🔥
Bot untuk monitor countdown mint dari akun OpenSea favorit kamu
+ Command Telegram untuk manage watchlist!
"""

import requests
import time
from datetime import datetime
import json
import threading
import re

# ==================== KONFIGURASI ====================
# Copy paste Token dan Chat ID kamu di sini:
TELEGRAM_BOT_TOKEN = "8379961868:AAHVZly7SPoZdaHBOu0m2zS_syGG1rO3C8U"
TELEGRAM_CHAT_ID = "558513540"

# Interval pengecekan (dalam detik)
# 3600 = 1 jam, 1800 = 30 menit
CHECK_INTERVAL = 3600  # Cek setiap 1 jam

# File untuk menyimpan data
WATCHLIST_FILE = "watchlist.json"
SENT_COLLECTIONS_FILE = "sent_collections.json"

# ==================== WATCHLIST MANAGEMENT ====================

def load_watchlist():
    """Load watchlist dari file"""
    try:
        with open(WATCHLIST_FILE, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except:
        # Default watchlist kalau file belum ada
        default = ["doodles", "boredapeyc", "azuki"]
        save_watchlist(default)
        return default

def save_watchlist(watchlist):
    """Simpan watchlist ke file"""
    with open(WATCHLIST_FILE, 'w') as f:
        json.dump(watchlist, f, indent=2)

def extract_username_from_url(text):
    """Ekstrak username dari link OpenSea"""
    # Pattern untuk berbagai format URL OpenSea
    patterns = [
        r'opensea\.io/([^/?\s]+)',  # opensea.io/username
        r'opensea\.io/collection/([^/?\s]+)',  # opensea.io/collection/name
        r'@(\w+)',  # @username
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            username = match.group(1)
            # Bersihkan username dari karakter aneh
            username = username.strip().lower()
            return username
    
    # Kalau gak ada pattern yang match, anggap sebagai username langsung
    return text.strip().lower()

# ==================== TELEGRAM FUNCTIONS ====================

def send_telegram_message(message):
    """Kirim pesan ke Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Gagal kirim pesan: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_telegram_updates(offset=None):
    """Ambil update/message dari Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"timeout": 30, "offset": offset}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"❌ Error getting updates: {e}")
        return None

def handle_command(message_text, chat_id):
    """Handle command dari Telegram"""
    # Pastikan message dari chat yang benar
    if str(chat_id) != str(TELEGRAM_CHAT_ID):
        return
    
    message_text = message_text.strip()
    
    # Command: /start atau /help
    if message_text.startswith('/start') or message_text.startswith('/help'):
        help_text = """
🤖 <b>OpenSea Mint Monitor Bot</b>

<b>📋 Available Commands:</b>

/add &lt;link/username&gt;
   ➜ Tambah akun ke watchlist
   Contoh: 
   • /add https://opensea.io/pudgypenguins
   • /add pudgypenguins
   • /add @pudgypenguins

/remove &lt;username&gt;
   ➜ Hapus akun dari watchlist
   Contoh: /remove pudgypenguins

/list
   ➜ Lihat semua akun di watchlist

/clear
   ➜ Hapus semua watchlist (hati-hati!)

/help
   ➜ Tampilkan pesan ini

<b>💡 Tips:</b>
• Paste link OpenSea langsung dari Twitter!
• Bot otomatis ekstrak username
• Max 50 akun di watchlist

<b>⏱️ Status:</b>
Bot cek setiap {interval} menit
""".format(interval=CHECK_INTERVAL//60)
        send_telegram_message(help_text)
    
    # Command: /add <username/link>
    elif message_text.startswith('/add '):
        input_text = message_text[5:].strip()
        
        if not input_text:
            send_telegram_message("❌ Format salah!\n\nContoh:\n/add https://opensea.io/pudgypenguins\natau\n/add pudgypenguins")
            return
        
        # Ekstrak username
        username = extract_username_from_url(input_text)
        
        # Load current watchlist
        watchlist = load_watchlist()
        
        # Cek apakah sudah ada
        if username in watchlist:
            send_telegram_message(f"⚠️ <b>@{username}</b> sudah ada di watchlist!")
            return
        
        # Cek limit
        if len(watchlist) >= 50:
            send_telegram_message("❌ Watchlist penuh! (max 50 akun)\n\nHapus beberapa akun dulu pakai /remove")
            return
        
        # Tambahkan ke watchlist
        watchlist.append(username)
        save_watchlist(watchlist)
        
        send_telegram_message(f"✅ Berhasil menambahkan <b>@{username}</b> ke watchlist!\n\n📋 Total: {len(watchlist)} akun\n\nLihat semua: /list")
    
    # Command: /remove <username>
    elif message_text.startswith('/remove '):
        username = message_text[8:].strip().lower()
        
        if not username:
            send_telegram_message("❌ Format salah!\n\nContoh: /remove pudgypenguins")
            return
        
        # Load current watchlist
        watchlist = load_watchlist()
        
        if username not in watchlist:
            send_telegram_message(f"⚠️ <b>@{username}</b> tidak ada di watchlist!")
            return
        
        # Hapus dari watchlist
        watchlist.remove(username)
        save_watchlist(watchlist)
        
        send_telegram_message(f"✅ Berhasil menghapus <b>@{username}</b> dari watchlist!\n\n📋 Sisa: {len(watchlist)} akun")
    
    # Command: /list
    elif message_text.startswith('/list'):
        watchlist = load_watchlist()
        
        if not watchlist:
            send_telegram_message("📋 Watchlist kosong!\n\nTambah akun pakai: /add <link>")
            return
        
        # Buat list dengan numbering
        list_text = "📋 <b>Watchlist Kamu:</b>\n\n"
        for i, username in enumerate(watchlist, 1):
            list_text += f"{i}. @{username}\n"
        
        list_text += f"\n<b>Total:</b> {len(watchlist)} akun"
        list_text += f"\n<b>Check Interval:</b> {CHECK_INTERVAL//60} menit"
        
        send_telegram_message(list_text)
    
    # Command: /clear (hapus semua watchlist)
    elif message_text.startswith('/clear'):
        watchlist = load_watchlist()
        count = len(watchlist)
        
        save_watchlist([])
        
        send_telegram_message(f"🗑️ Watchlist dikosongkan!\n\nDihapus: {count} akun")
    
    # Unknown command
    else:
        send_telegram_message("❌ Command tidak dikenal!\n\nKetik /help untuk lihat semua command.")

def telegram_bot_listener():
    """Thread untuk listen command dari Telegram"""
    print("👂 Telegram command listener started...")
    offset = None
    
    while True:
        try:
            updates = get_telegram_updates(offset)
            
            if updates and updates.get("ok"):
                for update in updates.get("result", []):
                    offset = update["update_id"] + 1
                    
                    # Cek apakah ada message
                    if "message" in update:
                        message = update["message"]
                        chat_id = message["chat"]["id"]
                        
                        # Hanya process text message
                        if "text" in message:
                            text = message["text"]
                            print(f"📨 Received command: {text}")
                            
                            # Handle command
                            handle_command(text, chat_id)
            
            time.sleep(1)  # Delay kecil untuk avoid spam request
            
        except Exception as e:
            print(f"❌ Error in bot listener: {e}")
            time.sleep(5)

# ==================== COLLECTION DATA MANAGEMENT ====================

def load_sent_collections():
    """Load daftar collection yang sudah dikirim notifikasi"""
    try:
        with open(SENT_COLLECTIONS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_sent_collections(sent_list):
    """Simpan daftar collection yang sudah dikirim notifikasi"""
    with open(SENT_COLLECTIONS_FILE, 'w') as f:
        json.dump(sent_list, f)

# ==================== OPENSEA MONITORING ====================

def get_opensea_collections(username):
    """Ambil data collections dari akun OpenSea"""
    url = f"https://api.opensea.io/api/v2/collections"
    headers = {
        "Accept": "application/json",
        "X-API-KEY": ""  # OpenSea API key opsional untuk rate limit lebih tinggi
    }
    params = {
        "creator": username,
        "limit": 50
    }
    
    try:
        print(f"🔍 Checking @{username}...")
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("collections", [])
        else:
            print(f"⚠️ Error getting data for @{username}: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def check_for_new_mints():
    """Cek semua akun di watchlist untuk countdown/mint baru"""
    watchlist = load_watchlist()
    
    if not watchlist:
        print("⚠️ Watchlist kosong! Tambah akun pakai command /add")
        return
    
    sent_collections = load_sent_collections()
    new_mints_found = False
    
    print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Starting check...")
    print(f"📋 Monitoring {len(watchlist)} accounts\n")
    
    for username in watchlist:
        collections = get_opensea_collections(username)
        
        for collection in collections:
            try:
                collection_name = collection.get("name", "Unknown")
                collection_slug = collection.get("collection", "")
                
                # Buat unique ID untuk collection
                collection_id = f"{username}_{collection_slug}"
                
                # Skip jika sudah pernah kirim notifikasi untuk collection ini
                if collection_id in sent_collections:
                    continue
                
                # Cek berbagai indikator mint/countdown
                has_mint_info = False
                mint_message = ""
                
                # Cek field yang mungkin ada
                if collection.get("safelist_request_status") == "approved":
                    # Collection baru yang verified
                    opensea_url = f"https://opensea.io/collection/{collection_slug}"
                    
                    mint_message = f"""
🔥 <b>NEW COLLECTION ALERT!</b> 🔥

👤 Creator: @{username}
📦 Collection: {collection_name}
🔗 Link: {opensea_url}

🚨 Collection baru terdeteksi! Cek countdown/mint details di OpenSea.

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                    has_mint_info = True
                
                # Jika ada info mint, kirim notifikasi
                if has_mint_info:
                    print(f"🎯 Found: {collection_name} by @{username}")
                    
                    if send_telegram_message(mint_message):
                        sent_collections.append(collection_id)
                        save_sent_collections(sent_collections)
                        new_mints_found = True
                        
                        # Delay untuk avoid spam
                        time.sleep(2)
                
            except Exception as e:
                print(f"⚠️ Error processing collection: {e}")
                continue
        
        # Delay antar request untuk avoid rate limit
        time.sleep(2)
    
    if not new_mints_found:
        print("✅ No new mints found this round")
    
    print(f"💤 Next check in {CHECK_INTERVAL} seconds...\n")

# ==================== MAIN FUNCTION ====================

def monitor_thread():
    """Thread untuk monitoring OpenSea"""
    print("🔍 OpenSea monitoring started...")
    
    while True:
        try:
            check_for_new_mints()
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"❌ Unexpected error in monitor: {e}")
            print("⏳ Waiting 60 seconds before retry...")
            time.sleep(60)

def main():
    """Fungsi utama - jalankan bot"""
    print("="*60)
    print("🤖 OpenSea Mint Monitor Bot v2.0 Started!")
    print("="*60)
    print(f"📱 Telegram Chat ID: {TELEGRAM_CHAT_ID}")
    print(f"⏱️  Check Interval: {CHECK_INTERVAL} seconds ({CHECK_INTERVAL//60} minutes)")
    print(f"💾 Watchlist file: {WATCHLIST_FILE}")
    print("="*60)
    
    # Load watchlist
    watchlist = load_watchlist()
    print(f"👥 Current watchlist: {len(watchlist)} accounts")
    if watchlist:
        for username in watchlist[:5]:  # Show first 5
            print(f"   • @{username}")
        if len(watchlist) > 5:
            print(f"   ... and {len(watchlist)-5} more")
    print("="*60)
    
    # Kirim pesan test ke Telegram
    test_message = """
🤖 <b>Bot v2.0 Started Successfully!</b>

✅ OpenSea Mint Monitor is now running!
📋 Command support enabled!

<b>Quick Commands:</b>
• /add &lt;link&gt; - Tambah watchlist
• /list - Lihat watchlist
• /help - Semua command

Try: /list untuk lihat watchlist kamu!
"""
    send_telegram_message(test_message)
    
    # Start Telegram command listener di thread terpisah
    listener_thread = threading.Thread(target=telegram_bot_listener, daemon=True)
    listener_thread.start()
    
    # Start monitoring di thread terpisah
    monitor = threading.Thread(target=monitor_thread, daemon=True)
    monitor.start()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user")
        send_telegram_message("🛑 Bot has been stopped")

if __name__ == "__main__":
    main()
