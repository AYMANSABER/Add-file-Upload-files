import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

OUTPUT_FILE = "Invoices_Report.xlsx"

# ==============================
# استخراج بيانات الفاتورة
# ==============================

def extract_invoice_data(pdf_file):
    """يستخرج بيانات الفاتورة الأساسية + تفاصيل الأصناف معاً من نفس الـ PDF."""
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

    invoice_id    = re.search(r"Internal ID:\s*(\S+)", text)
    issuance_date = re.search(r"Issuance Date\s*:\s*([0-9/]+)", text)
    customer_name = re.search(r"Recipients? /To\.?Taxpayer Name:\s*(.+)", text, re.DOTALL)
    total_amount  = re.search(r"Total Amount \(EGP\)\s*([0-9.,]+)", text)

    inv_id   = invoice_id.group(1)            if invoice_id    else ""
    inv_date = issuance_date.group(1)         if issuance_date else ""
    cust     = customer_name.group(1).strip() if customer_name else ""
    total    = total_amount.group(1)          if total_amount  else ""

    # ── التقرير الملخص: صف واحد لكل فاتورة ──
    summary_row = {
        "رقم الفاتورة": inv_id,
        "التاريخ":      inv_date,
        "اسم العميل":   cust,
        "الإجمالي EGP": total,
    }

    # ── التقرير التفصيلي: صف لكل صنف ──
    detail_rows = []
    for table in tables:
        for row in table:
            if row and len(row) >= 6:
                detail_rows.append({
                    "رقم الفاتورة":    inv_id,
                    "التاريخ":         inv_date,
                    "اسم العميل":      cust,
                    "الصنف":           row[2],
                    "الكمية":          row[3],
                    "سعر الوحدة":      row[4],
                    "إجمالي الصنف":    row[5],
                    "إجمالي الفاتورة": total,
                })

    return summary_row, detail_rows


# ==============================
# واجهة الموقع
# ==============================

st.set_page_config(page_title="Invoice Extractor Online", layout="centered")

st.title("🌐 نظام استخراج بيانات الفواتير")
st.write("ارفع ملفات PDF ثم اضغط زر استخراج البيانات.")

uploaded_files = st.file_uploader(
    "📤 اختر فواتير PDF",
    type=["pdf"],
    accept_multiple_files=True,
)

if st.button("🚀 استخراج البيانات"):
    if not uploaded_files:
        st.warning("من فضلك ارفع فواتير أولاً.")
    else:
        all_summary = []
        all_details = []
        progress_bar = st.progress(0)

        for i, file in enumerate(uploaded_files):
            try:
                file_bytes = BytesIO(file.read())
                summary_row, detail_rows = extract_invoice_data(file_bytes)
                all_summary.append(summary_row)
                all_details.extend(detail_rows)
            except Exception as e:
                st.warning(f"خطأ في الملف: {file.name} — {e}")
            progress_bar.progress((i + 1) / len(uploaded_files))

        if all_summary:
            df_summary = pd.DataFrame(all_summary)
            df_details = pd.DataFrame(all_details) if all_details else pd.DataFrame()

            # ── كتابة شيتين في نفس ملف Excel ──
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_summary.to_excel(writer, sheet_name="ملخص الفواتير", index=False)
                if not df_details.empty:
                    df_details.to_excel(writer, sheet_name="تفاصيل الأصناف", index=False)
            buffer.seek(0)

            st.success(f"تم استخراج {len(df_summary)} فاتورة بنجاح ✅")

            st.subheader("📋 ملخص الفواتير")
            st.dataframe(df_summary)

            if not df_details.empty:
                st.subheader("📦 تفاصيل الأصناف")
                st.dataframe(df_details)

            st.download_button(
                label="📥 تحميل ملف Excel (شيتين)",
                data=buffer,
                file_name=OUTPUT_FILE,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.warning("لم يتم استخراج بيانات من الملفات المرفوعة.")
