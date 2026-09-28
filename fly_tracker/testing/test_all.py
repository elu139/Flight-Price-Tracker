"""
Unit tests for Scraper.py
"""
import unittest
import sys
from unittest.mock import Mock, patch
import pandas as pd
from bs4 import BeautifulSoup
from types import SimpleNamespace
from fly_tracker import Scraper, Notifier, GoogleFlights
sys.path.append('../')
sys.path.append('./')
sys.path.append('testing/')

class TestPriceScraper(unittest.TestCase):
    """
    Unit Tests for the PriceScraper class
    Args:
        unittest (_type_): _description_
    """

    def setUp(self):
        self.PriceScraper = Scraper.PriceScraper(
            'New York', 'Boston', 100, '12 May')
        self.expected_df = pd.DataFrame(
            {
                'src': ['New York', 'New York', 'New York'],
                "dest": ['Boston', 'Boston', 'Boston'],
                "Price": [100, 104, 107]
            }
        )
        #file_path = os.path.join(os.path.join(os.getcwd(),'testing'),"test_source_page.html")
        #file = open(file_path, "r", encoding='utf-8')
        #self.mock_page_source = file.read()
        #file.close()
        self.mock_page_source = "<html> </html>"
        self.expected_soup = BeautifulSoup(
            self.mock_page_source, 'html.parser')
        self.email = 'test@example.com'
        self.notifier = Notifier(self.email, self.expected_df, self.PriceScraper)

    def test_preprocess(self) -> None:
        """
        Test for preprocess
        """
        self.PriceScraper.preprocess()
        self.assertEqual(self.PriceScraper.src, 'New-York')
        self.assertEqual(self.PriceScraper.dest, 'Boston')

    @patch('pandas.DataFrame')
    def test_create_df(self, mock_dataframe) -> None:
        """
        Unit Test for Scraper.create_df function
        Args:
            mock_dataframe (_type_): _description_
        """
        mock_json_data = [
            {"src": 'New York', "dest": 'Boston', "Price": 100},
            {"src": 'New York', "dest": 'Boston', "Price": 104},
            {"src": 'New York', "dest": 'Boston', "Price": 107}
        ]
        mock_dataframe.return_value = self.expected_df
        df = self.PriceScraper.create_df(mock_json_data)
        pd.testing.assert_frame_equal(df, self.expected_df)
        mock_dataframe.assert_called_once_with(mock_json_data)

    @patch.object(Scraper.PriceScraper, 'parser')
    def test_parser(self, mock_parser) -> None:
        """
        Unit Test for Scraper.Parser function
        Args:
            mock_parser (MagicMock): _description_
        """
        expected_data = [{
            "Source": "New York",
            "Departure Time": "10:00",
            "Destination": "Boston",
            "Arrival Time": "12:00",
            "Date": "2022-05-01",
            "Price": "100",
            "Airline": "Air India",
            "Timestamp": "2023-03-31 00:00:00.000000"
        }]
        mock_parser.return_value = expected_data

        soup = self.expected_soup
        data = self.PriceScraper.parser(soup)

        self.assertEqual(data, expected_data)
        mock_parser.assert_called_once_with(soup)

    @patch('bs4.BeautifulSoup', autospec=True)
    def test_soupify(self, mock_soup):
        """
        Unit Test for Scraper.Soupify function
        Args:
            mock_soup (_type_): _description_
        """
        mock_soup.return_value = self.expected_soup
        soup = self.PriceScraper.soupify(self.mock_page_source)
        self.assertEqual(soup, self.expected_soup)
        # mock_soup.assert_called_once_with(self.mock_page_source,features='html.parser')

    @patch('selenium.webdriver.Chrome', autospec=True)
    def test_get_page(self, mock_driver):
        """
        Unit Test for Scraper.get_page function
        Args:
            mock_driver (_type_): _description_
        """
        mock_driver.page_source = self.mock_page_source
        mock_response = Mock()
        mock_response.status_code = 200
        # create a mock driver.get() method
        mock_driver.return_value.get.return_value = mock_response.status_code
        page_source = self.PriceScraper.get_page()
        self.assertIsNotNone(page_source)

    @patch('smtplib.SMTP')
    def test_send_mail(self, mock_smtp):
        """
        Unit Test for Notifier.send_mail function
        Args:
            mock_smtp (_type_): _description_
        """
        self.notifier.send_mail(self.notifier.create_message())
        mock_smtp.return_value.sendmail.assert_called_once()

    def test_create_message(self):
        """
        Unit Test for Notifier.create_message function
        """
        msg = self.notifier.create_message()
        self.assertEqual(msg['From'], self.notifier.sender)
        self.assertEqual(msg['To'], self.email)
        self.assertEqual(msg['Subject'], f"FLY_TRACKER: {self.PriceScraper.src} to {self.PriceScraper.dest} on {self.PriceScraper.date} fares")

class TestFlightSearch(unittest.TestCase):
    """
    Unit Tests for GoogleFlights.FlightSearch
    """

    @staticmethod
    def itinerary(price, airline, legs):
        """Fake fast-flights result: legs = [(from, to, dep_time, arr_time), ...]"""
        return SimpleNamespace(price=price, airlines=[airline], flights=[
            SimpleNamespace(from_airport=SimpleNamespace(code=a), to_airport=SimpleNamespace(code=b),
                            departure=SimpleNamespace(time=dep), arrival=SimpleNamespace(time=arr))
            for a, b, dep, arr in legs])

    def test_round_trip(self) -> None:
        """
        Round trip sends both legs, filters by price, sorts cheapest first
        """
        results = [
            self.itinerary(432, 'Delta', [('BOS', 'ATL', (5, 30), (8, 40))]),
            self.itinerary(250, 'United', [('BOS', 'IAD', (5, 30), (7, 0)), ('IAD', 'ATL', (8, 15), (10, 5))]),
            self.itinerary(299, 'JetBlue', [('BOS', 'ATL', (20, 55), (23, 59))]),
        ]
        search = GoogleFlights.FlightSearch('bos', 'atl', 300, '2026-11-07', '2026-11-09')
        with patch.object(GoogleFlights, 'get_flights', return_value=results) as mock_get:
            df = search.search()
        query = mock_get.call_args.args[0]
        self.assertEqual(query.get_trip_type(), 'round-trip')
        self.assertEqual(len(query.flight_data), 2)
        self.assertEqual(list(df['Price']), [250, 299])
        self.assertEqual(df.loc[0, 'Destination'], 'ATL')
        self.assertEqual(df.loc[0, 'Stops'], 1)
        self.assertEqual(df.loc[0, 'Arrival Time'], '10:05')
        self.assertIn('returning 2026-11-09', Notifier('a@b.c', df, search).create_message()['Subject'])

    def test_one_way_nothing_found(self) -> None:
        """
        One-way sends a single leg; no results gives an empty frame
        """
        search = GoogleFlights.FlightSearch('BOS', 'ATL', 300, '2026-11-07')
        with patch.object(GoogleFlights, 'get_flights', side_effect=GoogleFlights.FlightsNotFound) as mock_get:
            df = search.search()
        self.assertEqual(mock_get.call_args.args[0].get_trip_type(), 'one-way')
        self.assertTrue(df.empty)


if __name__ == '__main__':
    unittest.main()
