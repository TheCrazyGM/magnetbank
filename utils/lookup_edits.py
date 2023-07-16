import re
import sys
import markdown
import lxml.html

from beem import Hive
from beem.account import Account
from beem.comment import Comment
from flask import Markup
from config import HIVE_NODE

hive = Hive(nodes=HIVE_NODE)


IMAGE_PROXY = "https://images.hive.blog/400x400/"


def strip(text):
    def replacer(match):
        if match.group(1):
            return rf"![]({match.group(1)}) >"
        elif match.group(2):
            return "<h3>"
        elif match.group(3):
            return rf"<img src={IMAGE_PROXY}{match.group(3)} >"
        else:
            return match.group(0)

    pattern = re.compile(
        r"(^https?:[^)''\"]+\.(?:jpg|jpeg|gif|png))|(<h1>|<h2>)|<img\b(?=\s)(?=(?:[^>=]|='[^']*'|=\"[^\"]*\"|=[^'\"][^\s>]*)*?\ssrc=['\"]([^\"]*)['\"]?)(?:[^>=]|='[^']*'|=\"[^\"]*\"|= '\"\s]*)*\"\s?\/?>"
    )
    text["body"] = re.sub(pattern, replacer, text["body"])
    text["body"] = markdown.markdown(
        text["body"],
        extensions=[
            "extra",
            "nl2br",
            "codehilite",
        ],
    )
    text["body"] = Markup(text["body"])
    return text


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
    data["permlink"] = comment.get("permlink")
    snap = Account(data["author"], blockchain_instance=hive)
    snap_range = snap.history(
        start=data["created"], stop=data["updated"], only_ops=["comment"]
    )
    data["edits"] = []  # Add this line to initialize the edits list

    for x in snap_range:
        if x["permlink"] == comment["permlink"]:
            edit = {"trx_id": x["trx_id"], "body": x["body"]}
            data["edits"].append(edit)

    for x in data["edits"]:
        x['body'] = lxml.html.fromstring(x["body"]).text_content()
        if x['body'].startswith("@@"):
            x['body'] =(f"```diff\n {x['body']} \n```")
        strip(x)
    return data


if __name__ == "__main__":
    authorperm = sys.argv[1]
    print(lookup_edits(authorperm))
