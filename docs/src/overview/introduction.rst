.. _introduction:

Introduction
=============
There is a collection of Level 1 requirements for the SKA Observatory, and the SKA-Mid and SKA-Low telescopes that, taken together, can be interpreted as implying the need for a “Shift Log Tool”. This interpretation has been reached in discussions with the SKA Science Operations team, and in the light of the experience of other major observatories, such as ALMA, that have similar tools.

The Shift Log Tool (SLT) is envisioned as both an “on-line” tool, used in real-time by the operators at the two telescope sites, and as an “off-line” tool, used at any of the three SKA sites. Its intention is to collate and then provide access to a record of the major events occurring during an operator’s shift.

1. At the telescope sites, the SLT will:
   - Collect and filter information on all events occurring during an operational shift.
   - Gather information from the EDA (Event Data Analytics), ODA (Operational Data Analytics), and logging databases.
   - Capture benign informational records, failures, warnings, and events such as unexpected RFI detection.
   - Operate continuously but organize information based on the concept of a "shift" (expected duration: 6-12 hours).
   - Provide a user interface for the telescope operator to view collated information in real-time and recent history.
   - Allow the telescope operator to enter narrative records linked to specific events.

2. At the observatory level (not in real-time during a shift), science operations staff at all three sites must be able to:
   - Use the SLT to view, interrogate, and annotate information collected during a shift.
   - Annotate the information, but not modify the original data from databases or operator entries.

3. The Shift Log information collected by the SLT must be persisted for the lifetime of the SKA Observatory.

.. note::
    The current version of the SLT (Shift Log Tool) service retrieves log data from the ODA system. 


Architecture Diagram

.. figure:: ../diagrams/slt_overview.png
   :align: center
