==============================================

Online Invoice Extractor - Manual Upload Version

جاهز للنشر كموقع على الإنترنت

==============================================

import streamlit as st import pdfplumber import pandas as pd import re from io import BytesIO

OUTPUT_FILE = "Invoices_Report.xlsx"

==============================

استخراج بيانات الفاتورة

==============================

def extract_invoice_data(pdf_file): data_rows = []

with pdfplumber.open(pdf_file) as pdf:
    text = ""
    tables = []

    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text

        page_tables = page.extract_tables()
        if page_tables:
            tables.extend(page_tables)

    invoice_id = re.search(r"Internal ID:\\s*(\\S+)", text)
    issuance_date = re.search(r"Issuance Date\\s*:\\s*([0-9/]+)", text)
    customer_name = re.search(r"Recipients \\\To\\\.?Taxpayer Name:\\s(.+)", text, re.DOTALL)
    total_amount = re.search(r"Total Amount \\\EGP\\\\\s*([0-9.]+)", text)

    invoice_id = invoice_id.group(1) if invoice_id else ""
    issuance_date = issuance_date.group(1) if issuance_date else ""
    customer_name = customer_name.group(1).strip() if customer_name else ""
    total_amount = total_amount.group(1) if total_amount else ""

    for table in tables:
        for row in table:
            if row and len(row) >= 6:
                item_name = row[2]
                quantity = row[3]
                unit_price = row[4]
                total_sales = row[5]

                data_rows.append({
                    "Invoice ID": invoice_id,
                    "Issuance Date": issuance_date,
                    "Customer Name": customer_name,
                    "Item Name": item_name,
                    "Quantity": quantity,
                    "Unit Price": unit_price,
                    "Total Sales": total_sales,
                    "Invoice Total": total_amount
                })

return data_rows

==============================

واجهة الموقع

==============================

st.set_page_config(page_title="Invoice Extractor Online", layout="centered")

st.title("🌐 نظام استخراج بيانات الفواتير")

st.write("ارفع ملفات PDF ثم اضغط زر استخراج البيانات.")

uploaded_files = st.file_uploader( "📤 اختر فواتير PDF", type=["pdf"], accept_multiple_files=True )

if st.button("🚀 استخراج البيانات"):

if not uploaded_files:
    st.warning("من فضلك ارفع فواتير أولاً.")

else:
    all_data = []

    progress_bar = st.progress(0)

    for i, file in enumerate(uploaded_files):
        try:
            file_bytes = BytesIO(file.read())
            rows = extract_invoice_data(file_bytes)
            all_data.extend(rows)
        except Exception:
            st.warning(f"خطأ في الملف: {file.name}")

        progress_bar.progress((i + 1) / len(uploaded_files))

    if all_data:
        df = pd.DataFrame(all_data)
        df.to_excel(OUTPUT_FILE, index=False)

        st.success("تم إنشاء ملف Excel بنجاح ✅")

        with open(OUTPUT_FILE, "rb") as f:
            st.download_button(
                label="📥 تحميل ملف Excel",
                data=f,
                file_name=OUTPUT_FILE,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning("لم يتم استخراج بيانات."
