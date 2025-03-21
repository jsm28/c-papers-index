# Prototype C document lists

This is a prototype of a system for numbering documents used in C
standardization, where different types of documents appear in
different numbered series and a document can have multiple numbered
versions (unlike the current system of a single namespace of
N-documents).

The document numbers should be considered far from final, and will
change as the logic for which documents to include in the list (and
what is/is not a version of the same document) is improved.  Revision
numbers are also currently far from final and at present always start
from 1 rather than taking account of any revision numbers that might
be in the document titles.

Currently all documents here are alternative numbers for N-documents;
this system does not yet support hosting documents directly.

## C-documents

These documents are technical (or occasionally purely editorial)
inputs to the standards process for the C standard and related
documents (typically proposals for changes, but also e.g. analysis of
some issue that doesn't propose a change, and presentations about
proposals, and documents about features in related languages and
software that might be relevant to C).  Ballot comments and
resolutions of those comments are included among C-documents.

Numbers for C-documents in this prototype start at C4000 but could
start at a different number if preferred.  The list is intended to
start with documents relevant or proposed for C2Y, but not anything
proposed for C23 and earlier versions unless still considered an
active proposal for C2Y or later (although the starting point could be
pushed further back if desired).

* [All revisions of C-documents, reverse-chronological](c-all.html)
* [C-documents in reverse order by document number](c-num.html)

## CPUB-documents

These documents are versions of the formal standards and related
documents that are outputs of the standards process.  (Typically the
final published version of any edition of such a document, and later
working drafts, are either unavailable here or are password-protected
because of JTC1 rules.)  Issue logs, where given document numbers, are
also CPUB-documents.  Each document revision has its own auxiliary
document series as needed for closely related documents such as a
diffmarked version or an editor's report.

The list is intended to be complete for such documents that were
previously assigned N-document numbers (although this involves some
guesswork for N-documents not available online).

## CADM-documents

These are administrative documents such as the Charter or documents
about processes rather than the contents of the C standard and related
technical documents.  This includes liaison documents with external
organizations, and minutes and agendas that are not for meetings of
the main C standards committee where they do not have a more specific
document series.

The list is intended to start with documents considered after C23 was
mostly complete (although the starting point could be pushed further
back if desired).

## Meeting documents

CMA-documents are agendas for meetings of the C standards committee,
CMM-documents are minutes and CM-documents are auxiliary documents for
a meeting such as venue information.  Document numbers are based on
the year and month of the meeting (the start of the meeting, for
meetings that crossed a month boundary).

The list is intended to be complete for such documents that were
previously assigned N-document numbers.

## CFP teleconference documents

CFPTCA-documents are agendas for meetings of the floating-point study
group, and CFPTCM-documents are corresponding minutes.  Document
numbers are based on the year and month of the meeting.

The list is intended to be complete for such documents that were
previously assigned N-document numbers.

## All documents

* All revisions of all documents, reverse-chronological (list not yet
  set up, but intended to include N-documents).  This list does not
  include early X3J11 documents from before WG14 was set up or before
  all significant C standards committee documents went through WG14,
  but such documents could be added if the relevant data is available.
