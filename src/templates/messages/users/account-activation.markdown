Subject: {{ _("Account Activation") }}

{{ _("You, or somebody using your email address, has registered an account on the Pakfire Build Service.") }}

{{ _("To activate your account, please click on the link below:") }}

  {{ baseurl }}/user/{{ user.name }}/activate?code={{ user.email.activation_code }}

Sincerely,  
-The Pakfire Build Service