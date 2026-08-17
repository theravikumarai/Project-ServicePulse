import streamlit as st

from database import RedshiftClient
from queries import get_incidents_query


st.set_page_config(
    page_title="ServicePulse",
    page_icon="📊",
    layout="wide",
)

st.title("ServicePulse")
st.subheader("Incident Analytics Dashboard")


@st.cache_data(ttl=300)
def load_incidents():

    client = RedshiftClient()

    return client.execute_query(
        get_incidents_query()
    )


try:

    df = load_incidents()

    st.success(
        f"Successfully loaded {len(df)} incidents."
    )

    st.dataframe(
        df,
        use_container_width=True,
    )

except Exception as exc:

    st.error(
        f"Unable to load Redshift data: {exc}"
    )