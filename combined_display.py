import streamlit as st
import pandas as pd
import re
import io

# ---- STREAMLIT CONFIG ----
st.set_page_config(page_title="CSV Merger Tool", page_icon="🧩", layout="centered")
st.title("🧩 CSV Merger for Employee Performance Data")

# ---- HELPER FUNCTIONS ----
def clean_numeric(value):
    if isinstance(value, str):
        value = re.sub(r"\(.*?\)", "", value).strip()
        try:
            return float(value.replace(",", ""))
        except ValueError:
            return None
    return value

def read_csv_safely(file, skip_rows=8):
    try:
        df = pd.read_csv(file, skiprows=skip_rows, encoding='utf-8')
        return df
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        return pd.DataFrame()

# ---- FILE UPLOADS ----
st.sidebar.header("📂 Upload Required CSV Files")

neg_file = st.sidebar.file_uploader("Upload Negative Sales Performance Report", type=["csv"])
pos1_file = st.sidebar.file_uploader("Upload First Positive Sales Dataset", type=["csv"])
pos2_file = st.sidebar.file_uploader("Upload Second Positive Sales Dataset", type=["csv"])
client_add_file = st.sidebar.file_uploader("Upload Client Addition Dataset", type=["csv"])
meeting_file = st.sidebar.file_uploader("Upload Daily Meeting Dataset", type=["csv"])
task_file = st.sidebar.file_uploader("Upload Activation & Specific Task Dataset", type=["csv"])

# ---- PROCESS WHEN ALL FILES UPLOADED ----
if all([neg_file, pos1_file, pos2_file, client_add_file, meeting_file, task_file]):
    st.success("✅ All files uploaded! Click below to process.")

    if st.button("🔄 Merge and Process Data"):
        # Read and clean
        df_neg = read_csv_safely(neg_file)
        df_pos1 = read_csv_safely(pos1_file)
        df_pos2 = read_csv_safely(pos2_file)
        df_client_add = read_csv_safely(client_add_file)
        df_meeting = read_csv_safely(meeting_file)
        df_task = read_csv_safely(task_file)

        # Process negative sales
        if not df_neg.empty:
            df_neg = df_neg[["Owner", "Product or Service", "Actual Closure Date", "Number of Deals", "Sum of Amount ( Actual Value )(In INR)"]]
            df_neg["Number of Deals"] = df_neg["Number of Deals"].apply(clean_numeric)
            df_neg["Sum of Amount ( Actual Value )(In INR)"] = df_neg["Sum of Amount ( Actual Value )(In INR)"].apply(clean_numeric)
            df_neg["Sum of Amount ( Actual Value )(In INR)"] = df_neg["Sum of Amount ( Actual Value )(In INR)"].apply(lambda x: -x if pd.notnull(x) else x)
            df_neg.rename(columns={"Actual Closure Date": "Date"}, inplace=True)

        # Process positive sales 1
        if not df_pos1.empty:
            df_pos1 = df_pos1[["Owner", "Product or Service", "Created At", "Number of Deals", "Sum of Amount ( Actual Value )(In INR)"]]
            df_pos1["Number of Deals"] = df_pos1["Number of Deals"].apply(clean_numeric)
            df_pos1["Sum of Amount ( Actual Value )(In INR)"] = df_pos1["Sum of Amount ( Actual Value )(In INR)"].apply(clean_numeric)
            df_pos1.rename(columns={"Created At": "Date"}, inplace=True)

        # Process positive sales 2
        if not df_pos2.empty:
            df_pos2 = df_pos2[["Owner", "Product or Service", "Pipeline", "Number of Deals", "Sum of Amount ( Actual Value )(In INR)"]]
            df_pos2["Number of Deals"] = df_pos2["Number of Deals"].apply(clean_numeric)
            df_pos2["Sum of Amount ( Actual Value )(In INR)"] = df_pos2["Sum of Amount ( Actual Value )(In INR)"].apply(clean_numeric)
            df_pos2.rename(columns={"Pipeline": "Date"}, inplace=True)

        # Merge all sales
        final_df = pd.concat([df_neg, df_pos1, df_pos2], ignore_index=True)

        # Add extra columns
        extra_columns = ["Number of CLIENT TYPE", "Number of meetings", "Status", "Activation", "Specific Task"]
        for col in extra_columns:
            final_df[col] = None

        # Process client addition
        if not df_client_add.empty:
            df_client_add = df_client_add[["Owner", "Number of Deals", "Number of CLIENT TYPE"]]
            df_client_add["Number of Deals"] = df_client_add["Number of Deals"].apply(clean_numeric)
            df_client_add["Number of CLIENT TYPE"] = df_client_add["Number of CLIENT TYPE"].apply(clean_numeric)
            df_client_add = df_client_add.reindex(columns=final_df.columns, fill_value=None)
            final_df = pd.concat([final_df, df_client_add], ignore_index=True)

        # Process meetings
        if not df_meeting.empty:
            df_meeting = df_meeting[["Created By", "Number of meetings", "Status"]]
            df_meeting.rename(columns={"Created By": "Owner"}, inplace=True)
            df_meeting["Number of meetings"] = df_meeting["Number of meetings"].apply(clean_numeric)
            df_meeting = df_meeting.reindex(columns=final_df.columns, fill_value=None)
            final_df = pd.concat([final_df, df_meeting], ignore_index=True)

        # Process activation & task
        if not df_task.empty:
            df_task.columns = df_task.columns.str.strip().str.lower()
            rename_map = {
                "owner": "Owner",
                "activation": "Activation",
                "specific task": "Specific Task"
            }
            df_task.rename(columns=rename_map, inplace=True)

            required_cols = ["Owner", "Activation", "Specific Task"]
            for col in required_cols:
                if col not in df_task.columns:
                    df_task[col] = None

            df_task = df_task[["Owner", "Activation", "Specific Task"]]
            df_task = df_task.reindex(columns=final_df.columns, fill_value=None)
            final_df = pd.concat([final_df, df_task], ignore_index=True)

        # ---- DOWNLOAD FINAL FILE ----
        st.success("✅ Data merged successfully!")
        st.dataframe(final_df)

        csv_buffer = io.StringIO()
        final_df.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue().encode()

        st.download_button(
            label="📥 Download Merged CSV",
            data=csv_bytes,
            file_name="final_merged_data.csv",
            mime="text/csv"
        )

else:
    st.info("📋 Please upload all six files to continue.")

