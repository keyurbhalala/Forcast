import streamlit as st
import pandas as pd
import datetime
import re
import base64

# 🚀 Set config FIRST before any other Streamlit command
st.set_page_config(page_title="🔮 Forecast Wizard", layout="centered")

# 🔧 Inject background and styles
def add_custom_bg(image_file):
    with open(image_file, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()
    css = f"""
    <style>
        body {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-attachment: fixed;
            color: #f0f0f0;
        }}
        .stApp {{
            background-color: rgba(0, 0, 0, 0.6);
            padding: 2rem;
            border-radius: 15px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #00ffcc;
        }}
        .stButton>button {{
            background-color: #00ffcc;
            color: black;
            font-weight: bold;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# 🖼️ Add your own image name here
add_custom_bg("space_bg.jpg")

# 🚨 Fun & flashy welcome
st.title("🧙‍♂️ Welcome to the Forecast Wizard!")

st.markdown("""
✨ *Behold! The mystical spreadsheet whisperer is here to unveil the sacred run-out prophecies!*  
Upload the following scrolls:

1. 📜 **Weekly Sales Report**: Product names in column A, and weekly sales data starts from column H. Ignore any wizard gibberish after 'Items Sold'.
2. 📜 **Current Stock Report**: Must contain a column titled **"Closing Inventory"**. The order of product names doesn't matter — magic will align them.

Click the big shiny button to conjure your destiny.
""")

file1 = st.file_uploader("🧾 Upload Weekly Sales Report", type=["xlsx", "csv"])
file2 = st.file_uploader("🧾 Upload Current Stock Report", type=["xlsx", "csv"])

def clean_date_string(date_str):
    return re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

if file1 and file2 and st.button("🔮 Reveal Run-Out Prophecies"):
    try:
        df1 = pd.read_csv(file1) if file1.name.endswith("csv") else pd.read_excel(file1)
        df2 = pd.read_csv(file2) if file2.name.endswith("csv") else pd.read_excel(file2)

        df1.columns = df1.columns.astype(str)
        df2.columns = df2.columns.astype(str)

        # Detect date columns like "3rd Mar 2025"
        date_cols = [col for col in df1.columns if re.match(r"\d{1,2}(st|nd|rd|th)?\s+\w+\s+\d{4}", str(col))]
        if not date_cols:
            st.error("🛑 No mystical weekly date columns found. Please check your scroll format.")
            st.stop()

        df1_trimmed = df1[[df1.columns[0]] + date_cols].copy()
        df1_trimmed.rename(columns={df1.columns[0]: "Product Name"}, inplace=True)

        df1_trimmed["Total Sold"] = df1_trimmed[date_cols].sum(axis=1)
        df1_trimmed["Avg Weekly Sold"] = df1_trimmed[date_cols].mean(axis=1)

        cleaned_date = clean_date_string(date_cols[-1].strip())
        try:
            last_date = datetime.datetime.strptime(cleaned_date, "%d %b %Y")
        except ValueError:
            st.error(f"⚠️ Could not read the final date column: '{date_cols[-1]}'. Use format like '3rd Mar 2025'.")
            st.stop()

        if "Closing Inventory" not in df2.columns:
            st.error("🚫 No 'Closing Inventory' column found in the second scroll.")
            st.stop()

        df2_trimmed = df2[[df2.columns[0], "Closing Inventory"]].copy()
        df2_trimmed.rename(columns={df2.columns[0]: "Product Name"}, inplace=True)

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

        st.success("✨ Prophecies Revealed!")

        st.dataframe(
            merged_df[["Product Name", "Closing Inventory", "Avg Weekly Sold", "Weeks Remaining", "Estimated Run-Out Date", "Status"]],
            use_container_width=True
        )

        csv = merged_df.to_csv(index=False)
        st.download_button("📥 Download Your Destiny as CSV", data=csv, file_name="runout_forecast.csv", mime="text/csv")

    except Exception as e:
        st.error(f"💥 An unexpected magical disruption occurred: {str(e)}")
