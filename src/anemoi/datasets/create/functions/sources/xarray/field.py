# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.core.fieldlist import Field
from earthkit.data.core.fieldlist import math

from .coordinates import extract_single_value
from .coordinates import is_scalar
from .metadata import XArrayMetadata

LOG = logging.getLogger(__name__)


class EmptyFieldList:
    def __len__(self):
        return 0

    def __getitem__(self, i):
        raise IndexError(i)

    def __repr__(self) -> str:
        return "EmptyFieldList()"


class XArrayField(Field):

    def __init__(self, owner, selection):
        """Create a new XArrayField object.

        Parameters
        ----------
        owner : Variable
            The variable that owns this field.
        selection : XArrayDataArray
            A 2D sub-selection of the variable's underlying array.
            This is actually a nD object, but the first dimensions are always 1.
            The other two dimensions are latitude and longitude.
        """
        super().__init__(owner.array_backend)

        self.owner = owner
        self.selection = selection

        # Copy the metadata from the owner
        self._md = owner._metadata.copy()

        for coord_name, coord_value in self.selection.coords.items():
            if is_scalar(coord_value):
                # Extract the single value from the scalar dimension
                # and store it in the metadata
                coordinate = owner.by_name[coord_name]
                self._md[coord_name] = coordinate.normalise(extract_single_value(coord_value))

        values = self.selection.values
        # print(values.ndim, values.shape, selection.dims)
        # By now, the only dimensions should be latitude and longitude
        self._shape = tuple(list(values.shape)[-2:])
        if math.prod(self._shape) != math.prod(values.shape):
            print(values.ndim, values.shape)
            print(self.selection)
            raise ValueError("Invalid shape for selection")

    @property
    def shape(self):
        return self._shape

    def to_numpy(self, flatten=False, dtype=None):
        values = self.selection.values

        assert dtype is None
        if flatten:
            return values.flatten()
        return values.reshape(self.shape)

    def _make_metadata(self):
        return XArrayMetadata(self, self.owner.mapping)

    def grid_points(self):
        return self.owner.grid_points()

    @property
    def resolution(self):
        return None

    @property
    def grid_mapping(self):
        return self.owner.grid_mapping

    @property
    def latitudes(self):
        return self.owner.latitudes

    @property
    def longitudes(self):
        return self.owner.longitudes

    @property
    def forecast_reference_time(self):
        return self.owner.forecast_reference_time

    def __repr__(self):
        return repr(self._metadata)
