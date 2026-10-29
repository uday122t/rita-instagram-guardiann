# RITA Instagram Guardian

لوحة عربية أولية لإدارة قواعد المراجعة وسجل المخالفات، مع تجهيز تسجيل الدخول الرسمي عبر Instagram OAuth.

## الحالة الحالية
- لوحة تحكم عربية وسجل مخالفات محلي.
- زر ربط الحساب المحدد @rita_.core عبر صفحة Instagram الرسمية.
- مسار OAuth مع التحقق من state وتخزين رمز الوصول مشفرًا في SQLite.
- لا يمكن تشغيل الربط قبل إنشاء تطبيق Meta وضبط متغيرات البيئة.

## إعداد الربط
1. أنشئ تطبيق Meta يدعم Instagram API with Instagram Login.
2. أضف رابط إعادة التوجيه نفسه الموجود في META_REDIRECT_URI إلى إعدادات OAuth في تطبيق Meta.
3. اضبط المتغيرات التالية في Secrets/Environment Variables لدى الاستضافة:
   - META_APP_ID
   - META_APP_SECRET
   - META_REDIRECT_URI
   - APP_SIGNING_SECRET (قيمة عشوائية طويلة)
   - TOKEN_ENCRYPTION_KEY (مفتاح Fernet صالح)
4. شغّل التطبيق وافتح / ثم اضغط «ربط حساب Instagram».

لا تضع كلمة مرور Instagram أو أي سر في GitHub. أدخل كلمة المرور فقط في صفحة Instagram الرسمية.

## توليد مفاتيح الحماية
يمكن توليد مفتاح Fernet محليًا بالأمر:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
ولإنشاء APP_SIGNING_SECRET استخدم قيمة عشوائية طويلة وفريدة.

## حدود واجهات Instagram
تسجيل الدخول لا يمنح صلاحية إدارة مجموعات Instagram. واجهات Meta الرسمية لا تدعم قراءة مجموعات الدردشة أو حذف رسائل الآخرين أو طرد أعضاء المجموعات. نطاق الرسائل المتاح هنا يخضع لمتطلبات Meta ولا يحوّل الحساب إلى بوت إدارة مجموعات.

## التشغيل
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```
