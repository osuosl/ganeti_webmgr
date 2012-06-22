from django.dispatch import Signal

#
# Signals issued when a group is edited
#
view_group_created = Signal(providing_args=["editor"])
view_group_edited = Signal(providing_args=["editor"])
view_group_deleted = Signal(providing_args=["editor"])
