=======================
Contribution guidelines
=======================


Running tests
=============

Use ``tox``::

   pip install tox
   tox


Creating a release
==================

* Checkout the ``master`` branch.
* Pull the latest changes from ``origin``.
* Make sure ``check-manifest`` is happy.
* Increment the version number.
* Set the correct title for the release in ``HISTORY.rst``.
* Update the ``AUTHORS.rst`` file with new contributors::

     lancet contributors AUTHORS.rst

* Commit everything and make sure the working tree is clean.
* Push everything to github and make sure the tests pass on Travis::

     git push origin master

* Build and upload the release::

     python setup.py publish

* Tag the release::

     lancet tagver

* Push everything to github::

     git push --tags origin master

* Add the title for the next release to `HISTORY.rst`
