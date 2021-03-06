import sys
import subprocess
from subprocess import Popen, PIPE
import urllib2
import simplejson
import re
from datetime import datetime
from optparse import OptionParser

parser = OptionParser()
usage = "usage: %prog [options] arg1 arg2"
parser = OptionParser(usage=usage)

parser.add_option("-f", "--from",
                  help="date to restrict search from. you can use the form yyyy-mm-dd.",
		  dest="date")

parser.add_option("-d", "--directory", dest="directories",
		  action="append",
                  help="directory to diff.  if not specified, all directories assumped.", metavar="FILE")

(options, args) = parser.parse_args()

if len(args) != 2:
    parser.print_usage()
    print "\targ1 and arg2 are missing\n"
    sys.exit()

srcdir_1 = args[0]
srcdir_2 = args[1]

if options.date is None:
    date="1970-01-01"
else:
    date = options.date

ignore_before_date = datetime.strptime(date, "%Y-%m-%d");

directories = []
if options.directories is None:
    directories.append('/')
else:
    directories = options.directories

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
        if datetime.strptime(result['last_change_time'], '%Y-%m-%dT%H:%M:%SZ') < ignore_before_date:
            return None
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

for i, v in enumerate(directories):
    index = v.find(":")
    path1 = ""
    path2 = ""
    if index == -1:
        path1 = v
        path2 = v
    else:
        path1 = v[:index]
        path2 = v[index+1:]
    print "collecting data about " + path1 + " <--> " + path2
    populateHash(srcdir_1, srcdir_1_hash, path1)
    populateHash(srcdir_2, srcdir_2_hash, path2)

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
"</style>\n" \
"<script>\n" \
"function openAllBugs() {\n" \
"  var bugs = document.getElementsByTagName(\"a\");\n" \
"  for (a in bugs) {\n" \
"    try {\n" \
"      var decor = bugs[a].parentNode.parentNode.style.textDecoration;\n" \
"      if (decor != \"line-through\")\n" \
"        window.open(bugs[a].getAttribute(\"href\"));\n" \
"    } catch(e) {}\n" \
"  }\n" \
"}\n" \
"</script>\n" \
"</head><body>"\
"<h1>Diff Between" + srcdir_1 + " and " + srcdir_2 + "</h1>"\
"<div id=\"container\">\n" \
"<button onClick=\"openAllBugs()\">Open All Bugs</button>\n"
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



