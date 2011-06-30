from muddle.shots.registration import register, TemplateMixer

register('main_menu', TemplateMixer('ganeti/muddle/main_menu_ganeti.html'))
register('main_menu', TemplateMixer('ganeti/muddle/main_menu_search.html'))
register('admin_menu', TemplateMixer('ganeti/muddle/admin_menu.html'))

register('user-detail-tab', TemplateMixer('ganeti/muddle/user_usage.html'))
register('gruop-detail-tab', TemplateMixer('ganeti/muddle/group_usage.html'))

