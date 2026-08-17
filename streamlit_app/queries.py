from config import (
    REDSHIFT_SCHEMA,
    REDSHIFT_TABLE,
)

def get_incidents_query():

    return f"""
        SELECT
            incident_id,
            incident_number,
            short_description,
            state,
            state_label,
            priority,
            priority_label,
            urgency,
            impact,
            category,
            subcategory,
            created_at,
            updated_at,
            incident_age_days
        FROM {REDSHIFT_SCHEMA}.{REDSHIFT_TABLE}
        ORDER BY updated_at DESC
    """