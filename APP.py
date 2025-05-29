import streamlit as st
import pandas as pd
import datetime
import re

# 🎛️ Futuristic app title and page config
st.set_page_config(page_title="🚀 Quantum Stock Forecaster", page_icon="🧪")

st.markdown("""
# 🧪 Quantum Inventory Predictor 3000  
Welcome to the **future** of stock forecasting. Just feed in your Excel or CSV files, and let the AI-algorithm-wizardry predict when your products vanish into thin air... or at least off your shelves. 🛸📉
""")

st.markdown("## 🧬 Upload Your Intel")

# File uploads
file1 = st.file_uploader("📦 Upload Weekly Sales Report", type=["xlsx", "csv"])
file2 = st.file_uploader("🛰️ Upload Current Stock Snapshot", type=["xlsx", "csv"])

def clean_date_string(date_str):
    return re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

# Initiate analysis button
if file1 and file2 and st.button("🧠 Launch Prediction Protocol"):
    with st.spinner("🤖 Crunching numbers at quantum speed..."):
        try:
            df1 = pd.read_csv(file1) if file1.name.endswith("csv") else pd.read_excel(file1)
            df2 = pd.read_csv(file2) if file2.name.endswith("csv") else pd.read_excel(file2)

            df1.columns = df1.columns.astype(str)
            df2.columns = df2.columns.astype(str)

            date_cols = [col for col in df1.columns if re.match(r"\d{1,2}(st|nd|rd|th)?\s+\w+\s+\d{4}", str(col))]
            if not date_cols:
                st.error("🚫 No valid space-time coordinates (aka dates) found in File 1.")
                st.stop()

            df1_trimmed = df1[[df1.columns[0]] + date_cols].copy()
            df1_trimmed.rename(columns={df1.columns[0]: "🛍️ Product"}, inplace=True)
            df1_trimmed["📊 Total Sold"] = df1_trimmed[date_cols].sum(axis=1)
            df1_trimmed["📈 Avg Weekly Sold"] = df1_trimmed[date_cols].mean(axis=1)

            cleaned_date = clean_date_string(date_cols[-1].strip())
            try:
                last_date = datetime.datetime.strptime(cleaned_date, "%d %b %Y")
            except ValueError:
                st.error(f"🛑 Date parse error in column: '{date_cols[-1]}'. Format must be like '3rd Mar 2025'.")
                st.stop()

            if "Closing Inventory" not in df2.columns:
                st.error("🧯 Missing 'Closing Inventory' data in File 2.")
                st.stop()

            df2_trimmed = df2[[df2.columns[0], "Closing Inventory"]].copy()
            df2_trimmed.rename(columns={df2.columns[0]: "🛍️ Product"}, inplace=True)

            merged_df = pd.merge(df1_trimmed, df2_trimmed, on="🛍️ Product", how="left")
            merged_df["🕒 Weeks Left"] = (merged_df["Closing Inventory"] / merged_df["📈 Avg Weekly Sold"]).round(1)
            merged_df["📅 Run-Out ETA"] = merged_df["🕒 Weeks Left"].apply(
                lambda w: (last_date + datetime.timedelta(weeks=w)) if pd.notna(w) else None
            )
            merged_df["📅 Run-Out ETA"] = merged_df["📅 Run-Out ETA"].apply(
                lambda d: d.strftime("%Y-%m-%d") if pd.notna(d) else "Unknown"
            )
            merged_df["⚠️ Status"] = merged_df["Closing Inventory"].apply(
                lambda x: "🟥 OUT OF STOCK" if x <= 0 else "🟩 OK"
            )

            st.success("✅ Prediction Protocol Complete! Ready to deploy 🚀")

            st.dataframe(
                merged_df[["🛍️ Product", "Closing Inventory", "📈 Avg Weekly Sold", "🕒 Weeks Left", "📅 Run-Out ETA", "⚠️ Status"]],
                use_container_width=True
            )

            st.download_button(
                "📥 Download Forecast CSV",
                data=merged_df.to_csv(index=False),
                file_name="runout_forecast.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"💥 Kaboom! Something went wrong: {str(e)}")
