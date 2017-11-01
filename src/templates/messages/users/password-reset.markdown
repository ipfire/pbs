Subject: {{ _("Password Reset") }}

{{ _("You, or somebody else has requested a password reset for the Pakfire Build Service.") }}

{{ _("To reset your password, please click on the link below:") }}

  {{ baseurl }}/password-reset?code={{ user.password_recovery_code }}

Sincerely,  
-The Pakfire Build Service
