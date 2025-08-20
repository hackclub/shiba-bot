from slack_bolt import App
import os
from dotenv import load_dotenv
from pyairtable import Api

# load local .env (only for local dev)
load_dotenv()

app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"]
)

api = Api(os.environ['AIRTABLE_API_KEY'])

usersTable = api.table('appg245A41MWc6Rej', 'tblfD2WCyqAIOBBbz')
referralTable = api.table('appg245A41MWc6Rej', 'tblSnv5RdfJvzGO9g')



@app.command('/shiba-share-code')
def shiba_share_code(ack, respond, command):
    ack()

    userid = command['user_id']
    formula = f"{{slack id}}='{userid}'"
    records = usersTable.all(formula=formula)
    if len(records) <= 0:
        respond(f"your slack account is not linked to shiba!")
        return

    yourShareCode = records[0]['fields']['ReferralCode']

    respond(f"your shiba share code is: shiba.hackclub.com?sentby={yourShareCode}\nsend this to a friend and get SSS!")



@app.command("/shiba-share-leaderboard")
def shiba_share_leaderboard(ack, respond, command):
    ack()

    userid = command["user_id"]
    formula = f"{{slack id}}='{userid}'"
    records = usersTable.all(formula=formula)

    if len(records) <= 0:
        respond(f"your slack account is not linked to shiba!")
        return

    yourReferrals = records[0]['fields']['ReferralNumber']


    topReferrals = usersTable.all(view="TopReferrals")



    print(topReferrals)

    final_message = ":sss-shiba-fire:*SHIBA SHARE LEADERBOARD!*:sss-shiba-fire:\n"

    youAreInTop = False

    for i in range(10):
        if i >= len(topReferrals):
            break

        record = topReferrals[i]['fields']

        if record['slack id'] == userid:
            youAreInTop = True
        final_message += f"{str(i + 1)}. <@{record['slack id']}> with {record['ReferralNumber']} {'shiba shares' if record['ReferralNumber'] != 1 else 'shiba share'}\n"

    if not youAreInTop:
        final_message += f"\n_(you have {yourReferrals} {'shiba shares' if yourReferrals != 1 else 'shiba share'})_"



    respond(final_message)

if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
