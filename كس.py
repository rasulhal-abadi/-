import time
import telebot
from telebot import types
import sqlite3
import firebase_admin
from firebase_admin import credentials, db
from firebase_admin import credentials, db, initialize_app
import os

cred = credentials.Certificate("C:\\Users\\3bse\\Desktop\\data\\ghost2-74002-firebase-adminsdk-6ys3k-7b78aed97e.json")
firebase_admin.initialize_app(cred, {'databaseURL': 'https://ghost2-74002-default-rtdb.firebaseio.com/'})
import sqlite3

# اتصال بقاعدة البيانات SQLite
conn = sqlite3.connect('users.sqlite')
cursor = conn.cursor()

# إنشاء جدول لتخزين المعلومات
cursor.execute('''
    CREATE TABLE IF NOT EXISTS fa (
        user_id TEXT PRIMARY KEY,
        p_father TEXT,
        p_grand TEXT,
        ss_lg_no TEXT,
        database_name TEXT


    )
''')

conn = sqlite3.connect('users1.sqlite')
cursor = conn.cursor()

# إنشاء جدول لتخزين المعلومات
cursor.execute('''
    CREATE TABLE IF NOT EXISTS ma (
        user_id TEXT PRIMARY KEY,
        p_father TEXT,
        p_grand TEXT,
        ss_lg_no TEXT,
        database_name TEXT


    )
''')
# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

database_connections = {
    "اربيل": "erbil.sqlite",
    "الانبار": "anbar.sqlite",
    "بابل": "babl.sqlite",
    "بلد": "balad.sqlite",
    "البصرة": "basra.sqlite",
    "بغداد": "bg.sqlite",
    "دهوك" : "duhok.sqlite",
    "الديوانية-القادسية": "qadisiya.sqlite",
    "كربلاء":"krbl.sqlite",
    "ديالى":"deala.sqlite",
    "ذي قار":"zy.sqlite",
    "السليمانية":"sulaymaniyah.sqlite",
    "صلاح الدين":"salah-aldeen.sqlite",
    "كركوك":"kirkuk.sqlite",
    "المثنى":"muthana.sqlite",
    "ميسان":"mesan.sqlite",
    "النجف":"najaf.sqlite",
    "نينوى":"nineveh.sqlite",
    "واسط":"wasit.sqlite",
}

TOKEN = '6573377226:AAEB7Qd7C_5uWQpIJj_hxc4xV_1Ki9QC1_E'
bot = telebot.TeleBot(TOKEN)
user_full_names = {}
user_selected_regions = {}
batch_size = 40
delay_between_batches = 10  
selected_database_name = ""  # إضافة هذا المتغير لتخزين اسم قاعدة البيانات المحددة
def connect_to_database(db_name):
    return sqlite3.connect(db_name)
def create_region_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    buttons = [types.KeyboardButton(text=region) for region in database_connections.keys()]
    keyboard.add(*buttons)
    return keyboard
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, "مرحبًا! قم بإرسال الاسم الثلاثي للبحث عنه.")
    bot.register_next_step_handler(message, get_user_full_name)
    user_data = {"user_id": user_id, "user_name": message.from_user.first_name, "username": message.from_user.username}
    add_user_to_firebase(user_data)
def add_user_to_firebase(user_data):
    try:
        ref = db.reference('/users')
        ref.child(str(user_data["user_id"])).set(user_data)
    except Exception as e:
        print(f"Error adding user to Firebase: {e}")
def get_user_full_name(message):
    user_full_name = message.text
    user_full_names[message.from_user.id] = user_full_name
    name_parts = user_full_name.split()
    if len(name_parts) != 3:
        bot.send_message(message.chat.id, "الرجاء إدخال اسم ثلاثي فقط اضغط /start من جديد.")
        return
    bot.send_message(message.chat.id, f" الآن، اختر المحافظة للبحث عن الاسم {user_full_name}! :", reply_markup=create_region_keyboard())
