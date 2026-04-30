import re
import sys
import os
import markdown
from beem import Hive
from beem.account import Account
from beem.comment import Comment
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load config
load_dotenv()
HIVE_NODE = os.getenv("HIVE_NODE")

hive = Hive(nodes=HIVE_NODE)

IMAGE_PROXY = "https://images.hive.blog/400x400/"


def strip(text):
    text["body"] = re.sub(
        r"(^https?:[^)''\"]+\.(?:jpg|jpeg|gif|png))",
        r"![](\1)",
        text["body"],
    )

    text["body"] = markdown.markdown(
        text["body"],
        extensions=[
            "extra",
            "nl2br",
            "codehilite",
        ],
    )
    text["body"] = re.sub(
        r"<img\b(?=\s)(?=(?:[^>=]|='[^']*'|=\"[^\"]*\"|=[^'\"][^\s>]*)*?\ssrc=['\"]([^\"]*)['\"]?)(?:[^>=]|='[^']*'|=\"[^\"]*\"|=[^'\"\s]*)*\"\s?\/?>",
        rf"<img src={IMAGE_PROXY}\1>",
        text["body"],
    )

    return text


def get_comment_and_replies(authorperm):
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
    data["edits"] = []

    for x in snap_range:
        if x["permlink"] == comment["permlink"]:
            edit = {"trx_id": x["trx_id"], "body": x["body"]}
            data["edits"].append(edit)

    for x in data["edits"]:
        soup = BeautifulSoup(x["body"], "html.parser")
        x["body"] = soup.get_text()
        if x["body"].startswith("@@"):
            x["body"] = f"```diff\n{x['body']}\n```"
        strip(x)
    return data


if __name__ == "__main__":
    if len(sys.argv) > 1:
        authorperm = sys.argv[1]
        print(lookup_edits(authorperm))
