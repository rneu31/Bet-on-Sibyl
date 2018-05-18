from urllib import urlopen

import pandas as pd
from bs4 import BeautifulSoup

# unverified requests because work internet sucks
import ssl; ssl._create_default_https_context = ssl._create_unverified_context

class AcquireGameStats(object):
    # Creates a csv file containing all the matchup results between
    # teams for all seasons between inputs 'year1' and 'year2'.

    def __init__(self, year0, year1, year2, csv_filename, csv_datetime_filename):
        self.year0 = year0
        self.year1 = year1
        self.year2 = year2
        self.csv_filename = csv_filename
        self.csv_datetime_filename = csv_datetime_filename

    def __call__(self):
        print "Scraping game data..."
        self.get_gs_column_headers(self.year0)
        self.get_game_data(self.year1, self.year2, self.gs_column_headers)
        self.clean_gs_data(self.game_df)
        print "Scraping game data...OK"

    # Getting the column headers
    def get_gs_column_headers(self, year0):
        html_page = urlopen(
            'http://www.baseball-reference.com/teams/BAL/{year0}-schedule-scores.shtml'.format(year0=year0))
        soup = BeautifulSoup(html_page, "html5lib")
        schedule_table = soup.find('table', id="team_schedule")

        # Use data-stat instead of getText() because every
        # column has one, and they are more descriptive.
        gs_column_headers = []
        for th in schedule_table.find('thead').find_all('th'):
            gs_column_headers.append(th['data-stat'])

        self.gs_column_headers = gs_column_headers

    # Getting game data from year1 to year2
    def get_game_data(self, year1, year2, gs_column_headers):

        teams = ['ARI', 'ATL', 'BAL', 'BOS', 'CHC', 'CHW', 'CIN', 'CLE', 'COL', 'DET', 'HOU',
                 'KCR', 'LAA', 'LAD', 'MIA', 'MIL', 'MIN', 'NYM', 'NYY', 'OAK', 'PHI', 'PIT',
                 'SDP', 'SFG', 'SEA', 'STL', 'TBR', 'TEX', 'TOR', 'WSN']

        url_template = "http://www.baseball-reference.com/teams/{team}/{year}-schedule-scores.shtml"

        game_df = pd.DataFrame()

        for year in range(year1, year2 + 1):
            for team in teams:
                url = url_template.format(year=year, team=team)
                html = urlopen(url)
                soup = BeautifulSoup(html, 'html5lib')

                # Forming the yearly game data table
                #try:
                schedule_table = soup.find('table', id='team_schedule')
                if not schedule_table:
                    SCHEDULE_ERROR = 'The team schedule table was not found!'
                    raise RuntimeError(SCHEDULE_ERROR)

                games_data = []
                data_rows = schedule_table.find('tbody').find_all('tr')
                for row in data_rows:
                    # Since there are so many game logs they add
                    # the header row every so often so its easier for
                    # the viewer to remember the headings of the columns.
                    # Detect <tr class="thead"> and skip this row.
                    if row.has_attr('class') and 'thead' in row['class']:
                        continue

                    # Get "Gm#" content from the th in the tr
                    gm_num = row.find('th').getText()
                    game_data = [gm_num]

                    # Get other information
                    for td in row.find_all('td'):
                        game_data.append(td.getText().replace(u'\xa0', ' '))

                    # Add this game to games list
                    games_data.append(game_data)

                try:
                    year_df = pd.DataFrame(games_data, columns=gs_column_headers)
                except AssertionError as e:
                    print('URL: {}'.format(url))
                    print('Column Headers:\n{}'.format(gs_column_headers))
                    raise(e)

                # Add the year to the end of the entries in the date_game column
                year_df['date_game'] = year_df['date_game'].astype(str) + ', ' + str(year)

                # Append the data to the big data frame
                game_df = game_df.append(year_df, ignore_index=True)
                self.game_df = game_df

                # debug
                # game_df.to_csv('df.csv', encoding='utf-8')

    # Cleaning the data
    def clean_gs_data(self, game_df):
        # Create new dataframe inluding only the home games (games
        # where homeORvis does not indicate an away game) to avoid
        # duplicates in the big data frame.
        filtered_game_df = game_df[game_df['homeORvis'] != '@'].copy()

        # Dropping several columns we do not need
        filtered_game_df.drop(
          columns=[
            'team_game', 'boxscore', 'homeORvis', 'win_loss_result', 'extra_innings', 'win_loss_record',
            'rank', 'games_back', 'winning_pitcher', 'losing_pitcher', 'saving_pitcher', 'time_of_game',
            'day_or_night', 'attendance', 'win_loss_streak', 'reschedule'
          ],
          inplace=True
        )

        # When two games are played on the same day they have the format
        # May 7 (1) and May 7 (2). Remove the numbers and parenthesis
        # including the space before.
        filtered_game_df.date_game.replace(r"\s\(.*\)", "", regex=True, inplace=True)

        # Convert the column date_game to datetime to ease indexing the year
        # See notes here for why the syntax seems weird:
        #game_df = pd.to_datetime(game_df.loc[:, ('date_game')], format='%A, %b %d, %Y')
        #filtered_game_df.date_game = filtered_game_df.date_game.dt.strftime('%A, %b %d, %Y')
        filtered_game_df.date_game = pd.to_datetime(filtered_game_df.date_game, format='%A, %b %d, %Y')

        # Extracte exclusively the 'date_game' column to a csv file
        # for further analysis in Tableau with "tableau_input" file
        filtered_game_df.date_game.to_csv(self.csv_datetime_filename, mode='w+', header=False, index=False)

        # Index the year to create a column 'Season_Yr' for then easing the indexing
        # way in sqlite "Team" + "Year"
        filtered_game_df['Season_Yr'] = filtered_game_df.date_game.apply(lambda x: x.year)
        #filtered_game_df.insert(1, 'Season_Yr', game_df['Date'].apply(lambda x: x.year))

        # Drop the column 'date_game' as we do not need it anymore
        filtered_game_df.drop(columns=['date_game'], inplace=True)

        # Rename and reorder columns to match requirements for code that is
        # ran after this:
        # Season_Yr, Visitor_Team, V_PTS, Home_Team, H_PTS
        filtered_game_df.rename(
          columns={
            'opp_ID': 'Visitor_Team',
            'RA': 'V_PTS',
            'team_ID': 'Home_Team',
            'R': 'H_PTS'
          },
          inplace=True
        )

        ordered_df = filtered_game_df.reindex(columns=['Season_Yr', 'Visitor_Team', 'V_PTS', 'Home_Team', 'H_PTS'])

        # Write the csv file
        ordered_df.to_csv(self.csv_filename, mode='w+', index=False)
