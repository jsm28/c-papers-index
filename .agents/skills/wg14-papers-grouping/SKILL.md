---
name: wg14-papers-grouping
description: Check grouping of versions of a WG14 paper
---

The file $1 contains a list of documents of the standards committee
(WG14) for the C programming language that were proposals and other
inputs to the standards development process; the directory $2 has
copies of many of the documents themselves. The documents have
identifiers consisting of the letter 'N' followed by a number; in this
list, documents thought to be different revisions of the same paper
have been heuristically grouped, with each group being given an
identifier consisting of the letter 'S' followed by a number, and that
number being followed by 'r' and a revision number to distinguish the
successive versions of the paper. For example, nine revisions of the
"transparent aliases" proposal are given numbers S2729r1 through
S2729r9; each line in the list gives the 'S' number, the 'N' number,
and the date, author and title of the paper. The list is in reverse
order by 'N' number.

The intended grouping policy is fairly generous about what it counts
as versions of the same proposal, and all of the following are OK: (a)
a proposal taken over by someone other than its original author; (b) a
first version that just outlines an idea of a change and a later
version that fills out more details of the exact changes; (c) a later
version that removes some features from an earlier version because
they failed to gain committee support; or that only provides wording
and not the rationale present in earlier versions because the change
had gained consensus in principle and only the final wording needed to
be determined. However, slides presenting a proposal are not
considered as a version of the actual proposal document, and a
followup in the same subject area after a proposal was accepted is not
considered as a version of the original accepted proposal. A proposal
for a fix to a reported defect is not generally considered as a
version of a previous document proposing that defect be recorded as a
numbered Defect Report / DR (later, Clarification Request / CR). Where
a proposal is split into multiple separate proposals dealing with
different issues from the original proposal, those are generally
considered to start new groups rather than as new versions of the
original proposal.

Because the grouping is heuristic, it is likely there are errors in
it: cases where versions of the same paper have not been grouped
because of differences in how the title is listed, and cases where
multiple documents were linked by title when actually they were
different proposals on similar subjects, not versions of the same
proposal at all.

Please review the documents listed in $1 with 'S' numbers from $3
through $4 inclusive and identify any cases where it is likely there
is a mistake in grouping: either another document (possibly with a
number outside that range) should have been included in the group
sharing an 'S' number, but was not, or two or more documents were
grouped that in fact seem not to be versions of the same
proposal. Refer to the local copies of documents in $2 as needed to
check whether or not two documents are versions of the same proposal.
