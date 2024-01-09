import requests
import json
import configparser
from typing import List, Dict

config = configparser.ConfigParser()
config.read('config.ini')
TOKEN = config['SPORTSMONKS']['API_KEY']
BASE_URL = f'https://api.sportmonks.com/v3/'


def gen_url(endpoint: str,
            product: str = 'football/',
            includes: List[str] = None,
            filters: Dict[str, str] = None,
            pagination: str = '') -> str:
    """
    Generate a URL for accessing specific API endpoints.

    :param endpoint: A string representing the API endpoint to access.
    :param product: A string representing the API product to access.
    :param includes: A list of strings representing the resources to be included in the API response.
    :param filters: A list of strings specifying the filters to apply in the server-side.
    :param pagination: String to add for additional page results, if necessary.
    :return: A string representing the complete API url.
    """

    url = BASE_URL + product + f'{endpoint}?api_token={TOKEN}'
    if includes:
        url += f'&include={";".join(includes)}'
    if filters:
        url += f'&include={";".join(includes)}'
    if pagination:
        url += f'&{pagination}'
    return url


def paginated_results(url: str) -> dict:
    """
    Fetches and combines data from all pages of a paginated API endpoint.
    This function sends GET requests to the input URL, and if the response contains
    a link to the next page, it sends another request to fetch the data from
    the next page. This process is repeated until all pages have been fetched.
    The function returns a dictionary that includes data from all pages, as well
    as API subscription details, API rate limit details, and the time zone.

    Parameters:
    url (str): The URL of the API endpoint.

    Returns:
    dict: A dictionary that includes 'data' which is a list of dictionaries each
    representing an entity from the fetched pages. Other keys in the dictionary
    include 'subscription', 'rate_limit' and 'timezone'.
    """
    all_r = []
    pagination = None
    while True:
        if pagination is None:
            r = requests.get(url)
        else:
            r = requests.get(url + '&' + pagination[pagination.find('page='):])
        all_r.append(r.json())
        pagination = r.json()['pagination']['next_page']
        if pagination is None:
            break
    return {
        'data': [typedice for page in all_r for typedice in page['data']],
        'subscription': all_r[-1]['subscription'],
        'rate_limit': all_r[-1]['rate_limit'],
        'timezone': all_r[-1]['timezone'],
    }


def get_player(search=None, includes=None):
    if search is None:
        raise ValueError('Please enter a search condition')
    if type(search) is str:
        # TODO: Need a better search feedback process
        player = requests.get(gen_url(f'players/search/{search}')).json()
        if 'data' not in player.keys():
            raise LookupError('No result found for your search string')
        print(f'Returning first result: {player["data"][0]["name"]}')
        search = player['data'][0]['id']
    return requests.get(gen_url(f'players/{search}', includes=includes))


def update_lookup(file: dict, file_nm: str):
    """
    Writes a lookup dictionary object to a JSON file for future retrieval.

    Parameters:
    file (dict): The dictionary object to be written to the file.
    file_nm (str): The name of the output JSON file (without .json extension).
    """
    with open(f'lookup_files/{file_nm}.json', 'w') as lookup_file:
        json.dump(file, lookup_file)


def read_lookup(file_nm: str) -> dict:
    """
    Reads a stored lookup JSON file and returns its contents as a dictionary.

    This function accepts a filename (without .json extension) as input and reads the
    corresponding JSON file present in the 'lookup_files' directory. The contents
    of the file are returned as a Python dictionary. Object pairs hook converts the keys
    back to integers from the native JSON string format.

    Parameters:
    file (str): The name of the JSON file to be read (without .json extension).

    Returns:
    dict: A dictionary representing the contents of the JSON file.
    """
    with open(f'lookup_files/{file_nm}.json', 'r') as lookup_file:
        return json.load(lookup_file, object_pairs_hook=lambda kv: {int(k): v for k, v in kv})


def update_type_lookup():
    """
    This function is responsible for updating the type lookup dictionary.

    It fetches all types through a paginated request to an API end point and then maps the id and names of each type
    to create a dictionary. This dictionary is then updated as the type lookup dictionary of the program.
    """
    all_types = paginated_results(gen_url('types', product='core/'))
    type_lookup = {lookup['id']: lookup['name'] for lookup in all_types['data']}
    update_lookup(type_lookup, 'types')


try:
    types_lookup = read_lookup('types')
except FileNotFoundError:
    update_type_lookup()
    types_lookup = read_lookup('types')


if __name__ == '__main__':
    print(types_lookup)
