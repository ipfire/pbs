Subject: [{{ job.name }}] {{ _("Build job finished") }}

{{ _("The build job %s has finished") % job.name }}.

{{ _("If you are the maintainer, it is up to you to push it to one or more repositories.") }}

{{ _("Click on this link to get all details about the build:") }}
  {{ baseurl }}/job/{{ job.uuid }}

{{ _("Sincerely,") }}  
-{{ _("The Pakfire Build Service") }}