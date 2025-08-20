from typing import List, Union
import sportmonk
import csv
import os


def remove_duplicates(file_name: str):
    """
    Removes duplicate lines from a file.

    :param file_name: Name of the file to be processed.
    :return: None
    """
    with open(file_name, "r", encoding='utf-8') as f:
        lines = f.readlines()
    lines_seen = set()
    with open(file_name, "w", encoding='utf-8') as f:
        for line in lines:
            if line not in lines_seen:
                f.write(line)
                lines_seen.add(line)


def write_data(filename: str, data: Union[List[int], List[List]]):
    """
    Writes data to a file specified by the filename parameter.

    :param filename: The name of the file to write the data to.
    :type filename: str
    :param data: The data to be written to the file. It can either be a list of integers or a list of lists.
    :type data: Union[List[int], List[List]]
    :return: None
    """
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if type(data[0]) is list:
            writer.writerows(data)
        else:
            writer.writerow(data)


def dict_lookup(list_of_dicts: list, *args):
    """
    Searches for a dictionary in a list of dictionaries that matches all specified
    criteria given as key-value pairs.

    The function iterates through the provided list of dictionaries and checks
    whether all given key-value conditions are met in each dictionary. If a match
    is found, the dictionary is returned. If no match is found, an empty dictionary
    is returned.

    :param list_of_dicts: A list containing dictionaries to be searched.
    :param args: A variable number of key-value pairs to match against the
        dictionaries in the list.
    :return: The first dictionary that matches all the specified conditions, or an
        empty dictionary if no matching dictionary is found.
    """
    for row in list_of_dicts:
        if all([row[arg[0]]==arg[1] for arg in args]):
            return row
    return {}


def unnest(nested_dict: dict):
    """
    Unnests a dictionary structure by flattening nested dictionaries into the parent
    dictionary-level. The function processes items within a list of dictionaries and
    unwraps any detected nested dictionaries, appending their key-value pairs to
    the immediate parent structure. Ensures no nested dictionary remains directly
    nested after a single iteration.

    :param nested_dict: A list of dictionaries containing potentially nested
        dictionaries as values.
    :type nested_dict: dict
    :return: The modified list of dictionaries with all first-level nested dictionaries
        unnested into their respective parent dictionary.
    :rtype: dict
    """
    # TODO: Add recursiveness and handling for duplicate key names.
    for row in nested_dict:
        temp_dict = {}
        for key in row.keys():
            if type(row[key]) == dict:
                for nested_key in row[key].keys():
                    temp_dict[nested_key] = row[key][nested_key]
        if len(temp_dict) > 0:
            row.update(temp_dict)
    return nested_dict


def fixture_table(data: dict):
    """
    Main function for parsing fixture level data from the API response. Shows game level data including teams,
    scores, and home/away designation.
    :param data: JSON response from the Fixture API endpoint.
    :return: Dictionary of rows of data to be written to a csv file.
    """
    fixture = [data[key] for key in ['id', 'name', 'venue_id', 'starting_at', 'result_info']]

    for datapoint in ['participants', 'scores', 'xgfixture']:
        data[datapoint] = unnest(data[datapoint])

    home_team_id = dict_lookup(data['participants'], ('location', 'home'))['id']
    away_team_id = dict_lookup(data['participants'], ('location', 'away'))['id']

    fixture += [home_team_id, away_team_id]

    dict_lookup(data['scores'], ('description', '2ND_HALF'), ('participant', 'home'))

    performance = [
        [
            data['id'], home_team_id,
            dict_lookup(data['formations'], ('location', 'home'))['formation'] if len(data['formations']) > 0 else None,
            dict_lookup(data['scores'], ('description', '1ST_HALF'), ('participant', 'home')).get('score', {'goals': None})['goals'],
            dict_lookup(data['scores'], ('description', '2ND_HALF'), ('participant', 'home')).get('score', {'goals': None})['goals'],
            dict_lookup(data['xgfixture'], ('location', 'home'))['data']['value'] if len(data['xgfixture']) > 0 else None,
            'home'
        ],
        [
            data['id'], away_team_id,
            dict_lookup(data['formations'], ('location', 'away')).get('formation') if len(data['formations']) > 0 else None,
            dict_lookup(data['scores'], ('description', '1ST_HALF'), ('participant', 'away')).get('score', {'goals': None})['goals'],
            dict_lookup(data['scores'], ('description', '2ND_HALF'), ('participant', 'away')).get('score', {'goals': None})['goals'],
            dict_lookup(data['xgfixture'], ('location', 'away'))['data']['value'] if len(data['xgfixture']) > 0 else None,
            'away'
        ]
    ]
    return {'fixture': fixture, 'performance': performance}


