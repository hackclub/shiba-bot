from slack_bolt import App
import os
from dotenv import load_dotenv
from pyairtable import Api
from datetime import datetime
import uuid
import random
import string


load_dotenv()

app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"]
)

api = Api(os.environ['AIRTABLE_API_KEY'])

usersTable = api.table('appg245A41MWc6Rej', 'tblfD2WCyqAIOBBbz')
referralTable = api.table('appg245A41MWc6Rej', 'tblSnv5RdfJvzGO9g')
huddleLogTable = api.table('appg245A41MWc6Rej', 'tblLWNYMJYoJwC9hq')



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


user_huddle_times = {}

# helper to generate random HuddleLogID
def generate_huddle_log_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# helper to get user email from Slack
def get_user_email(user_id):
    try:
        user_info = app.client.users_info(user=user_id)
        return user_info['user']['profile']['email']
    except Exception as e:
        print(f"Error getting user email for {user_id}: {e}")
        return None

# helper to calculate total duration per user (seconds)
def get_total_time(user_id):
    sessions = user_huddle_times.get(user_id, [])
    total_seconds = 0
    for s in sessions:
        join = s.get("join")
        leave = s.get("leave")
        if join:
            if leave:
                total_seconds += (leave - join).total_seconds()
            else:
                # still in huddle, count until now
                total_seconds += (datetime.now() - join).total_seconds()
    return total_seconds

# helper to calculate session duration in hours
def get_session_duration_hours(session):
    join = session.get("join")
    leave = session.get("leave")
    if join and leave:
        duration_seconds = (leave - join).total_seconds()
        return duration_seconds / 3600  # convert to hours
    return 0


@app.event("user_huddle_changed")
def handle_huddle_change(event, say):

    user_field = event.get("user")
    user_id = user_field.get("id")
    user_real_name = user_field.get("real_name")



    in_huddle = event.get("user").get("profile").get("huddle_state") == "in_a_huddle"  # True if joined, False if left
    huddle_id = event.get("user").get("profile").get("huddle_state_call_id")  # optional filter if you want

    ts = datetime.now()

    # optional: only track a specific huddle
    # if huddle_id != "YOUR_TEST_HUDDLE_ID":
    #     return



    if user_id not in user_huddle_times:
        user_huddle_times[user_id] = []

    if in_huddle:
        # user joined
        user_huddle_times[user_id].append({"join": ts, "huddle_id": huddle_id})
        print(f"{user_real_name} joined huddle at {ts} for {huddle_id}")
    else:
        # user left: find last session without leave
        sessions = user_huddle_times[user_id]
        for s in reversed(sessions):
            if s.get("leave") is None:
                s["leave"] = ts
                print(f"{user_real_name} left huddle at {ts} for {s['huddle_id']}")
                
                # Add to huddleLogTable in Airtable
                try:
                    # Generate random HuddleLogID
                    huddle_log_id = generate_huddle_log_id()
                    
                    # Calculate duration in hours
                    duration_hours = get_session_duration_hours(s)
                    
                    # Create record for huddleLogTable
                    huddle_log_record = {
                        "HuddleLogID": huddle_log_id,
                        "SlackID": user_id,  # Direct Slack ID instead of linking
                        "HuddleID": s["huddle_id"],  # The actual huddle ID from Slack
                        "HuddleJoinTime": s["join"].isoformat(),
                        "HuddleHours": duration_hours
                    }
                    
                    # Add to Airtable
                    huddleLogTable.create(huddle_log_record)
                    print(f"Added huddle log to Airtable: {huddle_log_id} for {user_real_name} ({duration_hours:.2f} hours)")
                except Exception as e:
                    print(f"Error adding huddle log to Airtable: {e}")
                
                break

    # example: print current total time
    total_time_sec = get_total_time(user_id)
    print(f"Total time for {user_real_name}: {total_time_sec/60:.1f} min")


if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
