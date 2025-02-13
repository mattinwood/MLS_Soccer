import sportmonk, data_normalizer
from datetime import datetime
from dateutil.relativedelta import relativedelta


def generate_quarters(season=2023):
    quarters = []
    start = datetime(season, 1, 1)
    for _ in range(4):
        end = start + relativedelta(months=3, days=-1)
        quarters.append((start.isoformat()[0:10], end.isoformat()[0:10]))
        start = end + relativedelta(days=1)
    return quarters

def download_fixtures_date_range(date_start, date_end):
    include = ['lineups', 'events', 'statistics', 'timeline', 'lineups.details',
               'participants',
               'scores', 'periods', 'ballCoordinates', 'xGFixture', 'formations']
    games = sportmonk.get_fixtures(date=date_start, date_range_end=date_end, include=include)
    variables = {}
    for fixture in games['data']:
        try:
            fixture = sportmonk.fixture_statistics_lookups(fixture)
            fixture = sportmonk.fixture_lineup_detail_lookups(fixture)
            fixture = sportmonk.fixture_lineup_lookups(fixture)

            # TODO: Add Ball Coordinates

            data_normalizer.output_data_table(fixture, data_normalizer.fixture_table, output_directory='database', duplicate_remove=True)
            data_normalizer.output_data_table(fixture, data_normalizer.event_table, output_directory='database', duplicate_remove=True)
            data_normalizer.output_data_table(fixture, data_normalizer.player_performance_table, output_directory='database', duplicate_remove=True)
        except:
            print(f'Error on fixture: {fixture["id"]}')


def backfill_fixtures_by_year(year):
    for q in generate_quarters(year):
        print(q)
        download_fixtures_date_range(q[0], q[1])


def update_players():
    pass


if __name__ == '__main__':
    # download_fixtures_date_range('2023-03-18', '2023-03-18')
    backfill_fixtures_by_year(2024)