def output_data_table(data, function, output_directory='data', duplicate_remove=False):
    """
    Outputs incoming data in a dictionary (or dictionaries) of lists as rows for a CSV files.
    Optionally removes duplicates from the resulting files.

    :param data: Row data to be written to CSV files. Can be a single dictionary or a list of dictionaries.
    :param function: Function passed through for cleaning and structuring the subset of data.
    :param output_directory: Directory where the resulting CSV files will be saved.
    :param duplicate_remove: Flag indicating whether duplicates should be removed after writing. 
    :return: None
    """
    if data is not None:
        fixture = function(data)
    else:
        fixture = function()
    for table_nm in fixture.keys():
        if len(fixture[table_nm]) > 0:
            write_data(f'{output_directory}/{table_nm}.csv', fixture[table_nm])
            if duplicate_remove:
                remove_duplicates(f'{output_directory}/{table_nm}.csv')


def event_table(data):
    list_of_events = []
    for event in data['events']:
        list_of_events.append([
            event['fixture_id'],
            event['id'],
            dict_lookup(data['periods'], ('id', event['period_id'])).get('sort_order'),
            event['minute'],
            event['extra_minute'],
            event['player_id'],
            event['player_name'],
            event['participant_id'],
            event['related_player_id'],
            event['related_player_name'],
            event['type'],
            event['subtype'],
            event['info'],
            event['injured']
            ])
    return {'events': list_of_events}


def player_performance_table(data):
    rows = [
        [
            deet['player_id'],
            deet['fixture_id'],
            deet['team_id'],
            deet['type'],
            deet['data']['value']
        ]
        for player in data['lineups'] for deet in player['details']
    ]
    return {'player_performance': rows}


def players_table(data):
    players = data['participants'][0]['players'] + data['participants'][1]['players']
    rows = []
    for player in players:
        row = [
            player['id'],
            player['player_id'],
            player['team_id'],
            player['player']['name'],

            sportmonk.COUNTRY_LOOKUP.get(player['player']['nationality_id']),
            sportmonk.TYPES_LOOKUP.get(player['position_id']),
            sportmonk.TYPES_LOOKUP.get(player['detailed_position_id']),
            player['jersey_number'],

            player['player']['height'],
            player['player']['weight'],
            player['player']['date_of_birth'],
            player['player']['image_path']
        ]
        rows.append(row)
    return {'squad_players': rows}


def export_fixture(game, output_directory='sample_data'):
    game = sportmonk.fixture_statistics_lookups(game)
    game = sportmonk.fixture_lineup_detail_lookups(game)
    game = sportmonk.fixture_lineup_lookups(game)

    output_data_table(game, fixture_table, output_directory=output_directory, duplicate_remove=True)
    output_data_table(game, event_table, output_directory=output_directory, duplicate_remove=True)
    output_data_table(game, player_performance_table, output_directory=output_directory, duplicate_remove=True)
    output_data_table(game, players_table, output_directory=output_directory, duplicate_remove=True)

    return game


def test_single_game(fixture_id=19051563):
    game1 = sportmonk.get_fixtures(fixture_id=fixture_id,
                                   include=[
                                            'lineups', 'events', 'statistics',
                                            'timeline',] # 'lineups.details',
                                            # 'participants', 'participants.players.player',
                                            # 'participants.country',
                                            # 'scores', 'periods', 'ballCoordinates', 'xGFixture',
                                            # 'formations']
                                   )['data']

    game1 = export_fixture(game1)

    return game1


def test_game_range(date_start='2023-01-01', date_end='2024-06-01'):
    include = ['lineups', 'events', 'statistics', 'timeline', 'lineups.details',
               'participants', 'participants.players.player',
               'participants.country',
               'scores', 'periods', 'ballCoordinates', 'xGFixture',
               'formations']
    games = sportmonk.get_fixtures(date=date_start, date_range_end=date_end, include=include)
    for fixture in games['data']:
        fixture = export_fixture(fixture)
        yield fixture


if __name__ == '__main__':
    sample = test_single_game(19322669)
