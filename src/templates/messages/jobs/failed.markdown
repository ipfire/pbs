Subject: [{{ job.name }}] {{ _("Build job failed") }}

{{ _("The build job %s has failed") % job.name }}.
{{ _("This could have a couple of reasons and needs to be investigated by you.") }}

{{ _("Here is more information about the incident:") }}

* {{ _("Name") }}: {{ job.name }}
{% if job.builder %}* {{ _("Builder") }}: {{ job.builder }}{% end %}

{{ _("Click on this link to get all details about the build:") }}
  {{ baseurl }}/job/{{ job.uuid }}

{{ _("Sincerely,") }}  
-{{ _("The Pakfire Build Service") }}