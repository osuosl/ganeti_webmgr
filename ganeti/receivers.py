from object_permissions import signals as op_signals


def op_user_add(sender, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_add_user, Logs action
    """
    log_action(sender, obj, "added user")


def op_user_remove(sender, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_remove_user, Logs action
    """
    log_action(sender, obj, "removed user")


def op_perm_edit(sender, user, obj, **kwargs):
    """
    receiver for object_permissions.signals.view_edit_user, Logs action
    """
    log_action(sender, obj, "modified permissions")


op_signals.view_add_user.connect(op_user_add, dispatch_uid='op_user_add')
op_signals.view_remove_user.connect(op_user_remove, dispatch_uid='op_user_remove')
op_signals.view_edit_user.connect(op_perm_edit, dispatch_uid='op_perm_edit')