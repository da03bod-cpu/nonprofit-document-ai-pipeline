SYSTEM_PROMPT = """أنت نموذج متخصص في استخراج البرامج والمشاريع والمبادرات والأنشطة من التقارير السنوية للجمعيات غير الربحية.
ااقرأ نص التقرير كما هو، حتى لو احتوى على أخطاء في التنسيق أو النص..
استخرج البرامج والمشاريع والأنشطة المذكورة فعليًا فقط.
أعد JSON فقط وفق المخطط المطلوب، ولا تضف شرحًا خارج JSON.
صحح أخطاء OCR الواضحة فقط عندما يكون التصحيح مؤكدًا من السياق، ولا تخترع معلومات غير موجودة.
إذا كانت قيمة غير موجودة بوضوح في التقرير، استخدم null.
"""

SCHEMA = """{
  "programs": [
    {
      "type": "program",
      "name": "string",
      "year": "number|null",
      "description": "string|null",
      "beneficiaries_count": "number|null",
      "budget": "number|string|null",
      "beneficiary_value": "string|null",
      "target_audience": "string|null",
      "delivery_method": "string|null",
      "notes": "string|null"
    }
  ]
}"""

def build_messages(document_text):
    user_prompt = f"""استخرج البرامج والمشاريع والمبادرات والأنشطة من النص التالي.

يجب أن يكون الإخراج JSON فقط بهذا الشكل:
{SCHEMA}

قواعد مهمة:
- لا تضف أي مفتاح خارج المخطط.
- لا تخترع أي برنامج أو رقم أو ميزانية.
- إذا لم توجد معلومة استخدم null.
- احتفظ بالأسماء والمعلومات كما وردت في التقرير مع تصحيح أخطاء OCR الواضحة فقط.
- كل عنصر مستخرج يمثل برنامجًا أو مشروعًا أو مبادرة أو نشاطًا فعليًا مذكورًا في التقرير.

النص:
{document_text}
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
