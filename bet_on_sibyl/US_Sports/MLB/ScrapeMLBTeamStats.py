from urllib import urlopen

import pandas as pd
from bs4 import BeautifulSoup
import requests

from bet_on_sibyl.utils import selenium_get_page_content


class AcquireTeamStats(object):
    # Creates a csv file containing cummulative data by season for each
    # team that played games between input 'year1' and 'year2'.
    # When you finished to make your modif' do not forget to convert
    # your file in '.py' to make it usesable as class in other programs

    def __init__(self, year_start, year_end, csv_filename):
        self.year_start = year_start
        self.year_end = year_end
        self.csv_filename = csv_filename

    def __call__(self):
        print('Year Start: {}'.format(self.year_start))
        print('Year End: {}'.format(self.year_end))

        # --------------------------Batting Stats---------------------------------
        print "=> Scraping Batting Stats..."
        self.get_batting_team_stats(self.year_start, self.year_end)
        self.clean_batting_data(self.batting_season_df)
        print "=> Scraping Batting Stats...OK"

        # --------------------------Pitching Stats---------------------------------
        print "=> Scraping Pitching Stats..."
        self.get_pitching_team_stats(self.year_start, self.year_end)
        self.clean_pitching_data(self.pitching_season_df)
        print " Scraping Pitching Stats...OK"

        # ------------------------Merge Data Frames & Write to csv----------------
        self.write_to_csv(self.csv_filename, self.batting_season_df, self.pitching_season_df)

    # ----------------------------BATTING FUNCTIONS------------------------------------
    def get_batting_team_stats(self, year1, year2):
        """Get data from the Teams Standard Batting table.

        This table loads immediately on the web page, so it is possible (and quicker)
        to grab the content directly.
        """
        # creating a url template that will allow us to access the web page for each year
        url_template = "http://www.baseball-reference.com/leagues/MLB/{}.shtml"

        # create the empty all season dataframe
        batting_season_df = pd.DataFrame()

        for year in range(year1, year2 + 1):
            url = url_template.format(year)  # for each year
            html = urlopen(url)  # get the url
            soup = BeautifulSoup(html, 'html5lib')  # Creating a BS object

            # Indexing the right table
            team_batting_table = soup.find('table', id="teams_standard_batting")
            if not team_batting_table:
                TEAM_BATTING_ERROR = 'The team batting table was not found!'
                raise RuntimeError(TEAM_BATTING_ERROR)

            # Record the column headers the last time through the loop
            # (for the latest year).
            if year == year2:
                batting_column_headers = [th.getText() for th in team_batting_table.find_all('tr', limit=1)[0].find_all('th')]

            # Get the team batting data
            teams_batting_data = []
            data_rows = team_batting_table.find_all('tr')[1:]
            for row in data_rows:
                # Get team name
                team_name = row.find('th').getText()
                team_batting_data = [team_name]

                # Get stats
                for td in row.find_all('td'):
                    team_batting_data.append(td.getText())

                # Add this teams data to the teams list
                teams_batting_data.append(team_batting_data)

            # Turn yearly data into a data frame
            year_df = pd.DataFrame(teams_batting_data, columns=batting_column_headers)

            # Insert Season_Yr
            year_df.insert(1, 'Season_Yr', year)

            # Append the data to the big data frame
            batting_season_df = batting_season_df.append(year_df, ignore_index=True)

        self.batting_season_df = batting_season_df


    # -----------------------------------------PITCHING FUNCTIONS--------------------------------
    def get_pitching_team_stats(self, year1, year2):
        """Get data from the Teams Standard Pitching table.

        This table does not load immediately and using selenium is required.
        """
        # creating a url template that will allow us to access the web page for each year
        url_template = "http://www.baseball-reference.com/leagues/MLB/{year}.shtml"

        # create the empty all season dataframe
        pitching_season_df = pd.DataFrame()

        for year in range(year1, year2 + 1):
            soup = selenium_get_page_content(url_template.format(year=year))

            # Find the "Team Standard Pitching" table
            team_pitching_table = soup.find('table', id="teams_standard_pitching")
            if not team_pitching_table:
                TEAM_PITCHING_ERROR = 'The team pitching table was not found!'
                raise RuntimeError(TEAM_PITCHING_ERROR)

            # Record the column headers the last time through the loop
            # (for the latest year).
            if year == year2:
                 pitching_column_headers = [th.getText() for th in team_pitching_table.find_all('tr', limit=1)[0].find_all('th')]

            # Get the team pitching data
            teams_pitching_data = []
            data_rows = team_pitching_table.find_all('tr')[1:]
            for row in data_rows:
                # Get team name
                team_name = row.find('th').getText()
                team_pitching_data = [team_name]

                # Get stats
                for td in row.find_all('td'):
                    team_pitching_data.append(td.getText())

                # Add this teams data to the teams list
                teams_pitching_data.append(team_pitching_data)

            # Turn yearly data into a data frame
            year_df = pd.DataFrame(teams_pitching_data, columns=pitching_column_headers)

            # Insert Season_Yr
            year_df.insert(1, 'Season_Yr', year)

            # Append the data to the big data frame
            pitching_season_df = pitching_season_df.append(year_df, ignore_index=True)

        self.pitching_season_df = pitching_season_df
        #pitching_season_df.to_csv('team_pitching.csv', encoding='utf-8')

    def clean_batting_data(self, batting_season_df):
        # TODO: We are writing this out onto a csv and re-reading it in somewhere else.. right?
        # Convert the data to the proper data frame
        # batting_season_df = batting_season_df.apply(pd.to_numeric, errors="ignore")

        # Get rid of the 'league average' and empty column values rows
        batting_season_df = batting_season_df[batting_season_df.Tm != 'LgAvg']
        batting_season_df = batting_season_df[batting_season_df.Tm != '']
        batting_season_df = batting_season_df[batting_season_df.Tm != 'Tm']
        batting_season_df = batting_season_df[batting_season_df.Tm.notnull()]

        # Rename the columns
        # get the column names and replace all '%' with '_Perc'
        batting_season_df.columns = batting_season_df.columns.str.replace('%', '_Perc')

        # get the column names and replace all '#' with 'Nb'
        batting_season_df.columns = batting_season_df.columns.str.replace('#', 'Nb_')

        # get the column names and replace all '+' with '_Plus'
        batting_season_df.columns = batting_season_df.columns.str.replace('+', '_Plus')

        # and replace all '/' with '_per_'
        batting_season_df.columns = batting_season_df.columns.str.replace('/', '_per_')

        # Delete the columns we do not need in both data frames
        if 'BatAge' in batting_season_df.columns:
            batting_season_df.drop('BatAge', axis='columns', inplace=True)
        if 'Nb_Bat' in batting_season_df.columns:
            batting_season_df.drop('Nb_Bat', axis='columns', inplace=True)
        if 'G' in batting_season_df.columns:
            batting_season_df.drop('G', axis='columns', inplace=True)
        if 'W' in batting_season_df.columns:
            batting_season_df.drop('W', axis='columns', inplace=True)
        if 'L' in batting_season_df.columns:
            batting_season_df.drop('L', axis='columns', inplace=True)
        if 'GS' in batting_season_df.columns:
            batting_season_df.drop('GS', axis='columns', inplace=True)
        if 'GF' in batting_season_df.columns:
            batting_season_df.drop('GF', axis='columns', inplace=True)
        if 'Nb_P' in batting_season_df.columns:
            batting_season_df.drop('Nb_P', axis='columns', inplace=True)

        # Add a prefix to designate this data as batting data (except for 'Tm' col)
        batting_season_df.columns = ['Tm', 'Season_Yr'] + ['B_' + str(col) for col in batting_season_df.columns if col not in ['Tm', 'Season_Yr']]


        self.batting_season_df = batting_season_df
        batting_season_df.to_csv('team_batting.csv', encoding='utf-8')

    def clean_pitching_data(self, pitching_season_df):
        # TODO: We are writing this out onto a csv and re-reading it in somewhere else.. right?
        # Convert the data to the proper data frame
        # pitching_season_df = pitching_season_df.apply(pd.to_numeric, errors="ignore")

        # Get rid of the 'league average' and empty column values rows
        pitching_season_df = pitching_season_df[pitching_season_df.Tm != 'LgAvg']
        pitching_season_df = pitching_season_df[pitching_season_df.Tm != '']
        pitching_season_df = pitching_season_df[pitching_season_df.Tm != 'Tm']
        pitching_season_df = pitching_season_df[pitching_season_df.Tm.notnull()]

        # Rename the columns
        # replace the 'W/L%' by 'WinLoss%' to avoid the '_' which seems to cause trouble in table operations
        pitching_season_df.columns = pitching_season_df.columns.str.replace('W-L%', 'WinLoss%')

        # get the column names and replace all '%' with '_Perc'
        pitching_season_df.columns = pitching_season_df.columns.str.replace('%', '_Perc')

        # get the column names and replace all '#' with 'Nb'
        pitching_season_df.columns = pitching_season_df.columns.str.replace('#', 'Nb_')

        # get the column names and replace all '+' with 'Nb'
        pitching_season_df.columns = pitching_season_df.columns.str.replace('+', '_Plus')

        # and replace all '/' with '_per_'
        pitching_season_df.columns = pitching_season_df.columns.str.replace('/', '_per_')

        # Delete the columns we do not need in both data frames
        if 'PAge' in pitching_season_df.columns:
            pitching_season_df.drop('PAge', axis='columns', inplace=True)
        if 'G' in pitching_season_df.columns:
            pitching_season_df.drop('G', axis='columns', inplace=True)
        if 'W' in pitching_season_df.columns:
            pitching_season_df.drop('W', axis='columns', inplace=True)
        if 'L' in pitching_season_df.columns:
            pitching_season_df.drop('L', axis='columns', inplace=True)
        if 'GS' in pitching_season_df.columns:
            pitching_season_df.drop('GS', axis='columns', inplace=True)
        if 'GF' in pitching_season_df.columns:
            pitching_season_df.drop('GF', axis='columns', inplace=True)
        if 'Nb_P' in pitching_season_df.columns:
            pitching_season_df.drop('Nb_P', axis='columns', inplace=True)
        #if 'Tm' in pitching_season_df.columns:
        #    pitching_season_df.drop('Tm', axis='columns', inplace=True)
        #if 'Season_Yr' in pitching_season_df.columns:
        #    pitching_season_df.drop('Season_Yr', axis='columns', inplace=True)

        # Add a prefix to designate this data as pitching data (except for 'Tm' col)
        pitching_season_df.columns = ['Tm', 'Season_Yr'] + ['P_' + str(col) for col in pitching_season_df.columns if col not in ['Tm', 'Season_Yr']]

        self.pitching_season_df = pitching_season_df
        pitching_season_df.to_csv('team_pitching.csv', encoding='utf-8')

    def write_to_csv(self, csv_filename, batting_season_df, pitching_season_df):
        # Merge both batting and pitching data frames
        big_df = batting_season_df.merge(pitching_season_df, how='inner')

        # Rename duplicates as some issue may happen when uploading in sqlite
        # cols = pd.Series(big_df.columns)
        # for dup in big_df.columns.get_duplicates():
        #     cols[big_df.columns.get_loc(dup)] = [
        #         'P_' + dup if d_idx != 0 else 'B_' + dup for d_idx in
        #         range(big_df.columns.get_loc(dup).sum())]
        # big_df.columns = cols

        big_df.to_csv(csv_filename, mode='w+')
