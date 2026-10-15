# Docs digest — Assets, Categories, Projects

Sources:
- User docs, Assets: https://docs.mautic.org/en/7.2/components/assets.html (A)
- User docs, Categories: https://docs.mautic.org/en/7.2/categories/categories-overview.html (C)
- User docs, Projects: https://docs.mautic.org/en/7.2/projects/projects-overview.html (P)
- Developer docs, Assets API: https://devdocs.mautic.org/en/7.2/rest_api/assets.html
- Developer docs, Categories API: https://devdocs.mautic.org/en/7.2/rest_api/categories.html
- Form actions: https://docs.mautic.org/en/7.2/components/forms.html#form-actions

The 8.0 Categories and Projects pages are identical to 7.2. The 8.0 Assets page adds "Downloading multiple Assets". The devdocs Asset and Category API pages carry a "legacy page, potentially inaccurate" banner. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/assets.html]

## Terminology
- The docs capitalise product nouns: Asset, Category, Project, Contact, Form, Form action, Landing Page, Email, Campaign, Segment, Focus Item, Dynamic Web Content, Marketing Messages, Text messages, Stage, Points. [docs: https://docs.mautic.org/en/7.2/components/assets.html]
- "Local" vs "Remote" Assets; "Download an Asset" is the Form action; "Associate with other entities" is the Project permission. [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#permissions]

## Assets (user docs)
1. Categories must exist and be published before you assign them; Assets cannot be assigned to unpublished Categories. [docs: https://docs.mautic.org/en/7.2/components/assets.html#working-with-assets]
2. Set up storage integrations (for example the Amazon S3 Plugin) before creating Assets. [docs: https://docs.mautic.org/en/7.2/components/assets.html#working-with-assets]
3. Assets are Local (upload, drag-drop, auto-upload on selection) or Remote (a URL, or browse integrated cloud storage). [docs: https://docs.mautic.org/en/7.2/components/assets.html#creating-a-new-asset]
4. Server settings limit the upload size, and warnings may show in the upload area. [docs: https://docs.mautic.org/en/7.2/components/assets.html#creating-a-new-asset]
5. Default allowed types are csv, doc, docx, epub, gif, jpg, jpeg, mpg, mpeg, mp3, odt, odp, ods, pdf, png, ppt, pptx, tif, tiff, txt, xls, xlsx and wav. Extra types, the maximum size and the Assets directory are set in Configuration > Asset Settings. [docs: https://docs.mautic.org/en/7.2/components/assets.html#uploading-an-asset]
6. Documented fields: Title, Alias (code: no such field in 7.2.1), Description, Category, Language, Published, Publish at, Unpublish at, and "Block search engines from indexing this file" (`X-Robots-Tag`). [docs: https://docs.mautic.org/en/7.2/components/assets.html#uploading-an-asset]
7. UTM parameters on the download URL appear in the Asset download Report. [docs: https://docs.mautic.org/en/7.2/components/assets.html#add-utm-codes-to-asset]
8. Setting `validate_remote_domains => true` in local.php restricts remote URLs to Configuration > System Settings > Miscellaneous > Allowed remote domains, plus the Mautic domain. [docs: https://docs.mautic.org/en/7.2/components/assets.html#using-remote-assets]
9. The download URL tracks which Contacts download. Append `?stream=1` to open the file in a new tab; the result depends on the browser. [docs: https://docs.mautic.org/en/7.2/components/assets.html#viewing-an-asset]
10. To gate an Asset, use the Form action "Download an Asset". For verified emails, attach the Asset to an Email sent through a Form action. [docs: https://docs.mautic.org/en/7.2/components/assets.html#viewing-an-asset]
11. Deleting an Asset cannot be undone and removes its download statistics. Points the Contact already earned remain. The docs recommend unpublishing instead. [docs: https://docs.mautic.org/en/7.2/components/assets.html#deleting-an-asset]
12. Default streamed extensions are gif, jpg, jpeg, mpg, mpeg, mp3, pdf, png and wav. Override them with a `streamed_extensions` array in local.php. [docs: https://docs.mautic.org/en/7.2/components/assets.html#display-assets-directly-in-the-browser]
13. The "Download an Asset" form action downloads a specific Asset, or the most recently published Asset in a Category. [docs: https://docs.mautic.org/en/7.2/components/forms.html#form-actions]
14. 8.0 docs: select Assets, open the three-dot menu and choose **Download selected assets** to get `assets-batch-{date}-{time}.zip`.
    - Limits: at most 100 Assets and 500 MB, local Assets only, and view permission on each.
    - Duplicate names get a ` (1)` suffix.
    - Any violation aborts the whole download.

    The code has this on the 7.x branch after 7.2.1, not yet released [PR #15609]. [docs: https://docs.mautic.org/en/8.0/components/assets.html#downloading-multiple-assets]

## Assets REST API (devdocs)
15. Legacy endpoints:

    | Endpoint | Purpose |
    |---|---|
    | `GET /api/assets/ID` | get one Asset |
    | `GET /api/assets` | list (`search`, `start`, `limit`, `orderBy`, `orderByDir`, `publishedOnly`, `minimal`) |
    | `POST /api/assets/new` | create (`title`, `storageLocation`, `file`) |
    | `PATCH` or `PUT /api/assets/ID/edit` | edit; PUT creates when missing (201) |
    | `DELETE /api/assets/ID/delete` | delete |

    [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/assets.html]
16. Response fields include `downloadCount`, `uniqueDownloadCount`, `revision`, `category`, `extension`, `mime`, `size` (bytes) and `downloadUrl`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/assets.html]
17. To create a local Asset, first upload the file through the Files API with folder `assets`, then pass the returned name as `file` with `storageLocation=local`. For a remote Asset, `file` is the URL. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/assets.html#create-asset]
18. Deleting a local Asset through the API also deletes the file. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/assets.html#delete-asset]
19. Campaign export returns JSON, or a ZIP with the JSON plus the associated Assets. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/campaigns.html#export-campaign]
20. The Edit example passes `'type' => 'general'`, which is not an Asset field (probably a copy-paste error). [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/assets.html#edit-asset]

## Categories (user docs and devdocs)
21. Categories exist for Assets, Campaigns, Emails, Focus Items, Forms, Pages, Points, Social Monitoring and Stages. A Category is either element-specific or global. Code also registers Segments, Marketing Messages, Dynamic Content and SMS. [docs: https://docs.mautic.org/en/7.2/categories/categories-overview.html]
22. Categories are created from the Settings menu > Categories. Fields: type, title, description, alias, color and published. [docs: https://docs.mautic.org/en/7.2/categories/categories-overview.html#creating-and-managing-categories]
23. The docs say deleting a Category does not delete its items; they become uncategorized. Code instead refuses the delete while registered entities use the Category. [docs: https://docs.mautic.org/en/7.2/categories/categories-overview.html#deleting-categories]
24. Contacts get Categories through the Preference Center (Contact details > Preference). Contact Categories work in Segment and Dynamic Content filters. [docs: https://docs.mautic.org/en/7.2/categories/categories-overview.html#using-categories-for-contacts]
25. Category API endpoints: `GET /api/categories/ID`, `GET /api/categories`, `POST /api/categories/new` (`title`, `bundle`), `PATCH` or `PUT /api/categories/ID/edit`, and `DELETE /api/categories/ID/delete`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/categories.html]
26. To assign a Category on any entity through the API, send `category: <ID>`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/categories.html#assign-a-category]
27. The devdocs call the list "List Contact Categories" and say it "isn't filterable". The example shows bundle `point`, and code supports `?bundle=`. [devdocs: https://devdocs.mautic.org/en/7.2/rest_api/categories.html#list-contact-categories]
28. The docs do not describe Category permissions, global scoping in pickers, alias rules, or what an unpublished Category does to its entities. Use behaviour.md for those. [docs: https://docs.mautic.org/en/7.2/categories/categories-overview.html]

## Projects (user docs)
29. Projects group entities of many types for one initiative. Documented types: Assets, Campaigns, Companies, Dynamic Web Content, Emails, Focus Items, Forms, Landing Pages, Marketing Messages, Points, Segments, Stages and Text messages. Code adds Point Triggers. [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html]
30. Projects appear in the left main menu with a count of assigned entities. [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#managing-projects]
31. The name must be unique: "A project with this name already exists." The description is optional. [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#creating-projects]
32. Delete a single Project from the three-dot menu, or several with checkboxes and the "Delete selected" banner. Assigned entities are not deleted. [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#deleting-projects]
33. Assign from an entity's Projects field. Several Projects are allowed, and with create permission you can type a name and "Hit enter to create". [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#assigning-entities-to-a-project]
34. Assign from the Project: the button reads **Add new to project <Type>** when only one type is editable, and **Add Entities to Project** otherwise. Remove an entity with three-dot > **Remove from project**. [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#assigning-entities-to-a-project] [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#deleting-entities-from-projects]
35. Project permissions are View, Edit, Create, Delete, Full and **Associate with other entities**. Associate is required to use the Projects field or to add and remove entities. [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#permissions]
36. The docs do not state the version that introduced Projects, their API, or which lists filter by Project. [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html]

## Procedures
- **Create an Asset:**
  1. Publish the Categories first.
  2. Go to Components > Assets > New.
  3. Choose Local upload or Remote.
  4. Fill in the fields and save.

  [docs: https://docs.mautic.org/en/7.2/components/assets.html#creating-a-new-asset]
- **Gate an Asset behind a Form:** add the Form action "Download an Asset" and choose an Asset or a Category. [docs: https://docs.mautic.org/en/7.2/components/forms.html#form-actions]
- **Create or delete a Category:** go to Settings > Categories, choose New, or delete with confirmation. [docs: https://docs.mautic.org/en/7.2/categories/categories-overview.html]
- **Create a Project and assign entities:** go to Projects > New, then use an entity's Projects field or the Project's Add button. [docs: https://docs.mautic.org/en/7.2/projects/projects-overview.html#managing-projects]
