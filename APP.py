import streamlit as st
import pandas as pd
import datetime
import re
import base64

# ---------- Add futuristic background ----------
def get_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

bg_image = get_base64("background.jpg")  # <-- Make sure the image is in the same folder

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{bg_image}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #f0f0f0;
        font-family: 'Segoe UI', sans-serif;
    }}
    .css-18ni7ap, .css-1d391kg, .css-1v3fvcr {{
        background-color: rgba(0, 0, 0, 0.6) !important;
    }}
    .stButton>button {{
        color: #fff;
        background-color: #4a00e0;
        border-radius: 12px;
        border: none;
        padding: 0.5em 1.2em;
        font-weight: bold;
        box-shadow: 0 0 15px #4a00e0;
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        box-shadow: 0 0 25px #8e2de2;
        background-color: #8e2de2;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- App Config ----------
st.set_page_config(page_title="🔮 Forecast Wizard", layout="centered")
st.title("🔮 Product Run-Out Forecaster")

st.markdown("""
Upload two files:
1. **Weekly Sales Report**: First column = Product Name. Weekly sales start from column **H** (like `3rd Mar 2025`). Ignore columns after `Items Sold`.
2. **Current Stock Report**: First column = Product Name. Include a column called **"Closing Inventory"**.
""")

# ---------- Upload Files ----------
file1 = st.file_uploader("📄 Upload Weekly Sales Report", type=["xlsx", "csv"])
file2 = st.file_uploader("📄 Upload Current Stock Report", type=["xlsx", "csv"])

# ---------- Clean date headers ----------
def clean_date_string(date_str):
    return re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

# ---------- Main Logic ----------
if file1 and file2 and st.button("🚀 Forecast Now"):
    try:
        # Load data
        df1 = pd.read_csv(file1) if file1.name.endswith("csv") else pd.read_excel(file1)
        df2 = pd.read_csv(file2) if file2.name.endswith("csv") else pd.read_excel(file2)

        df1.columns = df1.columns.astype(str)
        df2.columns = df2.columns.astype(str)

        # Find date columns (starting from H)
        date_cols = [col for col in df1.columns if re.match(r"\d{1,2}(st|nd|rd|th)?\s+\w+\s+\d{4}", str(col))]
        if not date_cols:
            st.error("❌ No valid weekly date columns found in the first file.")
            st.stop()

        df1_trimmed = df1[[df1.columns[0]] + date_cols].copy()
        df1_trimmed.rename(columns={df1.columns[0]: "Product Name"}, inplace=True)

        # Calculate metrics
        df1_trimmed["Total Sold"] = df1_trimmed[date_cols].sum(axis=1)
        df1_trimmed["Avg Weekly Sold"] = df1_trimmed[date_cols].mean(axis=1)

        last_col_header = date_cols[-1]
        cleaned_date = clean_date_string(last_col_header.strip())
        try:
            last_date = datetime.datetime.strptime(cleaned_date, "%d %b %Y")
        except ValueError:
            st.error(f"❌ Could not parse the last date column: '{last_col_header}'. Use format like '3rd Mar 2025'.")
            st.stop()

        # Prepare second file
        if "Closing Inventory" not in df2.columns:
            st.error("❌ 'Closing Inventory' column not found in the second file.")
            st.stop()

        df2_trimmed = df2[[df2.columns[0], "Closing Inventory"]].copy()
        df2_trimmed.rename(columns={df2.columns[0]: "Product Name"}, inplace=True)

        # Merge & forecast
        merged_df = pd.merge(df1_trimmed, df2_trimmed, on="Product Name", how="left")
        merged_df["Weeks Remaining"] = (merged_df["Closing Inventory"] / merged_df["Avg Weekly Sold"]).round(1)

        merged_df["Estimated Run-Out Date"] = merged_df["Weeks Remaining"].apply(
            lambda w: (last_date + datetime.timedelta(weeks=w)) if pd.notna(w) else None
        )
        merged_df["Estimated Run-Out Date"] = merged_df["Estimated Run-Out Date"].apply(
            lambda d: d.strftime("%Y-%m-%d") if pd.notna(d) else ""
        )

        merged_df["Status"] = merged_df["Closing Inventory"].apply(
            lambda x: "❌ Out of Stock" if x <= 0 else "✅ In Stock"
        )

        # Results
        st.success("🎉 Forecast Complete! Here's your crystal ball's prediction:")
        st.dataframe(
            merged_df[["Product Name", "Closing Inventory", "Avg Weekly Sold", "Weeks Remaining", "Estimated Run-Out Date", "Status"]],
            use_container_width=True
        )

        # Download
        csv = merged_df.to_csv(index=False)
        st.download_button("📥 Download as CSV", data=csv, file_name="runout_forecast.csv", mime="text/csv")

    except Exception as e:
        st.error(f"💥 Unexpected Error: {str(e)}")
