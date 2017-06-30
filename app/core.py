import re
import random
from app import chargers, macbooks, thunderbolts, lost, found, slack_client, slack_handles


def extract_id_from_slack_handle(slack_handle):
    '''
    Remove slack formatting of handle eg. <@U328FG73> => U328FG73
    '''
    match = re.findall("<@(.*)>", slack_handle)
    return match[0] if match else slack_handle


def get_equipment(equipment_id, equipment_type):
    '''
    Get equipment from database by id
    '''
    equipment_types = {
        "macbook": macbooks,
        "charger": chargers,
        "thunderbolt": thunderbolts
    }
    collection = equipment_types[equipment_type]
    return collection.find({"equipment_id": equipment_id})


def get_equipment_by_slack_id(slack_id, equipment_type):
    '''
    Get equipment by slack_id
    '''
    equipment = None
    equipment_types = {
        "macbook": macbooks,
        "charger": chargers,
        "thunderbolt": thunderbolts
    }

    collection = equipment_types[equipment_type]
    slack = slack_handles.find_one({"slack_id": slack_id})
    if slack is not None:
        email = slack["email"]
        equipment = collection.find({"owner_email": email})
    return equipment


def add_lost_equipment(owner, equipment_lost):
    '''
    Add a lost item to the database
    '''
    if not lost.find_one({"equipment": equipment_lost}):
        slack_profile = slack_client.api_call("users.info",
                                              user=owner)['user']["profile"]

        lost_item = {
            "equipment": equipment_lost,
            "owner": owner,
            "email": slack_profile["email"],
            "name": '{} {}'.format(slack_profile["first_name"],
                                   slack_profile["last_name"])
        }
        lost.insert_one(lost_item)
        return True
    return False


def add_found_equipment(submitter, equipment_found):
    '''
    Add a found item to the database
    '''
    if not found.find_one({"equipment": equipment_found}):
        slack_profile = slack_client.api_call("users.info",
                                              user=submitter)['user']["profile"]

        found_item = {
            "equipment": equipment_found,
            "submitter": submitter,
            "email": slack_profile["email"],
            "name": '{} {}'.format(slack_profile["first_name"],
                                   slack_profile["last_name"])
        }
        found.insert_one(found_item)
        return True
    return False


def remove_from_lost(equipment):
    lost.delete_one({"equipment": equipment})


def remove_from_found(equipment):
    found.delete_one({"equipment": equipment})


def search_found_equipment(equipment):
    return found.find_one({"equipment": equipment})


def search_lost_equipment(equipment):
    return lost.find_one({"equipment": equipment})


def notify_user_equipment_found(submitter, owner, equipment_type):
    message = "The user <@{}> found your `{}`".format(
        submitter, equipment_type)
    slack_client.api_call("chat.postMessage", text=message, channel=owner)


def generate_random_hex_color():
    '''
    Generate random hex color
    '''
    r = lambda: random.randint(0, 255)
    return ('#%02X%02X%02X' % (r(), r(), r()))


def build_search_reply_atachment(equipment, category):
    '''
    Returns a slack attachment to show a result
    '''
    return {
        "text": "{}'s {}".format(equipment["owner_name"], category),
        "fallback": "Equipment ID - {} | Owner - {}".format(equipment["equipment_id"], equipment["owner_name"]),
        "color": generate_random_hex_color(),
        "fields": [{
            "title": "Equipment ID",
            "value": "{}".format(equipment["equipment_id"]),
            "short": "true"
        },
            {
            "title": "Owner",
            "value": "{}".format(equipment["owner_name"]),
            "short": "true"
        }
        ]
    }


def get_help_message():
    return [
        {
            "text": "Sakabot helps you search, find or report a lost item "
            "whether it be your macbook, thunderbolt or charger.\n *USAGE*",
            "color": generate_random_hex_color(),
            "mrkdwn_in": ["fields", "text"],
            "fields": [
                {
                    "title": "Searching for an item's owner",
                    "value": "To search for an item's owner send "
                    "`find <charger|mac|thunderbolt|tb> <item_id>` "
                    "to _@sakabot_.\n eg. `find charger 41`"
                },
                {
                    "title": "Check what items someone owns",
                    "value": "To check what item someone owns "
                    "`find <@mention|my> <charger|mac|thunderbolt>` "
                    "to _@sakabot_.\n eg. `find my charger` or `find @ianoti tb`"
                },
                {
                    "title": "Reporting that you've lost an item",
                    "value": "When you lose an item, there's a chance that "
                    "somebody has found it and submitted it to Sakabot. "
                    "In that case we'll tell you who found it, otherwise, "
                    "we'll slack you in case anyone reports they found it. To "
                    "report an item as lost send `lost <charger|mac|thunderbolt|tb> <item_id>` to _@sakabot._"
                    "\n eg. `lost thunderbolt 33`"
                },
                {
                    "title": "Submit a found item",
                    "value": "When you find a lost item you can report that "
                    "you found it and in case a user had reported it lost, "
                    "we'll slack them immediately telling them you found it. "
                    "To report that you found an item send `found <charger|mac|thunderbolt|tb> <item_id>` to _@sakabot_"
                    "\n eg. `found mac 67`"
                }
            ],
        }
    ]


loading_messages = [
    "We're testing your patience.",
    "A few bits tried to escape, we're catching them...",
    "It's still faster than slacking OPs :stuck_out_tongue_closed_eyes:",
    "Loading humorous message ... Please Wait",
    "Firing up the transmogrification device...",
    "Time is an illusion. Loading time doubly so.",
    "Slacking OPs for the information, this could take a while...",
    "Loading completed. Press F13 to continue.",
    "Oh boy, more work! :face_with_rolling_eyes:..."
]
