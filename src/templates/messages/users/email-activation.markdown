Subject: {{ _("Email Address Activation") }}

{{ _("You, or somebody using your email address, has added this email address to an account on the Pakfire Build Service.") }}

{{ _("To activate your this email address, please click on the link below:") }}

  {{ baseurl }}/user/{{ user.name }}/activate?code={{ email.activation_code }}

Sincerely,  
-The Pakfire Build Service