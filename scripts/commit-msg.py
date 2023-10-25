#!/usr/bin/env python

import re
import subprocess
import sys

OK_C = "\033[92m"
WARN_C = "\033[93m"
FAIL_C = "\033[91m"
END_C = "\033[0m"

JIRA_REGEX = "(SPII|PCRM|NEMS|KF|IGWAY|NRL|APM|APMSPII|SPY3|SPINECLI)\-(\d+)"  # Example match: SPII-12345
FEATURE_REGEX = (
    "feature\/\w+\-(\w+\-\d+)\-"  # Example match: feature/das-SPII-12345-foo
)
OLD_FEATURE_REGEX = "feature\/\w+\-(\d+)\-"  # Example match: feature/das-12345-foo
sys.stdin = open("/dev/tty")  # Ensure that input can be taken by hook
MSG_FILE = sys.argv[1]  # commit-msg hook provides file name as first arg


def appendToCommitMessage(jiraId):
    print("Appended {0} to commit message.".format(jiraId))
    with open(MSG_FILE, "a") as f:
        f.write("{0}".format(jiraId))


def prependToCommitMessage(jiraId):
    print("Prepended {} to commit message.".format(jiraId))
    with open(MSG_FILE, "r") as f:
        text = f.read()
        text = "{} {}".format(jiraId, text)
        with open(MSG_FILE, "w") as f:
            f.write(text)


# Check if JIRA ID already exists in commit message
print("I am doing something")
with open(MSG_FILE, "r") as f:
    msg = ""
    for line in f:
        if not line.startswith("#"):
            msg += line.rstrip()
    if msg == "":
        # No commit message let Git fail the commot
        sys.exit(0)

    commitMatch = re.search(JIRA_REGEX, msg)
    if commitMatch:
        print(
            "JIRA {0}{1}-{2}{3} referenced by commit message.".format(
                OK_C, commitMatch.group(1), commitMatch.group(2), END_C
            )
        )
        sys.exit(0)

print(WARN_C + "No JIRA ID referenced by commit message." + END_C)

# Check if KEY-n+ can be used from branch name
branch = subprocess.check_output("git rev-parse --abbrev-ref HEAD", shell=True)
branchMatch = re.search(FEATURE_REGEX, str(branch))
if branchMatch:
    response = input(
        "Use {0}{1}{2} from branch name? (y/n) ".format(
            OK_C, branchMatch.group(1), END_C
        )
    )
    if response.strip().lower().startswith("y"):
        prependToCommitMessage(branchMatch.group(1))
        sys.exit(0)
oldBranchMatch = re.search(OLD_FEATURE_REGEX, str(branch))
if oldBranchMatch:
    jiraId = "SPII-{}".format(oldBranchMatch.group(1))
    response = input(
        "Use {0}{1}{2} from branch name? (y/n) ".format(OK_C, jiraId, END_C)
    )
    if response.strip().lower().startswith("y"):
        prependToCommitMessage(jiraId)
        sys.exit(0)

# All else fails ask what they want to use
jiraId = input("Please enter the JIRA ID (for example SPII-1234 or NEMS-123): ")
if not re.search(JIRA_REGEX, jiraId):
    print(FAIL_C + "Did not provide valid JIRA ID. Commit Aborted." + END_C)
    sys.exit(1)
else:
    prependToCommitMessage(jiraId)
    sys.exit(0)
