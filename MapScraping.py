import httpx

# Define subscription key as a global constant
SUBSCRIPTION_KEY = 'FFpRBsal7YvWdPvWrGyXUION7ppBY9bvSPc0vt5r0bSrXKognosAJQQJ99BCACYeBjFCYookAAAgAZMP18pE'

def get_search_fuzzy(query):
    """
    Perform a fuzzy search for an address or point of interest based on a query string.
    :param query: Query string for the search.
    :return: JSON response from Azure Maps.
    """
    url = "https://atlas.microsoft.com/search/fuzzy/json"
    params = {
        'subscription-key': SUBSCRIPTION_KEY,  # Use the global constant
        'api-version': '1.0',
        'query': query
    }

    response = httpx.get(url, params=params)
    return response.json()

def main():
    query = input("Enter the location you want to search for: ")

    try:
        response_json = get_search_fuzzy(query)  # Only passing query now

        if 'results' in response_json:
            for item in response_json['results']:
                print('Result Type:', item['type'])
                if 'poi' in item:
                    print('Name:', item['poi']['name'])
                print('Address:', item['address']['freeformAddress'])
                print('Lat Long:', item['position'])
                print('------------------------------------------------')
        else:
            print("No results found or an error occurred.")
            print(response_json)  # Print the response to help debug.

    except httpx.RequestError as e:
        print(f"An error occurred during the request: {e}")
    except KeyError as e:
        print(f"A key error occurred while parsing the response: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()