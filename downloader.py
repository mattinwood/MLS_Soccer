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
               'formations', 'participants', 'participants.players.player',
               'scores', 'periods', 'ballCoordinates', 'xGFixture',
               ]
    games = sportmonk.get_fixtures(date=date_start, date_range_end=date_end, include=include)
    for fixture in games['data']:
        try:
            data = data_normalizer.export_fixture(fixture, 'database')
        except:
            print(f'Error on fixture: {fixture["id"]}')


def backfill_fixtures_by_year(year):
    for q in generate_quarters(year):
        print(q)
        download_fixtures_date_range(q[0], q[1])


if __name__ == '__main__':
    for year in [2022, 2023, 2024]:
        backfill_fixtures_by_year(year)
    backfill_fixtures_by_year(2025)
    # data_normalizer.test_single_game(18449909)  # One-offs for testing
