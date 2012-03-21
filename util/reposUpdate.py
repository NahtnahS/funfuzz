#!/usr/bin/env python
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# To update specified repositories to default tip and provide a short list of latest checkins.
#
# Assumes that the repositories are located in ../../* or ../../trees/*, and assumes the Valgrind
# SVN directory is located only in ../../* if repositories are in ../../trees/*.

import os
import subprocess
import sys
from subprocesses import dateStr, timeSubprocess

repos = []
# Add your repository here.
repos.append('fuzzing')
# Spidermonkey friends
repos.append('ionmonkey')
#repos.append('jaegermonkey')
#repos.append('larch')
# Official repository branches
repos.append('mozilla-inbound')
repos.append('mozilla-central')
repos.append('comm-central')
repos.append('mozilla-aurora')
repos.append('mozilla-beta')
repos.append('mozilla-esr10')
# Others
repos.append('v8')
# Miscellaneous tools
repos.append('buildbot-configs')
repos.append('mozmill-tests')
repos.append('valgrind')
# Soon-to-be obsolete
repos.append('mozilla-1.9.2')
repos.append('comm-1.9.2')

def typeOfRepo(r):
    '''
    Returns the type of repository.
    '''
    repoList = []
    repoList.append('.hg')
    repoList.append('.svn')
    repoList.append('.git')
    for rtype in repoList:
        try:
            os.mkdir(os.path.join(r, rtype))
            os.rmdir(os.path.join(r, rtype))
        except OSError, e:
            if 'File exists' in e or 'Cannot create a file when that file already exists' in e:
                return rtype[1:]
    raise Exception('Type of repository located at ' + r + ' cannot be determined.')

def main():
    print dateStr()
    cwdParent = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    cwdParentParent = os.path.abspath(os.path.join(cwdParent, os.pardir))

    for repo in repos:
        repoLocation = os.path.join(cwdParentParent, repo)
        if not (os.path.exists(repoLocation)):
            repoLocation = os.path.join(cwdParentParent, 'trees', repo)

        if not (os.path.exists(repoLocation)):
            print repo, "repository does not exist at %s or at %s\n" % \
                (os.path.join(cwdParentParent, repo), \
                os.path.join(cwdParentParent, 'trees', repo))
            continue

        print 'Now in %s repository.' % repo

        repoType = typeOfRepo(repoLocation)
        assert repoType != None

        count = 0
        # Try pulling 5 times per repository.
        while count < 5:
            if repoType == 'svn':
                # Valgrind SVN is located in svn://svn.valgrind.org/valgrind/trunk
                # V8 SVN is located in http://v8.googlecode.com/svn/branches/bleeding_edge/
                svnCoStdout, retval = timeSubprocess(
                    [repoType, 'update'], cwd=os.path.abspath(os.path.join(repoLocation)), vb=True)
            elif repoType == 'hg':
                hgPullRebaseStdout, retval = timeSubprocess(
                    ['hg', 'pull', '--rebase'], cwd=repoLocation, vb=True)
            else:
                assert repoType == 'git'
                gitStdout, retval = timeSubprocess(
                    ['git', 'pull'], cwd=repoLocation, vb=True)

            if ((retval == 255) or (retval == -1)) and \
                'hg pull: option --rebase not recognized' in hgPullRebaseStdout:
                # Exit if the "rebase =" line is absent from the [Extensions] section of ~/.hgrc
                print 'Please enable the rebase extension in your hgrc file!'
                print 'Exiting...'
                sys.exit(1)
            # 255 is the return code for abnormal hg exit on POSIX.
            # -1 is the return code for abnormal hg exit on Windows.
            # Not sure about SVN.
            if (retval != 255) and (retval != -1):
                break

            count += 1
            # If this script tries 5 times and fails, exit with status 1.
            if count == 5:
                print 'Script has tried to pull 5 times and has failed every time.'
                print 'Exiting...'
                sys.exit(1)

        if repoType == 'hg' and repo != 'valgrind':
            timeSubprocess(['hg', 'update', 'default'], cwd=repoLocation, vb=True)
            timeSubprocess(['hg', 'log', '-l', '5'], cwd=repoLocation, vb=True)

        if 'comm-' in repo:
            timeSubprocess(['python', 'client.py', 'checkout'], cwd=repoLocation, vb=True)

    print dateStr()

# Run main when run as a script, this line means it will not be run as a module.
if __name__ == '__main__':
    main()
