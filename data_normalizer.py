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


def find_key_in_nested_dict(nested_dict, target_key):
    for key, value in nested_dict.items():
        if key == target_key:
            return value
        elif isinstance(value, dict):
            result = find_key_in_nested_dict(value, target_key)
            if result is not None:
                return result


def dict_lookup(list_of_dicts: list, *args):
    for row in list_of_dicts:
        if all(find_key_in_nested_dict(row, key) == value for key, value in args):
            return row
    return {}


def fixture_table(data):
    fixture = [data[key] for key in ['id', 'name', 'starting_at', 'result_info']]

    home_team_id = dict_lookup(data['participants'], ('location', 'home'))['id']
    away_team_id = dict_lookup(data['participants'], ('location', 'away'))['id']

    fixture += [home_team_id, away_team_id]

    dict_lookup(data['scores'], ('description', '2ND_HALF'), ('participant', 'home'))

    performance = [
        [
            data['id'], home_team_id,
            dict_lookup(data['formations'], ('location', 'home')).get('formation'),
            dict_lookup(data['scores'], ('description', '1ST_HALF'), ('participant', 'home'))['score']['goals'],
            dict_lookup(data['scores'], ('description', '2ND_HALF'), ('participant', 'home'))['score']['goals'],
            dict_lookup(data['xgfixture'], ('location', 'home')).get('data', {}).get('value'),
            'home'
        ],
        [
            data['id'], away_team_id,
            dict_lookup(data['formations'], ('location', 'away'))['formation'],
            dict_lookup(data['scores'], ('description', '1ST_HALF'), ('participant', 'away'))['score']['goals'],
            dict_lookup(data['scores'], ('description', '2ND_HALF'), ('participant', 'away'))['score']['goals'],
            dict_lookup(data['xgfixture'], ('location', 'away')).get('data', {}).get('value'),
            'away'
        ]
    ]
    return {'fixture': fixture, 'performance': performance}


def output_data_table(data, function, output_directory='data', duplicate_remove=False):
    fixture = function(data)
    for table_nm in fixture.keys():
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


def test_single_game(fixture_id=19051563):
    game1 = sportmonk.get_fixtures(fixture_id=fixture_id)['data']

    game1 = sportmonk.fixture_statistics_lookups(game1)
    game1 = sportmonk.fixture_lineup_detail_lookups(game1)
    game1 = sportmonk.fixture_lineup_lookups(game1)

    output_data_table(game1, fixture_table, output_directory='sample_data', duplicate_remove=True)
    output_data_table(game1, event_table, output_directory='sample_data', duplicate_remove=True)
    output_data_table(game1, player_performance_table, output_directory='sample_data', duplicate_remove=True)

    return game1


def test_game_range(date_start='2023-01-01', date_end='2024-06-01', team='Chicago Fire'):
    include = ['lineups', 'events', 'statistics', 'timeline', 'lineups.details',
               'participants',
               'scores', 'periods', 'ballCoordinates', 'xGFixture', 'formations']
    games = sportmonk.get_fixtures(date=date_start, date_range_end=date_end,
                                   team=team, include=include)
    variables = {}
    for fixture in games['data']:

        fixture = sportmonk.fixture_statistics_lookups(fixture)
        fixture = sportmonk.fixture_lineup_detail_lookups(fixture)
        fixture = sportmonk.fixture_lineup_lookups(fixture)

        output_data_table(fixture, fixture_table, output_directory='sample_data', duplicate_remove=True)
        output_data_table(fixture, event_table, output_directory='sample_data', duplicate_remove=True)
        output_data_table(fixture, player_performance_table, output_directory='sample_data', duplicate_remove=True)


if __name__ == '__main__':
    test_game_range()
    # game = test_single_game()
    event_dict = {}
