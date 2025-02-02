import pytest
import requests
import requests_mock
from fastProxy.proxy_sources.geonode import GeoNodeSource

SAMPLE_RESPONSE = {
    "data": [
        {
            "ip": "1.2.3.4",
            "port": 8080,
            "protocols": ["http", "https"],
            "country": "United States",
            "anonymityLevel": "elite",
            "upTime": 95.5,
            "lastChecked": "2024-02-17T07:09:35.811692Z"
        },
        {
            "ip": "5.6.7.8",
            "port": 3128,
            "protocols": ["http"],
            "country": "Germany",
            "anonymityLevel": "transparent",
            "upTime": 92.1,
            "lastChecked": "2024-02-17T07:08:30.123456Z"
        }
    ]
}

def test_fetch_success(requests_mock):
    """Test successful proxy fetching from GeoNode API"""
    source = GeoNodeSource()
    requests_mock.get(source.API_URL, json=SAMPLE_RESPONSE)

    proxies = source.fetch()

    assert len(proxies) == 2
    assert proxies[0] == {
        'ip': '1.2.3.4',
        'port': '8080',
        'https': 'yes',
        'country': 'United States',
        'anonymity': 'elite proxy'
    }
    assert proxies[1] == {
        'ip': '5.6.7.8',
        'port': '3128',
        'https': 'no',
        'country': 'Germany',
        'anonymity': 'transparent proxy'
    }

def test_fetch_empty_response(requests_mock):
    """Test handling of empty response from API"""
    source = GeoNodeSource()
    requests_mock.get(source.API_URL, json={"data": []})

    proxies = source.fetch()
    assert len(proxies) == 0

def test_fetch_error_response(requests_mock):
    """Test handling of API error response"""
    source = GeoNodeSource()
    requests_mock.get(source.API_URL, status_code=500)

    proxies = source.fetch()
    assert len(proxies) == 0

def test_fetch_invalid_json(requests_mock):
    """Test handling of invalid JSON response"""
    source = GeoNodeSource()
    requests_mock.get(source.API_URL, text="invalid json")

    proxies = source.fetch()
    assert len(proxies) == 0

def test_fetch_missing_data(requests_mock):
    """Test handling of response missing required fields"""
    source = GeoNodeSource()
    requests_mock.get(source.API_URL, json={"data": [{"ip": "1.2.3.4"}]})

    proxies = source.fetch()
    assert len(proxies) == 0

def test_fetch_connection_error(requests_mock):
    """Test handling of connection error"""
    source = GeoNodeSource()
    requests_mock.get(source.API_URL, exc=requests.exceptions.ConnectionError)

    proxies = source.fetch()
    assert len(proxies) == 0

def test_fetch_different_protocol_formats(requests_mock):
    """Test handling of different protocol formats"""
    source = GeoNodeSource()
    response = {
        "data": [
            {
                "ip": "1.1.1.1",
                "port": 8080,
                "protocols": "http,https",  # String format
                "country": "US",
                "anonymityLevel": "elite"
            },
            {
                "ip": "2.2.2.2",
                "port": 8081,
                "protocols": 123,  # Invalid format
                "country": "UK",
                "anonymityLevel": "anonymous"
            }
        ]
    }
    requests_mock.get(source.API_URL, json=response)

    proxies = source.fetch()
    assert len(proxies) == 2
    assert proxies[0]['https'] == 'yes'
    assert proxies[1]['https'] == 'no'

def test_fetch_different_anonymity_levels(requests_mock):
    """Test handling of different anonymity levels"""
    source = GeoNodeSource()
    response = {
        "data": [
            {
                "ip": "1.1.1.1",
                "port": 8080,
                "protocols": ["http"],
                "country": "US",
                "anonymityLevel": "elite_proxy"  # With underscore
            },
            {
                "ip": "2.2.2.2",
                "port": 8081,
                "protocols": ["http"],
                "country": "UK",
                "anonymityLevel": None  # Missing anonymity
            }
        ]
    }
    requests_mock.get(source.API_URL, json=response)

    proxies = source.fetch()
    assert len(proxies) == 2
    assert proxies[0]['anonymity'] == 'elite proxy'
    assert proxies[1]['anonymity'] == 'unknown proxy'

def test_fetch_malformed_data(requests_mock):
    """Test handling of malformed data"""
    source = GeoNodeSource()
    response = {
        "data": [
            {
                "ip": "",  # Empty IP
                "port": "invalid",  # Invalid port
                "protocols": ["http"],
                "country": "US",
                "anonymityLevel": "elite"
            },
            {
                "ip": None,  # None IP
                "port": None,  # None port
                "protocols": ["http"],
                "country": "UK",
                "anonymityLevel": "anonymous"
            }
        ]
    }
    requests_mock.get(source.API_URL, json=response)

    proxies = source.fetch()
    assert len(proxies) == 0
