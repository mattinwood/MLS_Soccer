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
    for row in list_of_dicts:
        if all([row[arg[0]]==arg[1] for arg in args]):
            return row
    return {}


def unnest(nested_dict):
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

def fixture_table(data):
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


def players_table():
    players = sportmonk.all_players()
    rows = [
        [data['id'], data['name'],
         data['nationality']['name'] if type(data['nationality']) is dict else None,
         data['position']['name'] if type(data['position']) is dict else None,
         data['detailedposition']['name'] if type(data['detailedposition']) is dict else None,
         data['height'], data['weight'],
         data['date_of_birth'], data['image_path']] for data in players['data']]
    return {'players': rows}


def test_single_game(fixture_id=19051563):
    game1 = sportmonk.get_fixtures(fixture_id=fixture_id)['data']

    game1 = sportmonk.fixture_statistics_lookups(game1)
    game1 = sportmonk.fixture_lineup_detail_lookups(game1)
    game1 = sportmonk.fixture_lineup_lookups(game1)

    output_data_table(game1, fixture_table, output_directory='sample_data', duplicate_remove=True)
    output_data_table(game1, event_table, output_directory='sample_data', duplicate_remove=True)
    output_data_table(game1, player_performance_table, output_directory='sample_data', duplicate_remove=True)

    return game1


def test_game_range(date_start='2023-01-01', date_end='2024-06-01'):
    include = ['lineups', 'events', 'statistics', 'timeline', 'lineups.details',
               'participants',
               'scores', 'periods', 'ballCoordinates', 'xGFixture', 'formations']
    games = sportmonk.get_fixtures(date=date_start, date_range_end=date_end, include=include)
    variables = {}
    for fixture in games['data']:

        fixture = sportmonk.fixture_statistics_lookups(fixture)
        fixture = sportmonk.fixture_lineup_detail_lookups(fixture)
        fixture = sportmonk.fixture_lineup_lookups(fixture)

        output_data_table(fixture, fixture_table, output_directory='sample_data', duplicate_remove=True)
        output_data_table(fixture, event_table, output_directory='sample_data', duplicate_remove=True)
        output_data_table(fixture, player_performance_table, output_directory='sample_data', duplicate_remove=True)


if __name__ == '__main__':
    # games = test_game_range(date_start='2024-02-01', date_end='2024-03-01')
    # test_game_range()
    game = test_single_game(18454566)
    # players_table()
    # output_data_table(None, players_table, output_directory='sample_data', duplicate_remove=True)
    event_dict = {}
