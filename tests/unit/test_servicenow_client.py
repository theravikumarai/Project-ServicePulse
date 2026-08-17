from unittest.mock import Mock, patch

from src.ingestion.servicenow_client import ServiceNowClient


def test_get_incident_page():
    client = ServiceNowClient()

    fake_response = Mock()
    fake_response.status_code = 200

    fake_response.json.return_value = {
        "result": [
            {
                "sys_id": "abc123",
                "number": "INC001",
                "short_description": "Test incident",
            },
            {
                "sys_id": "def456",
                "number": "INC002",
                "short_description": "Another incident",
            },
        ]
    }

    with patch(
        "src.ingestion.servicenow_client.requests.get",
        return_value=fake_response,
    ) as mock_get:

        records = client.get_incident_page(
            limit=10,
            offset=0,
        )

    assert len(records) == 2
    assert records[0]["number"] == "INC001"
    assert records[1]["number"] == "INC002"

    mock_get.assert_called_once()


def test_get_all_incidents_pagination():
    client = ServiceNowClient()

    page_1 = [
        {"sys_id": "1", "number": f"INC{i:03d}"}
        for i in range(1, 11)
    ]

    page_2 = [
        {"sys_id": "2", "number": f"INC{i:03d}"}
        for i in range(11, 21)
    ]

    page_3 = [
        {"sys_id": "3", "number": f"INC{i:03d}"}
        for i in range(21, 24)
    ]

    with patch.object(
        client,
        "get_incident_page",
        side_effect=[
            page_1,
            page_2,
            page_3,
        ],
    ) as mock_get_page:

        records = client.get_all_incidents(
            page_size=10
        )

    # 10 + 10 + 3
    assert len(records) == 23

    # Verify all records were collected
    assert records[0]["number"] == "INC001"
    assert records[-1]["number"] == "INC023"

    # Verify pagination calls
    assert mock_get_page.call_count == 3

    mock_get_page.assert_any_call(
        limit=10,
        offset=0,
        query=None,
    )

    mock_get_page.assert_any_call(
        limit=10,
        offset=10,
        query=None,
    )

    mock_get_page.assert_any_call(
        limit=10,
        offset=20,
        query=None,
    )
def test_incremental_incidents_with_overlap():
    client = ServiceNowClient()

    fake_records = [
        {
            "sys_id": "abc123",
            "number": "INC001",
            "sys_updated_on": "2026-04-29 19:56:12",
        },
        {
            "sys_id": "def456",
            "number": "INC002",
            "sys_updated_on": "2026-04-29 20:01:00",
        },
    ]

    with patch.object(
        client,
        "get_incident_page",
        return_value=fake_records,
    ) as mock_get_page:

        records = client.get_incremental_incidents(
            last_updated_on="2026-04-29 19:56:12",
            overlap_minutes=5,
            page_size=10,
        )

    assert len(records) == 2

    mock_get_page.assert_called_once_with(
        limit=10,
        offset=0,
        query=(
            "sys_updated_on>=2026-04-29 19:51:12"
            "^ORDERBYsys_updated_on"
        ),
    )
def test_retry_on_server_error():
    client = ServiceNowClient()

    failed_response = Mock()
    failed_response.status_code = 500

    successful_response = Mock()
    successful_response.status_code = 200
    successful_response.json.return_value = {
        "result": [
            {
                "sys_id": "abc123",
                "number": "INC001",
                "short_description": "Recovered after retry",
            }
        ]
    }

    with patch(
        "src.ingestion.servicenow_client.requests.get",
        side_effect=[
            failed_response,
            failed_response,
            successful_response,
        ],
    ) as mock_get:

        with patch(
            "src.ingestion.servicenow_client.time.sleep"
        ) as mock_sleep:

            records = client.get_incident_page(
                limit=10,
                offset=0,
            )

    assert len(records) == 1
    assert records[0]["number"] == "INC001"

    # 500 → 500 → 200
    assert mock_get.call_count == 3

    # Backoff: 1 second → 2 seconds
    assert mock_sleep.call_count == 2

    mock_sleep.assert_any_call(1)
    mock_sleep.assert_any_call(2)