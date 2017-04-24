# Changelog

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
