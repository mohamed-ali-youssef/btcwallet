import sys
import os
import time
import qrcode
import requests
import keyboard
import eth_account
from web3 import Web3
from mnemonic import Mnemonic
from datetime import datetime
from bitcoinlib.keys import Address
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from bitcoinlib.wallets import Wallet, wallet_delete_if_exists
from bitcoinlib.wallets import Wallet, wallet_exists
from bitcoinlib.transactions import Transaction
from bitcoinlib.services.services import Service
from colorama import Fore, Back, Style, init
from decimal import Decimal, getcontext


init(autoreset=True)
# ضبط الدقة للحسابات المالية
getcontext().prec = 28

# Function to display QR Code in Terminal
def show_qr(data):
    qr = qrcode.QRCode(version=1, box_size=1, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    qr.print_ascii(invert=True)

def Create_New_Bitcoin_Wallet():
    print(f"\n{Fore.CYAN}{Style.BRIGHT}🚀 CREATE NEW SECURE WALLET")
    wallet_name = input(f"{Fore.WHITE} Enter a unique name for your wallet: ").strip()

    if not wallet_name:
        print(f"{Fore.RED} ❌ Operation Cancelled.")
        return

    # 1. التحقق من وجود المحفظة مسبقاً لمنع التكرار
    if wallet_exists(wallet_name):
        print(f"{Fore.RED} ❌ Error: A wallet with the name '{wallet_name}' already exists!")
        return

    try:
        print(f"{Fore.YELLOW}⚙️ Generating secure keys... Please wait.")
        
        # 2. توليد كلمات الاستعادة (Mnemonic)
        mnemo = Mnemonic("english")
        words = mnemo.generate(strength=128) # 12 كلمة
        
        # 3. إنشاء المحفظة فعلياً
        # ملاحظة: witness_type='segwit' هو المعيار الأحدث والأقل رسوماً
        w = Wallet.create(wallet_name, keys=words, network='bitcoin', witness_type='segwit')
        
        # 4. عرض النتائج بتنسيق احترافي وأنيق
        print(f"\n{Fore.GREEN}{'='*60}")
        print(f"{Fore.GREEN}🎉 WALLET CREATED SUCCESSFULLY!")
        print(f"{Fore.GREEN}{'='*60}")
        
        print(f"{Fore.WHITE}Wallet Name : {Fore.YELLOW}{wallet_name}")
        print(f"{Fore.WHITE}Network     : {Fore.MAGENTA}Bitcoin Mainnet")
        print(f"{Fore.WHITE}Address     : {Fore.CYAN}{w.get_key().address}")
        
        print(f"\n{Fore.RED}{Style.BRIGHT}⚠️  IMPORTANT: SECURITY BACKUP")
        print(f"{Fore.RED}Below is your 12-word recovery phrase. If you lose these words,")
        print(f"{Fore.RED}you lose access to your funds FOREVER. Store them offline!")
        
        # 5. عرض الكلمات داخل إطار مميز لسهولة النسخ
        print(f"\n{Fore.YELLOW}╔{ '═'*88 }╗")
        print(f"║ {Fore.MAGENTA}{words:^86} {Fore.YELLOW}║")
        print(f"╚{ '═'*88 }╝")
        
        print(f"\n{Fore.GREEN}{'='*60}")
        input(f"{Fore.WHITE}Press Enter after you have safely backed up your seed phrase...")

    except Exception as e:
        print(f"{Fore.RED} ❌ Critical Error during creation: {str(e)}")

def Wallet_Details():
    print(f"\n{Fore.CYAN}🔎 {Style.BRIGHT}Wallet Information Lookup")
    wallet_name = input(f"{Fore.WHITE} Wallet name : ").strip()
    
    if not wallet_name:
        print(f"{Fore.RED} ❌ Operation Cancelled.")
        return

    try:
        if wallet_exists(wallet_name):
            # تحميل المحفظة وعمل مزامنة سريعة
            wallet_obj = Wallet(wallet_name)
            print(f"{Fore.YELLOW}🔄 Fetching latest wallet data...{Style.DIM}")
            wallet_obj.scan()
            
            # استخراج البيانات الأساسية يدويًا لتنسيقها
            w_info = wallet_obj.as_dict()
            network = wallet_obj.network.name
            balance = wallet_obj.balance() / 10**8
            
            # تنسيق العرض الاحترافي
            print(f"\n{Fore.GREEN}╔{'═'*73}╗")
            print(f"║ {Style.BRIGHT}{'WALLET PROFILE':^71} ║")
            print(f"╠{'═'*73}╣")
            
            lines = [
                ("Name", wallet_name),
                ("Network", network.upper()),
                ("Witness Type", w_info.get('witness_type', 'N/A')),
                ("Main Address", wallet_obj.get_key().address),
                ("Total Balance", f"{balance:.8f} BTC"),
                ("Key Count", len(wallet_obj.keys())),
            ]

            for label, value in lines:
                print(f"║ {Fore.CYAN}{label:<15}: {Fore.WHITE}{value:<54} ║")
            
            print(f"{Fore.GREEN}╚{'═'*73}╝")
            
            # سؤال المستخدم إذا كان يريد رؤية البيانات التقنية الخام (Raw Data)
            show_raw = input(f"\n{Fore.BLUE}👉 Show raw technical logs? (y/n): ").lower()
            if show_raw == 'y':
                print(f"\n{Fore.MAGENTA}{'-'*20} RAW DATA {'-'*20}")
                wallet_obj.info()
                print(f"{Fore.MAGENTA}{'-'*49}")

        else:
            print(f"{Fore.RED} ❌ Error: Wallet '{wallet_name}' does not exist.")
            
    except Exception as e:
        print(f"{Fore.RED} ❌ Critical Error: {str(e)}")

def print_status_line(label, value, color=Fore.WHITE):
    """دالة مساعدة لطباعة الأسطر بتنسيق موحد"""
    print(f"{Fore.CYAN}{label:<25} {color}{value}")

def Check_Wallet_Status():
    print(f"\n{Fore.YELLOW}🔍 Starting Wallet Status Check...")
    wallet_name = input(f"{Fore.WHITE} Enter Wallet Name: ").strip()

    if not wallet_name:
        print(f"{Fore.RED} ❌ Operation Cancelled.")
        return

    try:
        if not wallet_exists(wallet_name):
            print(f"{Fore.RED} ❌ Error: Wallet '{wallet_name}' not found!")
            return

        # بدء عملية الربط والمزامنة
        wallet_obj = Wallet(wallet_name)
        
        print(f"{Fore.BLUE}🔄 Synchronizing with Blockchain... Please wait.")
        wallet_obj.scan()  # تحديث البيانات من الشبكة
        
        # استخراج البيانات
        main_key = wallet_obj.get_key()
        address = main_key.address
        balance_sat = wallet_obj.balance()
        balance_btc = balance_sat / 10**8
        network = wallet_obj.network.name

        # عرض النتائج بشكل منظم
        print(f"\n{Fore.GREEN}{'='*45}")
        print(f"{Fore.GREEN}{'✨ WALLET REPORT ✨':^45}")
        print(f"{Fore.GREEN}{'='*45}")
        
        print_status_line("Wallet Name:", wallet_name, Fore.YELLOW)
        print_status_line("Network:", network.upper(), Fore.MAGENTA)
        print_status_line("Primary Address:", address, Fore.WHITE)
        
        # تلوين الرصيد (أخضر إذا كان ممتلئاً، أصفر إذا كان فارغاً)
        balance_color = Fore.GREEN if balance_btc > 0 else Fore.YELLOW
        print_status_line("Confirmed Balance:", f"{balance_btc:.8f} BTC", balance_color)
        
        print(f"{Fore.GREEN}{'='*45}")

        # عرض QR Code
        print(f"\n{Fore.CYAN}📱 Scan QR Code to Receive Funds:")
        try:
            show_qr(address)
        except NameError:
            print(f"{Fore.RED}[!] QR function 'show_qr' not defined.")
            
        print(f"{Fore.GREEN}{'='*45}")

    except Exception as e:
        print(f"\n{Fore.RED}⛔ Critical Error: {str(e)}")

def Send_Funds():
    wallet_name = input(" Wallet name : ").strip()
    if wallet_name == "":
        print(" ❌ Cancelled.. ❌")
        return

    if wallet_exists(wallet_name):
        try:
            wallet_obj = Wallet(wallet_name)
            
            # 1. تحديث الرصيد من البلوكشين أولاً
            print(f"🔄 Scanning blockchain for {wallet_name} balance...")
            wallet_obj.scan() 
            
            # جلب الرصيد الحالي بالساتوشي وبالبيتكوين
            current_balance_sat = wallet_obj.balance()
            current_balance_btc = current_balance_sat / 10**8
            
            print(f"💰 Current Balance: {current_balance_btc:.8f} BTC")
            print("\n" + "-"*15 + " Send Bitcoin " + "-"*15)
            
            recipient = input("Recipient Address: ").strip()
            if not recipient:
                print("❌ Invalid Address.")
                return

            amount_btc = float(input("Amount in BTC: "))
            amount_satoshi = int(amount_btc * 10**8)

            # 2. فحص هل الرصيد كافٍ (يجب أن يكون الرصيد أكبر من المبلغ + رسوم تقريبية)
            # نفترض رسوم بسيطة للحماية، والمكتبة ستحسب الرسوم الدقيقة لاحقاً
            if amount_satoshi >= current_balance_sat:
                print(f"❌ Error: Insufficient funds!")
                print(f"You tried to send {amount_btc} BTC, but you only have {current_balance_btc:.8f} BTC (minus fees).")
                return

            confirm = input(f"Confirm sending {amount_btc:.8f} BTC to {recipient}? (y/n): ")
            if confirm.lower() == 'y':
                # تنفيذ عملية الإرسال
                t = wallet_obj.send_to(recipient, amount_satoshi)
                print(f"✅ Transaction Sent Successfully!")
                print(f"🔗 Transaction ID (TXID): {t.txid}")
            else:
                print("❌ Transaction cancelled by user.")

        except ValueError:
            print("❌ Error: Please enter a valid number for the amount.")
        except Exception as e:
            if "No unspent transaction outputs" in str(e):
                print("❌ Error: Your wallet is empty (No UTXOs found).")
            else:
                print(f"❌ Error: {e}")
    else:
        print(f" ❌ Error: Wallet '{wallet_name}' not found!")

def Delete_Wallet():
    print(f"\n{Fore.RED}{Style.BRIGHT}⚠️  DANGER ZONE: DELETE WALLET")
    wallet_name = input(f"{Fore.WHITE} Enter the name of the wallet to wipe: ").strip()

    if not wallet_name:
        print(f"{Fore.YELLOW} ❌ Operation aborted.")
        return False

    # 1. التحقق من وجود المحفظة قبل محاولة الحذف
    if not wallet_exists(wallet_name):
        print(f"{Fore.RED} ❌ Error: Wallet '{wallet_name}' not found.")
        return False

    # 2. تحذير شديد اللهجة وتأكيد مزدوج
    print(f"\n{Fore.RED}{'!'*45}")
    print(f"{Fore.RED}WARNING: This will permanently delete the wallet")
    print(f"{Fore.RED}database from this device. If you haven't backed up")
    print(f"{Fore.RED}your seed phrase, your funds will be GONE FOREVER.")
    print(f"{Fore.RED}{'!'*45}")

    # طلب كتابة اسم المحفظة للتأكيد (مثل GitHub)
    confirm_name = input(f"{Fore.WHITE}\nTo confirm, type the wallet name ({Fore.YELLOW}{wallet_name}{Fore.WHITE}): ").strip()

    if confirm_name == wallet_name:
        final_check = input(f"{Fore.RED}Final check: Are you absolutely sure? (y/n): ").lower()
        
        if final_check == 'y':
            try:
                if wallet_delete_if_exists(wallet_name):
                    print(f"\n{Fore.GREEN}✅ Success: Wallet '{wallet_name}' has been wiped.")
                    return True
                else:
                    print(f"{Fore.RED}❌ Error: Could not delete the wallet file.")
            except Exception as e:
                print(f"{Fore.RED}❌ System Error: {str(e)}")
        else:
            print(f"{Fore.YELLOW}❌ Deletion cancelled at the last second.")
    else:
        print(f"{Fore.RED}❌ Name mismatch. Deletion aborted for safety.")
    
    return False

def Import_Bitcoin_Wallet():
    """
    استيراد محفظة بيتكوين بطريقة احترافية: تشمل التحقق من المدخلات،
    المزامنة مع البلوكشين، وعرض النتائج بتنسيق بصري متقدم.
    """
    print(f"\n{Fore.CYAN}{Style.BRIGHT}🚀 BITCOIN WALLET IMPORT SYSTEM")
    print(f"{Fore.WHITE}{'-'*45}")

    # 1. جمع المدخلات مع تنظيف البيانات
    words = input(f"{Fore.YELLOW}🔑 Enter your mnemonic (12/24 words): ").strip()
    wallet_name = input(f"{Fore.YELLOW}📛 Enter a unique wallet name: ").strip()

    # التحقق من صحة المدخلات قبل بدء العمليات الثقيلة
    if not words or not wallet_name:
        print(f"{Fore.RED}❌ Error: Mnemonic or Wallet Name cannot be empty.")
        return None

    try:
        # 2. إنشاء الكائن والمزامنة
        print(f"\n{Fore.BLUE}⏳ Connecting to Blockchain Network...")
        
        # إنشاء المحفظة (افترضنا استخدام مكتبة bitcoinlib أو ما يشابهها)
        wallet_obj = Wallet.create(wallet_name, keys=words, network='bitcoin')
        
        print(f"{Fore.BLUE}🔄 Synchronizing transactions... This may take a moment.")
        wallet_obj.scan() 

        # 3. معالجة البيانات المالية بدقة احترافية
        main_key = wallet_obj.get_key()
        address = main_key.address
        
        # استخدام Decimal لتجنب مشاكل الكسور العشرية في البرمجة
        balance_sat = wallet_obj.balance()
        balance_btc = Decimal(balance_sat) / Decimal(10**8)
        network_name = wallet_obj.network.name.upper()

        # 4. بناء تقرير العرض (Visual Report)
        border = f"{Fore.GREEN}{'='*50}"
        print(f"\n{border}")
        print(f"{Fore.WHITE}{Style.BRIGHT}{'✨ OFFICIAL WALLET REPORT ✨':^50}")
        print(border)
        
        # عرض البيانات باستخدام تنسيق ثابت الأعمدة
        stats = [
            ("Wallet Name", wallet_name, Fore.YELLOW),
            ("Network", network_name, Fore.MAGENTA),
            ("Address", address, Fore.WHITE),
            ("Balance", f"{balance_btc:.8f} BTC", Fore.GREEN if balance_btc > 0 else Fore.YELLOW)
        ]

        for label, value, color in stats:
            print(f"{Fore.WHITE}{label:<18}: {color}{Style.BRIGHT}{value}")

        print(border)

        # 5. معالجة الـ QR Code كملحق اختياري
        if 'show_qr' in globals() or 'show_qr' in locals():
            print(f"\n{Fore.CYAN}📱 Scan to Receive (Public Address QR):")
            try:
                show_qr(address)
            except Exception as qr_err:
                print(f"{Fore.RED}[!] QR Display Error: {qr_err}")
        
        print(f"{Fore.GREEN}{'='*50}\n")
        return wallet_obj

    except Exception as e:
        # معالجة احترافية للأخطاء: تحديد نوع الخطأ إذا كان اسم المحفظة مكرر مثلاً
        error_msg = str(e)
        if "already exists" in error_msg.lower():
            print(f"{Fore.RED}❌ Error: A wallet with the name '{wallet_name}' already exists.")
        else:
            print(f"{Fore.RED}❌ Critical Failure: {error_msg}")
        return None
    

def GetDataCoin(symbol):
    data = ""
    symbol = symbol.lower()
    
    # الرابط الصحيح يبدأ بـ api.coingecko.com
    base_url = "https://api.coingecko.com/api/v3"
    
    # يفضل إضافة User-Agent لتجنب الحظر
    headers = {
        "accept": "application/json",
        # "x-cg-demo-api-key": "YOUR_API_KEY" # أضف مفتاحك هنا إذا كان لديك واحد
    }

    try:
        # الخطوة 1: البحث عن الـ ID
        search_res = requests.get(f"{base_url}/search?query={symbol}", headers=headers)
        search_data = search_res.json()

        if 'coins' in search_data and len(search_data['coins']) > 0:
            coin_id = ""
            full_name = ""
            for coin in search_data['coins']:
                if coin['symbol'].lower() == symbol:
                    coin_id = coin['id']
                    full_name = coin['name']
                    break
            
            if not coin_id: return ""

            # الخطوة 2: جلب بيانات السوق
            market_params = {
                'vs_currency': 'usd',
                'ids': coin_id,
                'sparkline': 'false',
            }
            response = requests.get(f"{base_url}/coins/markets", params=market_params, headers=headers)
            data_list = response.json()

            if data_list and isinstance(data_list, list):
                coin_data = data_list[0]
                
                def format_full_precision(val):
                    if val is None: return "0.00"
                    return f"{val:.12f}".rstrip('0').rstrip('.')

                price = format_full_precision(coin_data.get('current_price'))
                high_24h = format_full_precision(coin_data.get('high_24h'))
                low_24h = format_full_precision(coin_data.get('low_24h'))
                market_cap = f"{coin_data.get('market_cap', 0):,.0f}"
                volume = f"{coin_data.get('total_volume', 0):,.0f}"
                change = coin_data.get('price_change_percentage_24h') or 0

                # تنسيق الوقت بشكل آمن
                raw_date = coin_data.get('last_updated')
                formatted_date = raw_date.replace('T', ' ').replace('Z', '')[:19] if raw_date else "Unknown"

                data = f"{symbol.upper()}|{full_name}|{price}|{change:+.2f}%|{high_24h}|{low_24h}|{market_cap}|{volume}|{formatted_date}"
    
    except Exception as e:
        print(f"Error: {e}") # للديبيج فقط
        data = ""
        
    return data

def GetCoin():
    user_input = input(f"{Fore.CYAN}Enter Coin Symbol (e.g., BTC, ETH, PEPE): {Style.RESET_ALL}").upper()
    
    raw_data = GetDataCoin(user_input)


    if not raw_data or '|' not in raw_data:
        print(f"{Fore.RED}Error: Could not retrieve data for {user_input}")
        return

    CoinData = raw_data.split('|')
    
    # تحديد لون التغير (أخضر إذا كان موجباً، أحمر إذا كان سالباً)
    change_val = CoinData[3]
    change_color = Fore.GREEN if "-" not in change_val else Fore.RED
    
    # رسم الجدول
    border_color = Fore.YELLOW
    header_color = Fore.CYAN

    print(f"\n{border_color}╔{'═'*79}╗")
    
    # رأس الجدول
    header = f"║ {header_color}{'Symbol':<8} {border_color}│ {header_color}{'Price':<15} {border_color}│ {header_color}{'24h Change':<12} {border_color}│ {header_color}{'24h High':<15} {border_color}│ {header_color}{'24h Low':<15} {border_color}║"
    print(header)
    
    print(f"╠{'═'*79}╣")
    
    # صف البيانات
    row = (f"║ {Style.BRIGHT}{CoinData[0]:<8} {border_color}│ "
           f"{Fore.WHITE}{CoinData[2]:<15} {border_color}│ "
           f"{change_color}{change_val:<12} {border_color}│ "
           f"{Fore.WHITE}${CoinData[4]:<14} {border_color}│ "
           f"{Fore.WHITE}${CoinData[5]:<14} {border_color}║")
    print(row)
    
    print(f"{border_color}╚{'═'*79}╝\n")

def clear_screen():
    # تنظيف الشاشة لمنح تجربة مستخدم أفضل عند كل اختيار
    os.system('cls' if os.name == 'nt' else 'clear')

def get_all_coins():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    current_page = 1  # نبدأ بالصفحة الأولى

    print(Fore.CYAN + Style.BRIGHT + "--- Crypto Multi-Page Tracker (Colorama Edition) ---")
    print(f"Instructions: Press {Fore.YELLOW}[ENTER]{Fore.RESET} for next page, or type {Fore.YELLOW}'0'{Fore.RESET} to exit.")

    try:
        while True:
            # انتظار المستخدم لمعرفة الصفحة التالية
            user_input = input(f"\n{Fore.CYAN}>>> Press Enter for Page {current_page} (or '0' to quit): {Fore.RESET}").strip()
            
            if user_input == '0':
                print(Fore.YELLOW + "Exiting... Goodbye!")
                break

            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 50,
                'page': current_page,
                'sparkline': 'false'
            }

            try:
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    coins_data = response.json()
                    
                    if not coins_data:
                        print(Fore.RED + "No more data available.")
                        break

                    # رأس الجدول بتنسيق احترافي
                    header = f"{'#':<7} | {'Symbol':<15} | {'Price (USD)':<16} | {'24h Change':<17} | {'Name'}"
                    print(Style.BRIGHT + Fore.WHITE + "\n" + header)
                    print(Fore.BLUE + "=" * 110)
                    
                    # حساب بداية الترقيم بناءً على الصفحة
                    start_num = (current_page - 1) * 50 + 1

                    for i, coin in enumerate(coins_data, start=start_num):
                        name = coin['name']
                        symbol = coin['symbol'].upper()
                        price = coin['current_price']
                        change = coin.get('price_change_percentage_24h') or 0
                        # تحديد اللون بناءً على حالة السوق (صعود/هبوط)
                        change_color = Fore.GREEN if change >= 0 else Fore.RED
                        arrow = "▲" if change >= 0 else "▼"
                        # تنسيق الأرقام
                        formatted_price = f"{price:.10f}".rstrip('0').rstrip('.')
                        formatted_change = f"{change:+.2f}%"

                        # طباعة الصف
                        print(f"{Fore.LIGHTBLACK_EX}{i:<7}{Fore.RESET} | "
                              f"{Fore.YELLOW}{symbol:<15}{Fore.RESET} | "
                              f"{Fore.WHITE}${formatted_price:<15}{Fore.RESET} | "
                              f"{change_color}{arrow} {formatted_change:<15}{Fore.RESET} | "
                              f"{name}")
                    
                    print(Fore.BLUE + "=" * 110)
                    print(Fore.CYAN + f"Done loading Page {current_page}. Next will be Page {current_page + 1}.")
                    
                    # الانتقال للصفحة التالية في الضغطة القادمة
                    current_page += 1
                
                elif response.status_code == 429:
                    print(Fore.RED + "\n[Error] Too many requests! Please wait 60 seconds (API Limit).")
                else:
                    print(Fore.RED + f"\n[Error] API status code: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(Fore.RED + f"\n[Network Error] Check your internet connection: {e}")

    except KeyboardInterrupt:
        print(Fore.RED + "\n\nProgram closed by user.")
        sys.exit()


if __name__ == "__main__":
    while True:
        # تعريف الألوان لسهولة الاستخدام
        CYAN = Fore.CYAN
        YELLOW = Fore.YELLOW
        RED = Fore.RED
        GREEN = Fore.GREEN
        MAGENTA = Fore.MAGENTA
        RESET = Fore.RESET
        BC = Style.BRIGHT

        print(f"\n{CYAN}{'═'*45}")
        print(f"{BC}{YELLOW}  🌐 BITCOIN WALLET MANAGER PRO v1.0")
        print(f"{BC}{MAGENTA}        Eng. Mohamed Ali Youssef")
        print(f"{CYAN}{'═'*45}")
        
        menu_options = [
            ("1", "Create Bitcoin Wallet", "➕"),
            ("2", "Import Bitcoin Wallet", "📥"),
            ("3", "Check Wallet Bitcoin", "🔍"),
            ("4", "Wallet Bitcoin Details", "📋"),
            ("5", " Delete Bitcoin Wallet", "🗑️"),
            ("6", "Send Funds Bitcoin Wallet", "💸"),
            ("7", "Get Coin Data", "📉"),
            ("8", "Get All Coins Data", "📊"),

            ("0", "Exit", "🚪")
        ]

        for num, text, icon in menu_options:
            print(f" {CYAN}[{num}]{RESET} {icon} {text:<30}")

        print(f"{CYAN}{'━'*45}")
        
        command = input(f"{BC}{YELLOW} 👉 Choose from the list : {RESET}").strip()

        # مسح الشاشة قبل تنفيذ الأمر لجعل النتائج واضحة
        if command != "0": clear_screen()

        match command:
            case "1": Create_New_Bitcoin_Wallet()
            case "2": Import_Bitcoin_Wallet()
            case "3": Check_Wallet_Status()
            case "4": Wallet_Details()
            case "5": Delete_Wallet()
            case "6": Send_Funds()
            case "7": GetCoin()
            case "8": get_all_coins()
            case "0":
                print(f"{GREEN}👋 Goodbye! Secure your keys.")
                break
            case _:
                print(f"\n {RED}❌ Error: '{command}' is not a valid command!{RESET}\n")