@bot.message_handler(func=lambda message: message.text in database_connections.keys())
def handle_selected_region(message):
    user_id = message.from_user.id
    user_full_name = user_full_names.get(user_id, "الصديق")
    selected_region = message.text
    bot.send_message(message.chat.id, f"تم اختيار محافطة {selected_region}! الاسم الذي تود البحث عنه، {user_full_name}.")
    global selected_database_name
    selected_database_name = database_connections.get(selected_region, "")
    name_parts = user_full_names[user_id].split()
    db_name = database_connections.get(selected_region, "")
    connection = connect_to_database(db_name)
    try:
        cursor = connection.cursor()
        table_name = "person"
        columns = ["p_first", "p_father", "p_grand", "fam_no", "seq_no", "p_birth", "ss_lg_no"]
        query = f"SELECT {', '.join(columns)} FROM {table_name} WHERE p_first LIKE ? AND p_father LIKE ? AND p_grand LIKE ?"
        cursor.execute(query, (f"%{name_parts[0]}%", f"%{name_parts[1]}%", f"%{name_parts[2]}%"))
        results = cursor.fetchall()
        result_batches = [results[i:i + batch_size] for i in range(0, len(results), batch_size)]
        for batch in result_batches:
            for result in batch:
                full_name = " ".join(result[0:3]).strip()
                birth_date = str(result[5])[:4].lstrip("0")
                seq_no = str(result[4]).lstrip("0")
                inline_keyboard = types.InlineKeyboardMarkup()
                show_family_button = types.InlineKeyboardButton("جلب العائلة", callback_data=f"show_family_{result[3]}")
                inline_keyboard.add(show_family_button)
                message_text = f"{full_name}\nالرقم العائلي: {result[3]}\nتسلسل الفرد: {seq_no}\nتاريخ الميلاد: {birth_date}\n\n"
                bot.send_message(message.chat.id, message_text, reply_markup=inline_keyboard)
                time.sleep(delay_between_batches)
    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(message.chat.id, f"Error: {e}")
    finally:
        connection.close()
@bot.callback_query_handler(func=lambda call: call.data.startswith('show_family_'))
def handle_show_family_callback(call):
    fam_no = call.data.split('_')[2]
    user_id = call.from_user.id
    selected_region = user_selected_regions.get(user_id, "")
    db_name = database_connections.get(selected_region, "")
    connection = connect_to_database(selected_database_name)

    try:
        cursor = connection.cursor()
        table_name = "person"
        family_columns = ["p_first", "p_father", "p_grand", "fam_no", "seq_no", "p_birth", "ss_lg_no"]
        family_query = f"SELECT {', '.join(family_columns)} FROM {table_name} WHERE fam_no = ?"
        cursor.execute(family_query, (fam_no,))
        family_results = cursor.fetchall()
        sorted_family_results = sorted(family_results, key=lambda x: x[4])
        family_results_text = ""
        for family_result in sorted_family_results:
            family_full_name = " ".join(family_result[0:3]).strip()
            family_birth_date = str(family_result[5])[:4].lstrip("0")
            family_seq_no = str(family_result[4]).lstrip("0")
            birth_year = int(family_birth_date)
            current_year = 2023
            age = current_year - birth_year
            family_results_text += f"الاسم الثلاثي: {family_full_name}\n"
            family_results_text += f"الرقم العائلي: {family_result[3]}\n"
            family_results_text += f"التسلسل: {family_seq_no}\n"
            family_results_text += f"تاريخ الميلاد: {family_birth_date}\n"
            family_results_text += f"العمر: {age} سنة\n"
          #  family_results_text += f"الزقاق: {family_result[6]}\n\n"
            # تخزين معلومات المستخدم ذو التسلسل 1
         #   user_doc_ref = db.collection('users').document(family_seq_no)
           

            if family_seq_no == "1":
                user_info = {
                    "database_name": selected_database_name,
                    "user_id": user_id,
                    "p_father": family_result[1],
                    "p_grand": family_result[2],
                    "ss_lg_no": family_result[6]
                }
                add_user_to_sqlite(user_info)
                

                
                

            # تخزين معلومات المستخدم ذو التسلسل 2
            if family_seq_no == "2":
                user_info1 = {
                    "database_name": selected_database_name,
                    "user_id": user_id,
                    "p_father": family_result[1],
                    "p_grand": family_result[2],
                    "ss_lg_no": family_result[6]
                }
                add_user_to_sqlite1(user_info1)

        
       
        #user_doc_ref.set(user_info,user_info2)    
        
        bot.send_message(call.message.chat.id, family_results_text,"قم باراسل الامر /get لاضهار الاقارب")
        
        
      
    except Exception as e:
        print(f"Error: {e}")
    finally:
        connection.close()
