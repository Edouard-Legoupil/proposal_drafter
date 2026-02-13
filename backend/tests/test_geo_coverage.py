import requests

API_BASE_URL = "http://localhost:8502/api" # Adjust if necessary

def test_geographic_coverages():
    try:
        response = requests.get(f"{API_BASE_URL}/geographic-coverages")
        if response.status_code == 200:
            data = response.json()
            print("Full Response:", data)
            coverages = data.get("geographic_coverages")
            print("Geographic Coverages:", coverages)
            if isinstance(coverages, list):
                print("Test Passed: Received a list of geographic coverages.")
            else:
                print("Test Failed: Response is not a list.")
        else:
            print(f"Test Failed: Received status code {response.status_code}")
            print("Response:", response.text)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_geographic_coverages()
