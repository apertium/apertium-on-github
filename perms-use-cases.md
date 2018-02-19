## Proposed GitHub Permissions Model Use Cases

Note: 'organization owner', 'organization member', 'repository owner',
'repository admin', 'repository write', 'outside collaborator', and 'repository
read' are technical terms regarding various GitHub permissions. See the
[README][1] for a description of what they mean.

Let me introduce you to:
 * Pam, a member of the PMC and a organization owner of `apertium`
 * Mai, a repository admin of `apertium/apertium-zzz` and a organization member
of `apertium`
 * Con, a contributor with repository write access to `apertium/apertium-zzz`
and a organization member of `apertium`
 * Nub, a person who is not currently involved with Apertium but wishes to be

Listed in that order, if one person can do a certain action, then all people
above that person can also do that action, for the scenarios below.

### How Nub begins to contribute

Note: for Apertium, step 1 below is often skipped, but I'm including it here as
a good practice.

#### Step 1

1. Nub forks `apertium/apertium-zzz` to create `nub/apertium-zzz` and makes some
commits to `nub/apertium-zzz`. So far, Apertium knows nothing about Nub or his
new code.
1. Nub opens a pull request from `nub/apertium-zzz` to `apertium/apertium-zzz`,
essentially saying "please review my changes and add them to
`apertium/apertium-zzz`". Depending on their notification settings, Con, Mai,
and Pam receive emails about this pull request.
1. Con takes a look at Nub's changes. She thinks they are good, but she leaves a
few comments about what Nub can improve. Nub tries to fix the comments by making
more commits to `nub/apertium-zzz`.
1. Con is satisfied with his changes and merges the pull request. Now
`apertium/apertium-zzz` has the same code as `nub/apertium-zzz`.

At the end of this sequence of events, Nub still has the same permissions he had
at the beginning.

#### Step 2

Nub has contributed a number of pull requests and wants to be able to commit
further code without necessarily having it reviewed by Con or Mai.

1. Nub emails Mai or the `apertium-stuff` mailing list.
1. Mai thinks it's reasonable, and makes Nub an outside collaborator for
`apertium/apertium-zzz` with repository write access.
1. Nub starts making commits directly to `apertium/apertium-zzz`.

Now Nub has gained repository write access to `apertium/apertium-zzz`.

#### Step 3

Nub is still not a organization member of `apertium`.

1. Nub emails `apertium-stuff` about wanting to be an organization member.
1. Two existing organization members, including Con, reply to that email
seconding his request.
1. Pam notes that the two conditions required to become a member as per
Apertium's [by-laws][2] are satisfied: Nub has contributed code in the past, and he
has two existing members seconding him. Pam makes Nub an organization member of
`apertium`.

As an organization member, Nub can:
 * know who the other members are
 * view, create, talk to, and lead [teams][3]
 * use [project boards][4] to plan projects

Nub's write access to repositories has not changed and so far, he only has write
access to `apertium/apertium-zzz`. For other repositories, he can either follow
steps 1 and 2 again, or Pam can directly give him write access.


### How `apertium/apertium-zzz` is released

1. Con creates a [draft release][5] in `apertium/apertium-zzz` and emails Pam or
`apertium-stuff` about the planned release.
1. Pam replies, saying that the release is approved.
1. Con publishes the draft release.

Now the release will show up publicly on the `apertium/apertium-zzz` releases
page and Con will be able (through the API) to view download counts for the
release.


### How `apertium/apertium-zzz` is managed

Here, management includes setting up continuous integration, webhooks that
trigger automatic actions on commits/pull requests/issues/..., deploy keys,
deleting the repository, shifting from staging to trunk, etc.

1. Nub, Con, Mai, and other contributors discuss what they want to do via email
or the issue tracker.
1. Mai changes settings accordingly.

Note that this process does not involve Pam at all.


  [1]: https://github.com/sushain97/apertium-on-github/blob/master/README.md
  [2]: http://wiki.apertium.org/wiki/By-laws
  [3]: https://help.github.com/articles/about-teams/
  [4]: https://help.github.com/articles/about-project-boards/
  [5]: https://help.github.com/articles/about-releases/
