import os

import pandas as pd
import plotly.express as px
import streamlit as st

from labeler import label_comment, LABELS

# ---- Settings ----------------------------------------------------------
TITLE = "Queens Community Poll"
QUESTION = "What are the most pressing issues in Queens?"
CSV_FILE = "feedback.csv"
LOW_POINTS = 10   # a comment labeled with an issue the person gave under 10 points is flagged
# ------------------------------------------------------------------------

st.set_page_config(page_title=TITLE, layout="wide")
st.title(TITLE)
st.caption(QUESTION)

# Load the saved responses, or start with an empty table
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["comment", "label"] + LABELS)

tab_customer, tab_owner = st.tabs(["Resident: share your view", "Owner: analyze the results"])

# ---- Resident tab: split 100 points, leave a comment, get a label, save --------
with tab_customer:
    st.subheader("What bothers you the most?")
    st.write("Tell us what bothers you the most, to help us structure policies for the future. "
             "**Distribute 100 points** across the issues below. More points means more pressing.")
    with st.form("poll_form", clear_on_submit=True):
        points = {}
        cols = st.columns(3)
        for i, issue in enumerate(LABELS):
            points[issue] = cols[i % 3].number_input(issue, min_value=0, max_value=100, value=0, step=5)
        comment = st.text_area("Your comment")
        submitted = st.form_submit_button("Submit")

    if submitted:
        total = sum(points.values())
        if not comment.strip():
            st.error("Please leave a comment.")
        elif total != 100:
            st.error(f"Your points add up to {total}. They must add up to exactly 100.")
        else:
            label = label_comment(comment.strip())
            new_row = pd.DataFrame([{"comment": comment.strip(), "label": label, **points}])
            pd.concat([df, new_row], ignore_index=True).to_csv(CSV_FILE, index=False)
            df = pd.read_csv(CSV_FILE)
            st.success("Thank you for your response!")
            st.caption(f"Behind the scenes, the app labeled your comment: {label}")

# ---- Owner tab: analyze the results -------------------------------------------
with tab_owner:
    if df.empty:
        st.info("No responses yet. Switch to the resident tab and add the first one.")
    else:
        # Read carefully: the label is unclear, or the comment is about an issue the person gave few points
        def needs_review(row):
            return row["label"] == "unclear" or row[row["label"]] < LOW_POINTS

        flag = df.apply(needs_review, axis=1)
        avg_points = df[LABELS].mean().round(1).sort_values(ascending=False)

        st.subheader(QUESTION)
        m1, m2, m3 = st.columns(3)
        m1.metric("Responses", len(df))
        m2.metric("Top issue", avg_points.index[0], f"{avg_points.iloc[0]} avg points")
        m3.metric("Need manual review", int(flag.sum()))

        col1, col2 = st.columns(2)
        with col1:
            st.caption("Average points by issue (out of 100)")
            fig = px.bar(avg_points.reset_index(), x="index", y=0, text=0)
            fig.update_layout(xaxis_title=None, yaxis_title="Average points")
            st.plotly_chart(fig, width="stretch")
        with col2:
            st.caption("What residents wrote about, by issue")
            counts = df["label"].value_counts().rename_axis("label").reset_index(name="count")
            fig = px.bar(counts, x="label", y="count", text="count")
            fig.update_layout(xaxis_title=None, yaxis_title="Comments")
            st.plotly_chart(fig, width="stretch")

        st.subheader("Read these carefully")
        st.caption(f"The label is unclear, or the comment is about an issue the person gave fewer than "
                   f"{LOW_POINTS} points.")
        for _, row in df[flag].iterrows():
            with st.container(border=True):
                st.write(row["comment"])
                st.caption(f"Label: {row['label']} · " + ", ".join(f"{i} {int(row[i])}" for i in LABELS))

        with st.expander("All responses"):
            st.dataframe(df, hide_index=True, width="stretch")
        st.download_button("Download CSV", df.to_csv(index=False), file_name="feedback.csv")
        st.caption("On the free Streamlit Cloud, the saved file can disappear when the app restarts. "
                   "Download your CSV to keep it.")
