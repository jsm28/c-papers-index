---
name: wg14-minutes-docs
description: Extract list of discussed papers from WG14 meeting minutes
---

The file $1 is the minutes of a meeting of the standards committee
(WG14) for the C programming language. Among other things, such
minutes give details of the discussion of various WG14 papers, with
identifiers consisting of the letter 'N' followed by a number (with or
without a space after the 'N', and sometimes with lowercase 'n', so "N
1234", "N1234" and "n1234" all represent the same paper).

Please extract a list of all the papers discussed at this meeting, and
output it in the form of a Python list, where the individual elements
are strings for the numeric part of the document identifier, in the
order in which those papers were discussed. For example, if the
meeting discussed N4567, N1234 and N2345 in that order, appropriate
output would be: ['4567', '1234', '2345']. Only those papers that were
the specific subject of an agenda item should be listed, not ones
referred to under the discussion of another item. Only those papers
that the discussion actually reached at the meeting should be listed;
not any that were not discussed there but may be listed in the minutes
under "If time" or similar.
