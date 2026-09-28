import argparse
import time
from datetime import date, datetime
import schedule
from fly_tracker.GoogleFlights import FlightSearch
from fly_tracker.Notifier import Notifier

parser = argparse.ArgumentParser(description="Email me when a flight drops below a price")
parser.add_argument('--src', required=True, help="Origin airport code, e.g. BOS")
parser.add_argument('--dest', required=True, help="Destination airport code, e.g. ATL")
parser.add_argument('--price', required=True, type=int, help="Max price in USD")
parser.add_argument('--date', required=True, type=date.fromisoformat, help="Departure date, YYYY-MM-DD")
parser.add_argument('--return-date', type=date.fromisoformat,
                    help="Return date, YYYY-MM-DD. Omit for one-way")
parser.add_argument('--email', required=True)
args = parser.parse_args()


def main():
    """
    Main Function
    """
    try:
        script()
        # Schedule the function to run at 12:00 am and 12:00 pm
        schedule.every().day.at("00:00").do(script)
        schedule.every().day.at("12:00").do(script)
        # Run the scheduled jobs indefinitely
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Notification Service stopped")


def script():
    """
    Caller Function that is scheduled to run periodically
    """
    search = FlightSearch(args.src, args.dest, args.price, args.date.isoformat(),
                          args.return_date and args.return_date.isoformat())
    df = search.search()
    print(f"{datetime.now():%Y-%m-%d %H:%M} {len(df)} fares <= ${args.price}", flush=True)
    if df.empty:
        return
    df.to_csv(f'Results_{datetime.now():%Y%m%d_%H%M%S}.csv', index=False)
    notifier = Notifier(args.email, df, search)
    notifier.send_mail(notifier.create_message())


if __name__ == "__main__":
    main()
