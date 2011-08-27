#!/usr/bin/env python
# coding: utf-8

"""
Tests for pycavane api
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(__file__).rsplit(os.sep, 2)[0])

import api

def repopulate_cache():
    api.setup("guicavane", "guicavane", cache_dir="./", cache_lifetime=13**37)

    house_search = [x for x in api.Show.search("house")]
    house = [x for x in house_search if x.name == "House M.D."][0]
    house_seasons = [x for x in house.seasons]
    house_season_4 = [x for x in house_seasons if x.name == "Temporada 4"][0]
    house_season_4_episodes = [x for x in house_season_4.episodes]
    house_season_4_episodes_names = [x.name for x in house_season_4_episodes]
    house_season_4_episodes_info = [x.info for x in house_season_4_episodes]
    house_season_4_episodes_description = [x.description for x in house_season_4_episodes]

    friends_search = [x for x in api.Show.search("friends")]
    friends = [x for x in friends_search if x.name == "Friends"][0]
    friends_seasons = [x for x in friends.seasons]
    friends_season_8 = [x for x in friends_seasons if x.name == "Temporada 8"][0]
    friends_season_8_episodes = [x for x in friends_season_8.episodes]
    friends_season_8_episodes_names = [x.name for x in friends_season_8_episodes]
    friends_season_8_episodes_info = [x.info for x in friends_season_8_episodes]
    friends_season_8_episodes_description = [x.description for x in friends_season_8_episodes]

    matrix_search = [x for x in api.Movie.search("matrix")]
    matrix = [x for x in matrix_search if x.name == "Matrix"][0]
    matrix_info = matrix.info
    matrix_description = matrix.description


class TestApi(unittest.TestCase):

    def setUp(self):
        api.setup("guicavane", "guicavane", cache_dir="./", cache_lifetime=13**37)

    def test_existing_show_search(self):
        results = [x for x in api.Show.search("house")]
        results_names = [x.name for x in results]
        self.assertTrue("House M.D." in results_names)

        results = [x for x in api.Show.search("friends")]
        results_names = [x.name for x in results]
        self.assertTrue("Friends" in results_names)

    def test_nonexisting_show_search(self):
        results = [x for x in api.Show.search("sopleteduranio")]
        self.assertTrue(len(results) == 0)

    def test_show_info(self):
        house = [x for x in api.Show.search("house") if x.name.count("House M.D.")][0]
        self.assertTrue(not house.name.endswith("..."))

        expected_desc =  "El doctor Gregory House, especialista"
        expected_desc += "en el tratamiento de enfermedades infecciosas,"
        expected_desc += "trabaja en un hospital universitario de Princetown,"
        expected_desc += "donde dirige una unidad especial encargada de pacientes "
        expected_desc += "afectados por dolencias extrañas y en la que colabora"
        expected_desc += "con un selecto grupo de aventajados ayudantes."

        self.assertTrue(house.description == expected_desc)

    def test_season(self):
        house = [x for x in api.Show.search("house") if x.name == "House M.D."][0]
        seasons = [x for x in house.seasons]

        self.assertTrue(len(seasons) > 0)

        season_4 = [x for x in seasons if x.name == "Temporada 4"][0]
        season_4_episodes = [x for x in season_4.episodes]

        self.assertTrue(int(season_4.id) == 22)
        self.assertTrue(len(season_4_episodes) > 0)
        self.assertTrue(len(season_4_episodes) < 17)

        friends = [x for x in api.Show.search("friends") if x.name == "Friends"][0]
        seasons = [x for x in friends.seasons]

        self.assertTrue(len(seasons) > 0)

        season_8 = [x for x in seasons if x.name == "Temporada 8"][0]
        season_8_episodes = [x for x in season_4.episodes]

        self.assertTrue(int(season_8.id) == 116)
        self.assertTrue(len(season_8_episodes) > 0)
        self.assertTrue(len(season_8_episodes) < 25)

    def test_episodes(self):
        house = [x for x in api.Show.search("house") if x.name == "House M.D."][0]
        season_4 = [x for x in house.seasons if x.name == "Temporada 4"][0]
        episodes = [x for x in season_4.episodes]

        self.assertTrue(len(episodes) > 0)

        episode_15 = episodes[14]

        self.assertTrue(not episode_15.name.endswith("..."))
        self.assertEqual(episode_15.name, "House's Head")
        self.assertEqual(episode_15.genere, "Drama")
        self.assertEqual(int(episode_15.number), 15)
        self.assertTrue("Hugh Laurie" in episode_15.cast)


if __name__ == "__main__":
    if "--repopulate" in sys.argv:
        repopulate_cache()
        sys.argv.remove("--repopulate")

    unittest.main()
