# coding: utf-8

import sys
import numpy as np
import os

from RunModelMLB import MLBMakePredictions
from ScrapeMatchupDatetimeOddsTwoChoicesMLB import AcquireMatchupDatetimeOddsTwoChoices
from SibylVsBookiesMLB import AcquireSibylVsBookiesMLB
from ModelMetricsMLB import ModelMetricsMLB

# get_ipython().magic(u'matplotlib inline')

betbrain_upcoming_games_url='https://www.betbrain.com/baseball/united-states/mlb/'
oddsportal_url_fix='http://www.oddsportal.com/baseball/usa/mlb/results/'
oddsportal_url_list_format='http://www.oddsportal.com/baseball/usa/mlb/results/#/page/{}/'


class ModelMLB(object):

    def __init__(self, current_season, feature_file, mlb_db_name,
                 cs_team_stats_filename,
                 upcoming_game_outputs_filename_us,
                 upcoming_games_output_filename_eu,
                 ):
        self.current_season = current_season
        self.feature_file = feature_file
        self.data = np.load(feature_file)
        self.tableau_input_filename = "mlb_tableau_output_" + str(current_season) + ".csv"
        self.current_season = current_season
        self.X = self.data['X']
        self.y = self.data['y']
        self.mlb_db_name = mlb_db_name
        self.cs_team_stats_filename = cs_team_stats_filename
        self.league_name = 'MLB'
        self.upcoming_game_outputs_filename_us = upcoming_game_outputs_filename_us
        self.upcoming_games_output_filename_eu = upcoming_games_output_filename_eu
        self.cs_team_stats_filename = cs_team_stats_filename
        self.season_over = 'No'

    def __call__(self):
        print "MLB Machine Learning process execution..."
        x = MLBMakePredictions(
            self.current_season,
            self.feature_file,
            self.mlb_db_name
        )
        x()
        print "MLB Machine Learning process execution...OK\n"

        print "MLB Scraping odds and datetime from Betbrain.com process execution..."
        w = AcquireMatchupDatetimeOddsTwoChoices(
            self.season_over,
            betbrain_upcoming_games_url,
            self.cs_team_stats_filename,
            self.league_name,
            self.tableau_input_filename,
            self.upcoming_game_outputs_filename_us,
            self.upcoming_games_output_filename_eu)
        w()
        print "MLB Scraping odds and datetime from Betbrain.com process execution...OK\n"

        # ----------------------------------------------------------------------------

        self.season_over = w.season_over
        print self.league_name + ' season is over? : ' + self.season_over + '=> '
        if self.season_over == 'No':
            print "Moving on...\n"
        else:
            print "Season over => Stopping the MLB process\n"

        # ----------------------------------------------------------------------------

        print "MLB Sibyl vs Bookies process execution..."
        v = AcquireSibylVsBookiesMLB(
            self.season_over,
            oddsportal_url_fix,
            oddsportal_url_list_format,
            self.cs_team_stats_filename,
            self.tableau_input_filename
        )
        v()
        print "MLB Sibyl vs Bookies process execution...OK\n"

        print "MLB ModelMetrics process execution..."
        u = ModelMetricsMLB(
            self.season_over,
            self.tableau_input_filename,
            self.upcoming_game_outputs_filename_us,
            self.cs_team_stats_filename
        )
        u()
        print "MLB ModelMetrics process execution...OK\n"


if __name__ == '__main__':
    # TODO - learn what these files are and where they should live
    npz_file = os.path.join(os.path.dirname(__file__), 'mlb_1980_2014_features.npz')
    print 'NPZ_FILE: {}'.format(npz_file)

    x = ModelMLB(
        current_season=2016,
        feature_file=npz_file,
        mlb_db_name='mlb_team_data_2016.db',
        cs_team_stats_filename='mlb_team_stats_2016_2016.csv',
        upcoming_game_outputs_filename_us='MLB_Upcoming_Matchups_US_P_df.csv',
        upcoming_games_output_filename_eu='MLB_Upcoming_Matchups_EU_P_df.csv',
    )
    x()

# x = ModelMLB(
#     2016,
#     'mlb_1980_2014_features.npz',
#     'mlb_team_data_2016.db',
#     'https://www.betbrain.com/baseball/united-states/mlb/mlb/#/winner/whole-event/',\
#     'https://www.betbrain.com/baseball/united-states/mlb/',
#     'mlb_team_stats_2016_2016.csv',
#     'MLB',
#     'MLB_Upcoming_Matchups_US_P_df',
#     'MLB_Upcoming_Matchups_EU_P_df',
#     'http://www.oddsportal.com/baseball/usa/mlb/results/',
#     'http://www.oddsportal.com/baseball/usa/mlb/results/#/page/{}/'
# )
# Think to build the main section to run all of this from a terminal
