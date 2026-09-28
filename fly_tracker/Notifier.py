from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import smtplib
import pandas as pd

class Notifier:
    """
    Notifier class that sends email notification with the scraped data
    """

    def __init__(self, email:str, data:pd.DataFrame, scraper):
        # Define the email sender and recipient
        # Gmail address + app password (https://myaccount.google.com/apppasswords)
        self.sender = os.environ.get("FLY_TRACKER_SENDER", "")
        self.password = os.environ.get("FLY_TRACKER_APP_PASSWORD", "")
        self.recipient = email
        self.df = data
        self.src = scraper.src
        self.dest = scraper.dest
        self.date = scraper.date
        return_date = getattr(scraper, 'return_date', None)
        self.trip = f"{self.date} (returning {return_date})" if return_date else self.date
        # Define the HTML template
        # pylint: disable=R0801
        self.html_template = '''
        <html>
        <head>
        <style>
            /* Define table styles */
            table {{
            font-family: arial, sans-serif;
            border-collapse: collapse;
            width: 100%;
            }}

            td, th {{
            border: 1px solid #dddddd;
            text-align: left;
            padding: 8px;
            }}

            tr:nth-child(even) {{
            background-color: #dddddd;
            }}
        </style>
        </head>
        <body>

        <h2>Flight Data</h2>

        {table}

        </body>
        </html>
        '''

    def send_mail(self,msg:MIMEMultipart):
        """
        Create email body and send scraped flight fare data

        Args:
            msg (MIMEMultipart): Email to be sent
        """

        # Send the message using the SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(self.sender, self.password)
        text = msg.as_string()
        server.sendmail(self.sender, self.recipient, text)
        server.quit()
    def create_message(self):
        """
        Create a message object and set the subject and body

        Returns:
            MIMEMultipart: Email Content
        """
        msg = MIMEMultipart()
        msg['From'] = self.sender
        msg['To'] = self.recipient
        msg['Subject'] = f"FLY_TRACKER: {self.src} to {self.dest} on {self.trip} fares"
        body = f"This is an email notification from fly-tracker with fares for your {self.src} to {self.dest} route on {self.trip}"  # noqa: E501
        msg.attach(MIMEText(body, 'plain'))

        # Convert the dataframe to an HTML table
        flight_data_html = self.df.to_html(index=False, classes='table table-striped')

        # Insert the table into the HTML template
        html = self.html_template.format(table=flight_data_html)

        body = MIMEText(html, 'html')
        msg.attach(body)
        return msg
