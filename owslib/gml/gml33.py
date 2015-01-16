"""
GML 3.3 is an extension of 3.2, with the addition of several new concepts.

Implemented with reference to document 10-129r1 from 
http://www.opengeospatial.org/standards/gml.

"""
#from __future__ import print_function
import lxml
import warnings

import gml32

namespaces = {'gml33': 'http://www.opengis.net/gml/3.3',
              'gml33rgrid': 'http://www.opengis.net/gml/3.3/rgrid'}


gml32.GMLdomainSet.TAGS.append('gml33:domainSet')

# XXX TODO: How do we register the fact that there is a "gml33:pos" which is used within GMLPoint
gml32.GMLPoint.TAGS.append('gml33:Point')

gml32.GMLGrid.TAGS.append('gml33:Grid')

gml32.GMLRectifiedGrid.TAGS.append('gml33:RectifiedGrid')

gml32.GMLRectifiedGrid.TAGS.append('gml33:RectifiedGrid')



class AbstractReferenceableGrid(gml32.GMLGrid):
    # See 10.3 AbstractReferenceableGrid
    pass


class GMLReferenceableGridByArray(AbstractReferenceableGrid):
    # See 10.4 ReferenceableGridByArray
    TAGS = ['gml33:ReferencableGridByArray',
            'gml33rgrid:ReferencableGridByArray']
    def __init__(self, attrs, limits, axes, dims, pos_list, sequence_rule):
        super(GMLReferenceableGridByArray, self).__init__(attrs, limits, axes, dims)
        self.pos_list = pos_list
        self.sequence_rule = sequence_rule

    def np_arrays(self):
        import numpy as np
        assert self.sequence_rule[1] == 'Linear'
        axes_dims = [int(dim[1:]) - 1 for dim in self.sequence_rule[0].split(' ')]
        values = np.array(self.pos_list)
        axes_arrays = {ax: values[ax_i::len(self.axes)] for ax_i, ax in enumerate(self.axes)}

        shape = self.limits.highs
        if np.prod(shape) != len(axes_arrays.values()[0]):
            # There are some badly implemented GridEnvelopes out there...
            n_unique = {ax: len(np.unique(arr)) for ax, arr in axes_arrays.items()}

            shape = [n_unique[ax] for ax in self.axes]
            if np.prod(shape) != len(axes_arrays.values()[0]):
                raise ValueError("Unable to determine the shapes of the grid arrays. "
                                 "The GridEnvelope should describe the number of points, but doesn't in this case.")

        for ax_name, axes_dim in zip(axes_arrays, axes_dims):
            # XXX Completely undocumented, but it looks to be column-major order...
            axes_arrays[ax_name] = axes_arrays[ax_name].reshape(shape, order='f')

            # Let's tidy up and remove the repeated dimension (leaving that dimension length one).
            full = [slice(0, 1)] * len(shape)
            full[axes_dim] = slice(None)
            axes_arrays[ax_name] = axes_arrays[ax_name][full]

        return axes_arrays

    @classmethod
    def init_kwargs_from_xml(cls, element):
        kwargs = super(GMLReferenceableGridByArray, cls).init_kwargs_from_xml(element)

        pos_list = gml32.GMLPosList.from_xml(gml32.GMLPosList.find_one(element))

        sequence_rule = gml32.GMLSequenceRule.find_one(element)
        sequence_rule = sequence_rule.get('axisOrder'), sequence_rule.text

        kwargs.update({'pos_list': pos_list, 'sequence_rule': sequence_rule})
        return kwargs


gml32.GMLEnvelope.TAGS.append('gml33:Envelope')

gml32.GMLGridEnvelope.TAGS.append('gml33:GridEnvelope')
