import streamlit as st
import pandas as pd
import datetime
import re

st.set_page_config(page_title="Stock Run-Out Forecaster")
st.title("📦 Product Run-Out Forecaster")

st.markdown("""
Upload two files:
1. **Weekly Sales Report**: First column = Product Name, weekly sales start from column H with dates like `3rd Mar 2025`. Extra columns (like `Items Sold`) after weekly data will be ignored.
2. **Current Stock Report**: Contains product name and a column titled **"Closing Inventory"**.
""")

# File upload
file1 = st.file_uploader("📄 Upload Weekly Sales Report", type=["xlsx", "csv"])
file2 = st.file_uploader("📄 Upload Current Stock Report", type=["xlsx", "csv"])

# Date cleaner
def clean_date_string(date_str):
    return re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

# On button click
if file1 and file2 and st.button("🔍 Analyze Run-Out Dates"):
    try:
        # Load files
        if file1.name.endswith("csv"):
            df1 = pd.read_csv(file1)
        else:
            df1 = pd.read_excel(file1)

        if file2.name.endswith("csv"):
            df2 = pd.read_csv(file2)
        else:
            df2 = pd.read_excel(file2)

        # Normalize columns
        df1.columns = df1.columns.astype(str)
        df2.columns = df2.columns.astype(str)

        # Identify valid date columns (like '3rd Mar 2025')
        date_cols = [col for col in df1.columns if re.match(r"\d{1,2}(st|nd|rd|th)?\s+\w+\s+\d{4}", str(col))]
        if not date_cols:
            st.error("❌ No valid weekly date columns found in the first file.")
            st.stop()

        # Extract product names and sales data
        df1_trimmed = df1[[df1.columns[0]] + date_cols].copy()
        df1_trimmed.rename(columns={df1.columns[0]: "Product Name"}, inplace=True)

        # Compute total weekly sold across date columns
        df1_trimmed["Total Sold"] = df1_trimmed[date_cols].sum(axis=1)
        df1_trimmed["Avg Weekly Sold"] = df1_trimmed[date_cols].mean(axis=1)

        # Clean and parse last date column header
        last_col_header = date_cols[-1]
        cleaned_date = clean_date_string(last_col_header.strip())
        try:
            last_date = datetime.datetime.strptime(cleaned_date, "%d %b %Y")
        except ValueError:
            st.error(f"❌ Could not parse the last date column: '{last_col_header}'. Please use format like '3rd Mar 2025'.")
            st.stop()

        # Prepare second file
        if "Closing Inventory" not in df2.columns:
            st.error("❌ 'Closing Inventory' column not found in the second file.")
            st.stop()

        df2_trimmed = df2[[df2.columns[0], "Closing Inventory"]].copy()
        df2_trimmed.rename(columns={df2.columns[0]: "Product Name"}, inplace=True)

        # Merge both files on Product Name
        merged_df = pd.merge(df1_trimmed, df2_trimmed, on="Product Name", how="left")

        # Calculate weeks remaining
        merged_df["Weeks Remaining"] = (merged_df["Closing Inventory"] / merged_df["Avg Weekly Sold"]).round(1)

        # Calculate estimated run-out date
        merged_df["Estimated Run-Out Date"] = merged_df["Weeks Remaining"].apply(
            lambda w: (last_date + datetime.timedelta(weeks=w)) if pd.notna(w) else None
        )
        merged_df["Estimated Run-Out Date"] = merged_df["Estimated Run-Out Date"].apply(
            lambda d: d.strftime("%Y-%m-%d") if pd.notna(d) else ""
        )

        # Highlight out-of-stock
        merged_df["Status"] = merged_df["Closing Inventory"].apply(
            lambda x: "❌ Out of Stock" if x <= 0 else "✅ In Stock"
        )

        st.success("✅ Run-Out Forecast Completed!")

        # Display results
        st.dataframe(merged_df[["Product Name", "Closing Inventory", "Avg Weekly Sold", "Weeks Remaining", "Estimated Run-Out Date", "Status"]], use_container_width=True)

        # Download option
        csv = merged_df.to_csv(index=False)
        st.download_button("📥 Download Result as CSV", data=csv, file_name="runout_forecast.csv", mime="text/csv")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
