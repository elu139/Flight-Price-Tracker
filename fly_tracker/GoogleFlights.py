"""
Searches Google Flights (via fast-flights, no browser needed) for one-way or round-trip fares
"""
import datetime
import json
import pandas as pd
from fast_flights import FlightQuery, FlightsNotFound, create_query, fetch_flights_html
from fast_flights.parser import parse_js
from selectolax.lexbor import LexborHTMLParser


def fetch_itineraries(query) -> list:
    """
    fast-flights' get_flights() only parses Google's "top flights" list (payload[3]) and silently
    drops the "best flights" list (payload[2]), which can hold the cheapest fare (e.g. Frontier).
    Parse both. Overlaps are removed later by FlightSearch.to_df.
    """
    js = LexborHTMLParser(fetch_flights_html(query)).css_first(r"script.ds\:1").text()
    results = list(parse_js(js))  # raises FlightsNotFound on a Google error
    payload = json.loads(js.split("data:", 1)[1].rsplit(",", 1)[0])
    if payload[2] and payload[2][0]:
        payload[3] = payload[2]
        results += parse_js("data:" + json.dumps(payload) + ",")
    return results


class FlightSearch:
    """
    One-way search when return_date is None, round trip otherwise.
    src/dest are IATA airport codes (e.g. BOS), dates are YYYY-MM-DD.
    """

    def __init__(self, src: str, dest: str, price: int, date: str, return_date: "str | None" = None) -> None:
        self.src = src.upper()
        self.dest = dest.upper()
        self.price = int(price)
        self.date = date
        self.return_date = return_date

    def search(self) -> pd.DataFrame:
        """
        Returns:
            pd.DataFrame: fares at or below self.price, cheapest first
        """
        legs = [FlightQuery(date=self.date, from_airport=self.src, to_airport=self.dest)]
        if self.return_date:
            legs.append(FlightQuery(date=self.return_date, from_airport=self.dest, to_airport=self.src))
        query = create_query(
            flights=legs,
            trip="round-trip" if self.return_date else "one-way",
            currency="USD",
            language="en-US",
        )
        try:
            results = fetch_itineraries(query)
        except FlightsNotFound:
            results = []
        return self.to_df(results)

    def to_df(self, results) -> pd.DataFrame:
        """
        Flatten fast-flights results into rows, dropping fares above the threshold
        """
        rows = []
        now = datetime.datetime.now()
        for itinerary in results:
            if itinerary.price > self.price:
                continue
            first, last = itinerary.flights[0], itinerary.flights[-1]
            rows.append({
                "Source": first.from_airport.code,
                "Departure Time": "%02d:%02d" % first.departure.time,
                "Destination": last.to_airport.code,
                "Arrival Time": "%02d:%02d" % last.arrival.time,
                "Stops": len(itinerary.flights) - 1,
                "Date": self.date,
                "Return Date": self.return_date or "",
                # Round trip: Google's total for both legs; outbound details shown
                "Price": itinerary.price,
                "Airline": ", ".join(itinerary.airlines),
                "Timestamp": now,
            })
        df = pd.DataFrame(rows).drop_duplicates()
        return df.sort_values("Price", ignore_index=True) if rows else df
