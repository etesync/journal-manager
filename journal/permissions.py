from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.owner == request.user


class IsJournalOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a journal to view it
    """

    def has_permission(self, request, view):
        journal_uid = view.kwargs['journal_uid']
        journal = view.get_journal_queryset().get(uid=journal_uid)
        return journal.owner == request.user
