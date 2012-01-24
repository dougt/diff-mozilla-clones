import subprocess
from subprocess import Popen, PIPE
import urllib2
import simplejson
import re

srcdir_1 = "/builds/mozilla-central"
srcdir_2 = "/builds/mozilla-aurora"
directory_of_interest = "mobile/android"

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
        return result['assigned_to']['real_name'], result['summary']
    except urllib2.HTTPError:
        return "Stuart", "I do not have a pony. See bug " + bug

def populateHash(srcdir, hashtable):
    cmd = "hg log " + directory_of_interest
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
populateHash(srcdir_1, srcdir_1_hash)

print "collecting data about " + srcdir_2
populateHash(srcdir_2, srcdir_2_hash)

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
"<h2>Diffing directory: " + directory_of_interest + "</h2>"\
"<div id=\"container\">"

for index in enumerate(bugs_that_have_not_landed):
    info = getBugInfo(index[1])
    html_out += "<div id=\"row\"><div id=\"bugnum\"> <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=" + index[1] + "\">" + index[1] + "</a></div>"
    html_out += "<div id=\"owner\">" + info[0] + "</div>"
    html_out += "<div id=\"summary\">" + info[1] + "</div></div>"

html_out += "</div></body></html>"


fout = open("data.html", "w")
fout.write(html_out)



