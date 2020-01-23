# Changelog

## Version 1.2.0
* Make it possible to override the drf authenticators from the app's settings.

## Version 1.1.0
* Return the UID of the last entry when returning the journal list.

## Version 1.0.3
* dist: don't install the test directory.
* Members: 404 when interacting with non existing journals.

## Version 1.0.2
* Really fix race condition when adding entries to journal.

## Version 1.0.1
* Fix race condition when adding entries to journal.

## Version 1.0.0
* Release version 1.0 \o/
* Add support for read only journal membership
* Journal entries: 404 when a user has no access, don't 403 - as the user shouldn't know it even exists.
* Improve testing

## Version 0.5.6
* Add migrations for django 2.1.

## Version 0.5.5
* Fix crash when trying to list the forbidden endpoint for userInfo (api/v1/user)

## Version 0.5.4
* Allow journal owners to add themselves as members

## Version 0.5.3
* Fix bug with journals that are shared with multiple users.

## Version 0.5.2
* Fix server error when trying to access members of non-existent journals.

## Version 0.5.1
* Fix user info fetching to be case insensitive.
* Improve user info creation failure error message.

## Version 0.5.0
* Add Django 2 support

## Version 0.4.1
* Entries: fixing pagination when using the last query parameter.

## Version 0.4.0
* Entries: add suppport for pagination - limiting the number of entries returned by a query parameter.
* Members: add a proper error message when trying to add oneself as a journal member.

## Version 0.3.1
* Journal members: disallow adding oneself as a journal member.

## Version 0.3.0
* Journal: save the time when the journal was last modified.
* Added API to share journals between users
    * UserInfo: add API to publish your public keys and save an encrypted version of your private key.
    * Members: add API to control the members of a journal.
* Improve the Journal Entry API to be nested on top of the journals.
* Permissions: allow the setting API_PERMISSIONS to be either a tuple or a list.
* Improve tests

## Version 0.2.1
* Return a 409 when trying to push without setting the last query parameter when journal is not empty.
* Add a "reset" endpoint to be used by test servers to let external test suites easily clear accouns
* Improve tests

## Version 0.2.0
* Added a read-only (except on creation) version field to Journal

## Version 0.1.0
* Initial release.
