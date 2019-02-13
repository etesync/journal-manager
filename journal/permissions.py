from rest_framework import permissions
from journal.models import Journal, JournalMember


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
        try:
            journal = view.get_journal_queryset().get(uid=journal_uid)
            return journal.owner == request.user
        except Journal.DoesNotExist:
            # If the journal does not exist, we want to 404 later, not permission denied.
            return True


class IsMemberReadOnly(permissions.BasePermission):
    """
    Custom permission to make a journal read only if a read only member
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        journal_uid = view.kwargs['journal_uid']
        try:
            journal = view.get_journal_queryset().get(uid=journal_uid)
            member = journal.members.get(user=request.user)
            return not member.readOnly
        except Journal.DoesNotExist:
            # If the journal does not exist, we want to 404 later, not permission denied.
            return True
        except JournalMember.DoesNotExist:
            # Not being a member means we are the owner.
            return True
