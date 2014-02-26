"""
Objects for dealing with Qiita metadata maps

This module provides the base object for dealing with Qiita metadata maps.
It standardizes the metadata map interface and all the different Qiita-db
backends should inherit from it in order to implement the job object.

The subclasses implementing this object should not provide any extra
public function in order to maintain back-end independence.

Classes
-------
- `QiitaMetadataMap` -- A Qiita Metadata map class
"""
__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"

from .base_object import QiitaStatusObject
from .exceptions import QiitaDBNotImplementedError


class QiitaMetadataMap(QiitaStatusObject):
    """
    Base analysis object to access to the Qiita metadata map information

    Standardizes the QiitaMetadataMap interface for all the back-ends.

    Parameters
    ----------
    id:
        The MetadataMap identifier

    Attributes
    ----------
    SampleIds
    CategoryNames
    Comments
    Metadata

    Methods
    -------
    getSampleMetadata(sample_id):
        Returns the metadata associated with a particular sample

    getCategoryValue(sample_id, category)
        Returns the category value associated with a sample's category

    getCategoryValues(sample_ids, category)
        Returns all the values of a given category.

    isNumericCategory(category)
        Returns True if the category is numeric and False otherwise

    hasUniqueCategoryValues(category)
        Returns True if the category's values are all unique

    hasSingleCategoryValue(category)
        Returns True if the category's values are all the same
    """

    @property
    def SampleIds(self):
        """Returns the IDs of all samples in the metadata map.

        The sample IDs are returned as a list of strings in alphabetical order.
        """
        raise QiitaDBNotImplementedError()

    @property
    def CategoryNames(self):
        """Returns the names of all categories in the metadata map.

        The category names are returned as a list of strings in alphabetical
        order.
        """
        raise QiitaDBNotImplementedError()

    @property
    def Comments(self):
        """List of strings for the comments in the mapping file.

        Can be an empty list
        """
        raise QiitaDBNotImplementedError()

    @Comments.setter
    def Comments(self, comments):
        """Sets the comments of the metadata map

        Parameters
        ----------
            comments : list of strings
                The new comments to be attached to the metadata map
        """
        raise QiitaDBNotImplementedError()

    @property
    def Metadata(self):
        """A python dict of dicts

        The top-level key is sample ID, and the inner dict maps category name
        to category value
        """
        raise QiitaDBNotImplementedError()

    @Metadata.setter
    def Metadata(self, metadata_map):
        """Sets the metadata dictionary

        Parameters
        ----------
            metadata_map : dict of dicts
                The top-level key is sample ID, and the inner dict maps
                category name to category value
        """
        raise QiitaDBNotImplementedError()

    def getSampleMetadata(self, sample_id):
        """Returns the metadata associated with a particular sample.

        The metadata will be returned as a dict mapping category name to
        category value.

        Parameters
        ----------
            sample_id : string
                the sample ID to retrieve metadata for
        """
        raise QiitaDBNotImplementedError()

    def getCategoryValue(self, sample_id, category):
        """Returns the category value associated with a sample's category.

        The returned category value will be a string.

        Parameters
        ----------
            sample_id : string
                the sample ID to retrieve category information for
            category : string
                the category name whose value will be returned
        """
        raise QiitaDBNotImplementedError()

    def getCategoryValues(self, sample_ids, category):
        """Returns all the values of a given category.

        The return categories will be a list.

        Parameters
        ----------
            sample_ids : list of strings
                An ordered list of sample IDs
            category : string
                the category name whose values will be returned
        """
        raise QiitaDBNotImplementedError()

    def isNumericCategory(self, category):
        """Returns True if the category is numeric and False otherwise.

        A category is numeric if all values within the category can be
        converted to a float.

        Parameters
        ----------
            category : string
                the category that will be checked
        """
        raise QiitaDBNotImplementedError()

    def hasUniqueCategoryValues(self, category):
        """Returns True if the category's values are all unique.

        Parameters
        ----------
            category : string
                the category that will be checked for uniqueness
        """
        raise QiitaDBNotImplementedError()

    def hasSingleCategoryValue(self, category):
        """Returns True if the category's values are all the same.

        For example, the category 'Treatment' only has values 'Control' for the
        entire column.

        Parameters
        ----------
            category : string
                the category that will be checked
        """
        raise QiitaDBNotImplementedError()
