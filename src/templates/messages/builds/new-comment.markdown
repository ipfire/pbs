Subject: {{ _("%(user)s commented on %(build)s") % { "user" : user.realname, "build" : build }}

{% for line in text.splitlines() %}  {{ line }}{% end %}
