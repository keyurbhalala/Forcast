import streamlit as st
import pandas as pd
import datetime
import re

# Set page config - must be first Streamlit command
st.set_page_config(page_title="🔮 Forecast Wizard", layout="centered", page_icon="📦")

st.markdown(
    """
    <style>
    body, .stApp {
        background-color: #121212;
        color: #eee;
    }
    .css-1d391kg, .css-1v3fvcr, .css-1d391kg * {
        color: #eee !important;
    }
    button, label {
        color: #eee !important;
    }
    .stButton>button {
        background-color: #4caf50;
        color: white;
        font-weight: bold;
    }
    /* Light blue background and black text for file uploader buttons */
    div[data-baseweb="file-uploader"] > div > label {
        background-color: #add8e6 !important;  /* Light blue */
        color: black !important;
        font-weight: 600;
        border-radius: 6px;
        padding: 8px 20px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    div[data-baseweb="file-uploader"] > div > label:hover {
        background-color: #87ceeb !important; /* Slightly darker blue on hover */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Dark mode styling with light text for visibility
st.markdown(
    """
    <style>
    body, .stApp {
        background-color: #121212;
        color: #eee;
    }
    .css-1d391kg, .css-1v3fvcr, .css-1d391kg * {
        color: #eee !important;
    }
    button, label {
        color: #eee !important;
    }
    .stButton>button {
        background-color: #4caf50;
        color: white;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🔮 Welcome to your futuristic Forecast Wizard!")
st.write("Upload your files, and let’s peer into the crystal ball of your stock levels! ✨")

# Instructions
st.markdown("""
Upload two files:

1. **Weekly Sales Report**:  
   - 1st column = Product Name  
   - Weekly sales start from column H onward (dates like `3rd Mar 2025`)  
   - Extra columns after weekly sales data will be ignored  

2. **Current Stock Report**:  
   - Must contain a column titled **Closing Inventory** alongside product names  
   
Let's find out when your stock will wave the white flag!
""")

# File upload
file1 = st.file_uploader("📄 Upload Weekly Sales Report", type=["xlsx", "csv"])
file2 = st.file_uploader("📄 Upload Current Stock Report", type=["xlsx", "csv"])

def clean_date_string(date_str):
    """Remove st, nd, rd, th suffix from dates for parsing."""
    return re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

if file1 and file2 and st.button("🔍 Analyze Run-Out Dates"):

    try:
        # Load weekly sales report
        if file1.name.endswith(".csv"):
            df1 = pd.read_csv(file1)
        else:
            df1 = pd.read_excel(file1)

        # Load current stock report
        if file2.name.endswith(".csv"):
            df2 = pd.read_csv(file2)
        else:
            df2 = pd.read_excel(file2)

        # Normalize column headers to str
        df1.columns = df1.columns.astype(str)
        df2.columns = df2.columns.astype(str)

        # Find date columns in weekly sales (from column H onward)
        # Assumes columns from H (index 7) onward are weekly sales dates
        date_cols = [col for col in df1.columns[7:] if re.match(r"\d{1,2}(st|nd|rd|th)?\s+\w+\s+\d{4}", col)]

        if not date_cols:
            st.error("❌ No valid weekly date columns found in the Weekly Sales Report. Dates must look like '3rd Mar 2025'.")
            st.stop()

        # Extract relevant columns from weekly sales data
        df1_trimmed = df1[[df1.columns[0]] + date_cols].copy()
        df1_trimmed.rename(columns={df1.columns[0]: "Product Name"}, inplace=True)

        # Calculate average weekly sold per product
        df1_trimmed["Avg Weekly Sold"] = df1_trimmed[date_cols].mean(axis=1)

        # Parse last date for runout base
        last_date_str = date_cols[-1]
        cleaned_date = clean_date_string(last_date_str.strip())
        try:
            last_date = datetime.datetime.strptime(cleaned_date, "%d %b %Y")
        except ValueError:
            st.error(f"❌ Could not parse the last date column: '{last_date_str}'. Please use format like '3rd Mar 2025'.")
            st.stop()

        # Check Closing Inventory column
        if "Closing Inventory" not in df2.columns:
            st.error("❌ 'Closing Inventory' column not found in Current Stock Report.")
            st.stop()

        df2_trimmed = df2[[df2.columns[0], "Closing Inventory"]].copy()
        df2_trimmed.rename(columns={df2.columns[0]: "Product Name"}, inplace=True)

        # Merge on Product Name (order can be different)
        merged_df = pd.merge(df1_trimmed, df2_trimmed, on="Product Name", how="left")

        # Calculate weeks remaining (avoid division by zero)
        merged_df["Weeks Remaining"] = merged_df.apply(
            lambda row: row["Closing Inventory"] / row["Avg Weekly Sold"]
            if pd.notna(row["Closing Inventory"]) and pd.notna(row["Avg Weekly Sold"]) and row["Avg Weekly Sold"] > 0 else None,
            axis=1
        )

        # Calculate estimated run-out date
        merged_df["Estimated Run-Out Date"] = merged_df["Weeks Remaining"].apply(
            lambda w: (last_date + datetime.timedelta(weeks=w)) if w is not None else None
        )
        merged_df["Estimated Run-Out Date"] = merged_df["Estimated Run-Out Date"].apply(
            lambda d: d.strftime("%Y-%m-%d") if d else ""
        )

        # Status with humor
        merged_df["Status"] = merged_df["Closing Inventory"].apply(
            lambda x: "❌ Out of Stock - Time to panic!" if pd.notna(x) and x <= 0 else "✅ In Stock - Chill mode ON"
        )

        st.success("✅ Forecast ready! Your stock’s future is revealed ✨")

        # Display results with columns of interest
        st.dataframe(merged_df[[
            "Product Name", "Closing Inventory", "Avg Weekly Sold", "Weeks Remaining", "Estimated Run-Out Date", "Status"
        ]], use_container_width=True)

        # Download button
        csv = merged_df.to_csv(index=False)
        st.download_button("📥 Download Forecast CSV", data=csv, file_name="runout_forecast.csv", mime="text/csv")

    except Exception as e:
        st.error(f"❌ Oops! Something went wrong: {e}")
else:
    st.info("Upload both files and hit that magical button to see the future! 🔮")
