import sys
import markdown

from beem import Hive
from beem.account import Account
from beem.comment import Comment

from config import HIVE_NODE

hive = Hive(nodes=HIVE_NODE)

def get_comment_and_replies(authorperm):
    # Connect to the hive blockchain

    # Extract author and permlink from authorperm
    author, permlink = authorperm.split("/")

    return Comment(authorperm, hive=hive)

def lookup_edits(authorperm):
    comment = get_comment_and_replies(authorperm)
    data = {"created": comment.get("created")}
    data["updated"] = comment.get("updated")
    data["author"] = comment.get("author")
    data['permlink'] = comment.get("permlink")
    snap = Account(data["author"], blockchain_instance=hive)
    snap_range = snap.history(start=data["created"], stop=data["updated"], only_ops=['comment'])
    data["edits"] = []  # Add this line to initialize the edits list

    for x in snap_range:
        if x['permlink'] == comment['permlink']:
            edit = {
                "trx_id": x['trx_id'],
                "body": markdown.markdown(x['body'])
            }
            data["edits"].append(edit)
    return data
if __name__ == "__main__":
    authorperm = sys.argv[1]
    print(lookup_edits(authorperm))