def add_user_to_sqlite(user_info):
    try:
        user_id = user_info.get("user_id")
        conn = sqlite3.connect('users.sqlite')
        cursor = conn.cursor()

        # التحقق مما إذا كان المستخدم موجودًا
        cursor.execute('SELECT * FROM fa WHERE user_id = ?', (user_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            # إذا وجد المستخدم، قم بحذفه
            cursor.execute('DELETE FROM fa WHERE user_id = ?', (user_id,))
            print(f"تم حذف معلومات المستخدم ذو user_id: {user_id}")
        else:
            print(f"المستخدم ذو user_id: {user_id} غير موجود")

        # إدراج المعلومات في جدول المستخدمين
        cursor.execute('''
            INSERT INTO fa (user_id, p_father, p_grand, ss_lg_no, database_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_info["user_id"], user_info["p_father"], user_info["p_grand"], user_info["ss_lg_no"], user_info["database_name"]))

        # حفظ التغييرات وإغلاق الاتصال
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error adding user to SQLite: {e}")
def add_user_to_sqlite1(user_info1):
    try:
        user_id = user_info1.get("user_id")
        conn = sqlite3.connect('users1.sqlite')
        cursor = conn.cursor()

        # التحقق مما إذا كان المستخدم موجودًا
        cursor.execute('SELECT * FROM ma WHERE user_id = ?', (user_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            # إذا وجد المستخدم، قم بحذفه
            cursor.execute('DELETE FROM ma WHERE user_id = ?', (user_id,))
            print(f"تم حذف معلومات المستخدم ذو user_id: {user_id}")
        else:
            print(f"المستخدم ذو user_id: {user_id} غير موجود")

        # إدراج المعلومات في جدول المستخدمين
        cursor.execute('''
            INSERT INTO ma (user_id, p_father, p_grand, ss_lg_no, database_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_info1["user_id"], user_info1["p_father"], user_info1["p_grand"], user_info1["ss_lg_no"], user_info1["database_name"]))

        # حفظ التغييرات وإغلاق الاتصال
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error adding user to SQLite: {e}")

@bot.message_handler(commands=['get'])
def handle_get_command(message):
    user_id = message.from_user.id

    # إنشاء لوحة المفاتيح
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    
    # إضافة زر "get fa" للربط بـ users.sqlite
    fa_button = types.KeyboardButton("البحث عن العمام")
    keyboard.add(fa_button)

    # إضافة زر "get ma" للربط بـ users1.sqlite
    ma_button = types.KeyboardButton("البحث عن الخوال")
    keyboard.add(ma_button)

    # إرسال رسالة مع لوحة المفاتيح
    bot.send_message(user_id,"قم باختيار طريقة البحث", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text in ['البحث عن العمام', 'البحث عن الخوال'])
def handle_get_data_command(message):
    user_id = message.from_user.id

    # تحديد قاعدة البيانات والجدول بناءً على اختيار المستخدم
    selected_database = "users.sqlite" if message.text == 'البحث عن العمام' else "users1.sqlite"
    selected_table = "fa" if message.text == 'البحث عن العمام' else "ma"

    # استعلام SQL لجلب معلومات المستخدم من الجدول المحدد باستخدام user_id
    query = f"SELECT database_name, user_id, p_father, p_grand, ss_lg_no FROM {selected_table} WHERE user_id = ?"

    try:
        # اتصال بقاعدة البيانات
        connection = sqlite3.connect(selected_database)
        cursor = connection.cursor()

        # تنفيذ الاستعلام باستخدام user_id الخاص بالمستخدم
        cursor.execute(query, (user_id,))

        # الحصول على البيانات
        result = cursor.fetchone()

        if result:
            # إرسال البيانات إلى المستخدم إذا تم العثور على نتيجة
            result_text = f"Database Name: {result[0]}\nUser ID: {result[1]}\nP Father: {result[2]}\nP Grand: {result[3]}\nSS Lg No: {result[4]}\n\n"
            print(result_text)

           # الآن، نقوم بالبحث مرة أخرى باستخدام database_name والجدول person
        search_in_database_name = result[0]
        search_table_name = "person"
        print(search_in_database_name)


            # استعلام SQL لجلب معلومات المستخدم من الجدول person باستخدام p_father و p_grand و ss_lg_no
        search_query = f"SELECT p_first, p_father, p_grand, fam_no, seq_no, p_birth, ss_lg_no FROM {search_table_name} WHERE p_father = ? AND p_grand = ? AND ss_lg_no = ?"
        connection = sqlite3.connect(search_in_database_name)
        cursor = connection.cursor()

        print(connection)
            # تنفيذ الاستعلام باستخدام القيم المسترجعة من البحث السابق
        cursor.execute(search_query, (result[2], result[3], result[4]))
        # الحصول على البيانات
        family_results = cursor.fetchall()
        sorted_family_results = sorted(family_results, key=lambda x: x[4])
        family_results_text = ""

        for family_result in sorted_family_results:
         family_full_name = " ".join(family_result[0:3]).strip()
         family_birth_date = str(family_result[5])[:4].lstrip("0")
         family_seq_no = str(family_result[4]).lstrip("0")
         birth_year = int(family_birth_date)
         current_year = 2023
         age = current_year - birth_year

         family_results_text += f"الاسم الثلاثي: {family_result[0]} {family_result[1]} {family_result[2]}\n"
         family_results_text += f"الرقم العائلي: {family_result[3]}\n"
         family_results_text += f"التسلسل: {family_seq_no}\n"
         family_results_text += f"تاريخ الميلاد: {family_birth_date}\n"
         family_results_text += f"العمر: {age} سنة\n"
         #family_results_text += f"الزقاق: {family_result[6]}\n\n"

        bot.send_message(user_id, family_results_text)


      
        #else:
        # bot.send_message(user_id, "لم يتم العثور على معلومات لهذا المستخدم.")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # إغلاق اتصال قاعدة البيانات
        connection.close()

if __name__ == "__main__":
    bot.polling(none_stop=True)
