## Proposed GitHub Permissions Model Use Cases

Note: 'organization owner', 'organization member', 'repository owner',
'repository admin', 'repository write', 'outside collaborator', and 'repository
read' are technical terms regarding various GitHub permissions. See the
[README][1] for a description of what they mean.

Let me introduce you to:
 * Fran, a member of the PMC and a organization owner of `apertium`
 * Ilnar, a repository admin of `apertium/apertium-tur` and a organization member
of `apertium`
 * Sushain, a contributor with repository write access to `apertium/apertium-tur`
and a organization member of `apertium`
 * Shardul, a person who is not currently involved with Apertium but wishes to be

Listed in that order, if one person can do a certain action, then all people
above that person can also do that action, for the scenarios below.

### How Shardul begins to contribute

Note: for Apertium, step 1 below is often skipped, but I'm including it here as
a good practice.

#### Step 1

1. Shardul forks `apertium/apertium-tur` to create `shardulc/apertium-tur` and makes some
commits to `shardulc/apertium-tur`. So far, Apertium knows nothing about Shardul or his
new code.
1. Shardul opens a pull request from `shardulc/apertium-tur` to `apertium/apertium-tur`,
essentially saying "please review my changes and add them to
`apertium/apertium-tur`". Depending on their notification settings, Sushain, Ilnar,
and Fran receive emails about this pull request.
1. Sushain takes a look at Shardul's changes. He thinks they are good, but he leaves a
few comments about what Shardul can improve. Shardul tries to fix the comments by making
more commits to `shardulc/apertium-tur`.
1. Sushain is satisfied with his changes and merges the pull request. Now
`apertium/apertium-tur` has the same code as `shardulc/apertium-tur`.

At the end of this sequence of events, Shardul still has the same permissions he had
at the beginning.

#### Step 2

Shardul has contributed a number of pull requests and wants to be able to commit
further code without necessarily having it reviewed by Sushain or Ilnar.

1. Shardul emails Ilnar or the `apertium-stuff` mailing list.
1. Ilnar thinks it's reasonable, and makes Shardul an outside collaborator for
`apertium/apertium-tur` with repository write access.
1. Shardul starts making commits directly to `apertium/apertium-tur`.

Now Shardul has gained repository write access to `apertium/apertium-tur`.

#### Step 3

Shardul is still not a organization member of `apertium`.

1. Shardul emails `apertium-stuff` about wanting to be an organization member.
1. Two existing organization members, including Sushain, reply to that email
seconding his request.
1. Fran notes that the two conditions required to become a member as per
Apertium's [by-laws][2] are satisfied: Shardul has contributed code in the past, and he
has two existing members seconding him. Fran makes Shardul an organization member of
`apertium`.

As an organization member, Shardul can:
 * know who the other members are (the ones not marked private)
 * view, create, talk to, and lead [teams][3]
 * use [project boards][4] to plan projects

**Note**: Shardul's write access to repositories has *not changed* and so far, he only has write
access to `apertium/apertium-tur`. For other repositories, he can either follow
steps 1 and 2 again, or Fran can directly give him write access.


### How `apertium/apertium-tur` is released

1. Sushain creates a [draft release][5] in `apertium/apertium-tur` and emails Fran or
`apertium-stuff` about the planned release.
1. Fran replies, saying that the release is approved.
1. Sushain publishes the draft release.

Now the release will show up publicly on the `apertium/apertium-tur` releases
page and Sushain will be able (through the API) to view download counts for the
release.


### How `apertium/apertium-tur` is managed

Here, management includes setting up continuous integration, webhooks that
trigger automatic actions on commits/pull requests/issues/..., deploy keys,
deleting the repository, shifting from staging to trunk, etc.

1. Shardul, Sushain, Ilnar, and other contributors discuss what they want to do via email
or the issue tracker.
1. Ilnar changes settings accordingly.

Note that this process does not involve Fran at all.


### How a Turkish-language team functions

<will add descriptions of how teams work, how they can plan projects, etc. if
there is interest in organizing `apertium` this way>


  [1]: https://github.com/sushain97/apertium-on-github#organization
  [2]: http://wiki.apertium.org/wiki/By-laws
  [3]: https://help.github.com/articles/about-teams/
  [4]: https://help.github.com/articles/about-project-boards/
  [5]: https://help.github.com/articles/about-releases/
