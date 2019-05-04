#!/usr/bin/env python
# vim: ft=python
""" Get tag with fewest commits from path of given branch

Usage:

    git-closest-tag [commit-ish]

To get closest tag to current HEAD

    git-closest-tag

To get closest tag to origin/master

    git-closest-tag origin/master

What does "closest" mean, in "closest tag"?

Imagine the following git history::

    A->B->C->D->E->F (HEAD)
           \     \
            \     X->Y->Z (v0.2)
             P->Q (v0.1)

Imagine the developer tag'ed Z as v0.2 on Monday, and then tag'ed Q as v0.1 on
Tuesday. v0.1 is the more recent, but v0.2 is closer in development history to
HEAD, in the sense that the path it is on starts at a point closer to HEAD.

We may want get the tag that is closer in development history. We can find that
by using ``git log v0.2..HEAD`` etc for each tag. This gives you the number of
commits on HEAD since the path ending at v0.2 diverged from the path followed by
HEAD.

``git describe`` does something slightly different, in that it tracks back from
(e.g.) HEAD to find the first tag that is on a path back in the history from
HEAD. In git terms, ``git describe`` looks for tags that are "reachable" from
HEAD.  It will therefore not find tags like v0.2 that are not on the path back
from HEAD, but a path that diverged from there.

Source:
    @matthew-brett
    https://github.com/MacPython/terryfy/blob/master/git-closest-tag
    https://stackoverflow.com/questions/1404796/how-to-get-the-latest-tag-name-in-current-branch-in-git
"""
# Requires at least Python 2.7
from __future__ import print_function

import sys
from subprocess import check_output


def backtick(cmd):
    """ Get command output as stripped string """
    output = check_output(cmd)
    return output.decode('latin1').strip()


def tagged_commit(tag):
    return backtick(['git', 'rev-parse', '--verify', tag + '^{commit}'])

def find_nearest_tag_from(target):
    # 5.6b2, 55, e1129da
    tag, distance, commit = backtick(['git',
        'describe', '--tags','--long', target]).rsplit('-',2)
    return commit

def get_ten_tags(target):
    #backtick(['git', 'for-each-ref', 'refs/tags', '--sort=-taggerdate',
    #    "--format='%(objectname),%(refname)'", '--count=10'])
    tags = backtick(['git', 'for-each-ref', 'refs/tags', '--sort=-taggerdate',
        "--format='%(refname:lstrip=2)'", '--count=5', target])
    #tags = [x.strip("'") for x in tags.split('\n')]
    return tags
'''
463404b247f8ee94cd017a6e849a6338b35282b7,refs/tags/v5.9'
'7f8697c8e7e4af6e11314b1cc3734c214ab7b91c,refs/tags/5.9.b2'
'481d8aae8b0b34b6c51bef905ed13d82270cbd55,refs/tags/5.9-b1'
'eb06fb0c3c4e81f3d946402c3c22fe974eca90a2,refs/tags/5.8.1-b1-2'
'e13ab44ceb1bf82f227d1cb29efedd8936c7f3b4,refs/tags/5.8.1-b1'
'6e31d4b3c501d5e03796fcc21ddd7c971f535b75,refs/tags/5.8'
'380f8fccb8228ecd7d23522c3c723719947f8965,refs/tags/5.8-b2'
'f095e9ead18b272cf3e7b67abeab0def28de625d,refs/tags/5.8-b1'
'246c61afdc1204347052d999beff248b15ef428c,refs/tags/5.7.3'
'46ac1692ac0136cb52570e37c385a9f01d6573c8,refs/tags/5.7.2'
'''

def n_commits_exclude_include(exclude, include):
    commit_range = '{}..{}'.format(exclude, include)
    commits = backtick(['git', 'log', '--oneline', commit_range])
    return 0 if commits == '' else len(commits.split('\n'))


def main():
    # Get commit-ish from passed command arguments, HEAD is default
    try:
        target_ref = sys.argv[1]
    except IndexError:
        target_ref = 'HEAD'
    # SHA1 for target reference
    target_commit = tagged_commit(target_ref)

    #mhw/
    end_target_ref = find_nearest_tag_from(target_ref)
    #tag_lines = backtick(['git', 'tag'])
    tag_lines = get_ten_tags(target_ref)
    #/mhw

    if tag_lines == '':
        raise RuntimeError("No tags to compare")
    tags = [tag.strip("'") for tag in tag_lines.split('\n')]
    tags_info = {}
    min_after = float('inf')
    for tag in tags:
        tag_commit = tagged_commit(tag)
        # The commits along target branch since the root of the branch that the
        # tag is on
        merge_base = backtick(['git', 'merge-base', tag, target_commit])
        tags_info[tag] = (tag_commit, merge_base)
        n_after = n_commits_exclude_include(merge_base, target_commit)
        if n_after < min_after:
            min_after = n_after
            candidates = [tag]
        elif n_after == min_after:
            candidates.append(tag)
    if len(candidates) == 0:
        raise RuntimeError('Could not find any useful tags')
    if len(candidates) == 1:
        print(candidates[0])
        return
    # More than one candidate with same post-tag-on-target length
    max_post_common = -1
    for tag in candidates:
        tag_commit, merge_base = tags_info[tag]
        n_after = n_commits_exclude_include(merge_base, tag_commit)
        if n_after > max_post_common:
            closest_tag = tag
            max_post_common = n_after
    print(closest_tag)


if __name__ == '__main__':
    main()
