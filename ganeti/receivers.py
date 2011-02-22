from object_permissions import signals as op_signals

from object_log.models import LogItem, LogAction
log_action = LogItem.objects.log_action

def op_user_add(sender, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_add_user, Logs action
    """
    log_action('ADD_USER', sender, obj,)


def op_user_remove(sender, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_remove_user, Logs action
    """
    log_action('REMOVE_USER', sender, obj)


def op_perm_edit(sender, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_edit_user, Logs action
    """
    log_action('MODIFY_PERMS', sender, obj)

LogAction.register('ADD_USER', 'object_log/permissions/add_user.html')
LogAction.register('REMOVE_USER', 'object_log/permissions/remove_user.html')
LogAction.register('MODIFY_PERMS', 'object_log/permissions/modify_perms.html')

op_signals.view_add_user.connect(op_user_add, dispatch_uid='op_user_add')
op_signals.view_remove_user.connect(op_user_remove, dispatch_uid='op_user_remove')
op_signals.view_edit_user.connect(op_perm_edit, dispatch_uid='op_perm_edit')
