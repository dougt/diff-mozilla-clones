import subprocess
from subprocess import Popen, PIPE
import urllib2
import simplejson
import re

srcdir_1 = "./mozilla-central"
srcdir_2 = "./mozilla-aurora"
directory_of_interest_1a = "mobile/android"
directory_of_interest_2a = "mobile/android"
directory_of_interest_1b = "widget/src/android"
directory_of_interest_2b = "widget/android"

srcdir_1_hash = {}
srcdir_2_hash = {}

def getBugInfo(bug):
    try:
        req = urllib2.Request("https://api-dev.bugzilla.mozilla.org/latest/bug/" + bug,
                              None,
                              {'user-agent':'dougt/rocks', 'Content-Type': 'application/json'})
        opener = urllib2.build_opener()
        f = opener.open(req)
        result = simplejson.load(f)
        not11 = "false"
        try:
            if "not-fennec-11" in result['whiteboard']:
                not11 = "true"
        except KeyError:
            not11 = "false"
        return result['assigned_to']['real_name'], result['summary'], not11
    except urllib2.HTTPError:
        return "Stuart", "I do not have a pony. See bug " + bug, "true"

def populateHash(srcdir, hashtable, dir_to_diff):
    cmd = "hg log " + dir_to_diff
    p = Popen(cmd, cwd=srcdir, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    matches = re.findall(r'(summary:\s+.Bug )(\d+)', stdout)
    for match in matches:
        # do something with each found email string
        hashtable[match[1]] = '1'

print "updating source directories:"
subprocess.call(["hg", "pull", "-u"], cwd=srcdir_1)
subprocess.call(["hg", "pull", "-u"], cwd=srcdir_2)

print "collecting data about " + srcdir_1
populateHash(srcdir_1, srcdir_1_hash, directory_of_interest_1a)
populateHash(srcdir_1, srcdir_1_hash, directory_of_interest_1b)

print "collecting data about " + srcdir_2
populateHash(srcdir_2, srcdir_2_hash, directory_of_interest_2a)
populateHash(srcdir_2, srcdir_2_hash, directory_of_interest_2b)

print "checking to see what hasn't landed in " + srcdir_2 

bugs_that_have_not_landed = [];
for index in enumerate(srcdir_1_hash):
    #check to see if it is also in srcdir_2_hash, if not print it.
    if (srcdir_2_hash.has_key(index[1]) == False):
        bugs_that_have_not_landed.append(index[1])



html_out =\
\
"<html><head><title>Diff Between" + srcdir_1 + " and " + srcdir_2 + "</title><style>"\
"#container {width: 100%; display: table;}"\
"#row { display: table-row;}"\
"#bugnum { width: 15%; display: table-cell;}"\
"#owner { width: 25%; display: table-cell;}"\
"#summary { width: 60%; display: table-cell;}"\
"</style></head><body>"\
"<h1>Diff Between" + srcdir_1 + " and " + srcdir_2 + "</h1>"\
"<div id=\"container\">\n"

for index in enumerate(bugs_that_have_not_landed):
    info = getBugInfo(index[1])
    if info is None:
        continue
    html_out += "<div id=\"row\" "
    if info[2] is "true":
        html_out += "style=\"text-decoration: line-through;\""
    html_out += ">\n"
    html_out += "\t<span id=\"bugnum\"> <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=" + index[1] + "\">" + index[1] + "</a></span>"
    html_out += "<span id=\"owner\">" + info[0] + "</span>"
    html_out += "<span id=\"summary\">" + info[1] + "</span>\n"
    html_out += "</div>\n"

html_out += "</div></body></html>"


fout = open("data.html", "w")
fout.write(html_out.encode('UTF-8'))



