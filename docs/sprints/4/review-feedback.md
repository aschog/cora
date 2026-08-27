# Sprint 4 — reviewer feedback

The reviewer's write-up of the sprint-4 project review, verbatim. It is the record, not
the backlog: turning each finding into a tracked checklist item is sprint 5's day-one
artefact (`docs/sprints/5/sprint-5-feedback.md`, per `docs/workflow.md`).

---

Georg made a good job on this project with his AI project that was presented during this
review. The idea of the use case is good and I would love to use this application because
of capability to have an universal AI agent who can consult&advice on specific domain. As
we have discussed during the project review, there are still less and more important
areeas for further improvement, such as:

README does not convey the main idea of the solution, just one or two sentences at the
beginning.

The designed database architecture is quite fragile and heavy. I mean that there are two
logical units of database (ChromaDB + SQL-based database) which duplicates the raw data
just for displaying highlighted chunks over the plain text. The purpose is clear, but
technical implementation is so heavy. I would change SQL-base database to individual set
of Markdown (.md) files which would corresponds every single raw data file and can be
called by the algorithm individually. We clearly discussed that during the project review.

Since the current version of the solution contain single domain only – that works
technically, but I have some concerns when add new domain to the solution. If we have two
databases for a signle domain, it is not clear how to setup database architecture for
multiple domains. This information should be explained at the main README.md file.

There is a single AI agent which receives and process user query. It would be more
efficient to breakdown logical processes into a sequence of actions within a agenting
workflow. That would be less fragile, more stable and easier to control from developer
perspective.

We have a productive and insighful discussion about that with Georg. I think that Georg
could build even stronger and more stable AI products with his knowledge and critical
thinking. For today, I recognize the presented project as a strong foundation for further
improvement and enrichments. So, congratulation with this achievement and good luck with
further challenges in the course!
