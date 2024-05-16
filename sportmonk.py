import requests
import json
import configparser
from typing import List, Dict, NewType, Optional

config = configparser.ConfigParser()
config.read('config.ini')
TOKEN = config['SPORTSMONKS']['API_KEY']
BASE_URL = f'https://api.sportmonks.com/v3/'
ISODate = NewType('ISODate', str)


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
    return url + '&timezone=America/Chicago'


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


def name_to_id(var: int | str, endpoint: str):
    """
    Convert a name or an id to the corresponding id in the specified endpoint.

    :param var: The name or id to convert. Can be an integer or a string.
    :param endpoint: The endpoint to search for the name or id.
    :return: The corresponding id of the name or id in the specified endpoint.
    :raises ValueError: If the var parameter is not a valid search parameter.
    """
    if isinstance(var, int):
        return var

    if isinstance(var, str):
        search_result = requests.get(gen_url(f'{endpoint}/search/{var}')).json()['data']
        for i, value in enumerate([team for team in search_result]):
            if endpoint == 'teams':
                print(f"{i + 1}. {value['name']: <30} Last Played: {value['last_played_at']}")
            else:
                print(f"{i + 1}. {value['name']}")
        while True:
            try:
                selected = int(input("\nPlease select a number from the list: "))
                if 1 <= selected <= len(search_result):
                    return search_result[selected-1]['id']
                else:
                    print("Invalid selection. Please select a number from the list.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    raise ValueError('Not a valid search parameter')


def get_fixtures(
        fixture_id: Optional[int] = None,
        date: Optional[ISODate] = None,
        team: Optional[str | int] = None,
        date_range_end: Optional[ISODate] = None,
        vs_team: Optional[str | int] = None):
    # TODO: Add Docstring

    include = None  # Default Include for lists of games

    if fixture_id is not None:
        endpoint = f'fixtures/{fixture_id}'
        include = ['lineups', 'events', 'statistics', 'timeline', 'lineups.details']
    elif all(var is None for var in [date, team, date_range_end, vs_team]):
        endpoint = 'fixtures'
    elif all(var is None for var in [team, date_range_end, vs_team]) and date is not None:
        endpoint = f'fixtures/date/{date}'
    elif all(var is None for var in [team, vs_team]) and all([date, date_range_end]):
        endpoint = f'fixtures/between/{date}/{date_range_end}'
    elif vs_team is None and all([date, date_range_end, team]):
        endpoint = f'fixtures/between/{date}/{date_range_end}/{name_to_id(team, "teams")}'
    elif all(var is None for var in [date, date_range_end]) and all([team, vs_team]):
        endpoint = (f'fixtures/head-to-head/'
                    f'{name_to_id(team, "teams")}/'
                    f'{name_to_id(vs_team, "teams")}')
    else:
        raise LookupError('Invalid combination of parameters:')
    fixtures = requests.get(gen_url(endpoint, includes=include)).json()

    return fixtures


def fixture_statistics_lookups(data):
    for stat in data['data']['statistics']:
        stat['type'] = TYPES_LOOKUP[stat['type_id']]
    return data


def fixture_lineup_detail_lookups(data):
    for player in data['data']['lineups']:
        for stat in player['details']:
            stat['type'] = TYPES_LOOKUP[stat['type_id']]
    return data

def fixture_lineup_lookups(data):
    for player in data['data']['lineups']:
        player['lineup_type'] = TYPES_LOOKUP[player['type_id']]
        player['position'] = TYPES_LOOKUP[player['position_id']]
    return data



def get_player(search=None):
    if search is None:
        raise ValueError('Please enter a search condition')
    if type(search) is str:
        # TODO: Need a better search feedback process
        player = requests.get(gen_url(f'players/search/{search}')).json()
        if 'data' not in player.keys():
            raise LookupError('No result found for your search string')
        print(f'Returning first result: {player["data"][0]["name"]}')
        search = player['data'][0]['id']
    return requests.get(gen_url(f'players/{search}'))


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
    TYPES_LOOKUP = read_lookup('types')
except FileNotFoundError:
    update_type_lookup()
    TYPES_LOOKUP = read_lookup('types')


if __name__ == '__main__':
    """
    In Place for testing various endpoints during development. 
    """
    # matchups = get_fixtures(team='fire', vs_team='st. louis')

    one_game = get_fixtures(fixture_id=19051528)
    one_game = fixture_statistics_lookups(one_game)
    one_game = fixture_lineup_detail_lookups(one_game)
    one_game = fixture_lineup_lookups(one_game)

    # games = get_fixtures(date='2024-05-05')
    # shaqiri = get_player('Shaqiri').json()
